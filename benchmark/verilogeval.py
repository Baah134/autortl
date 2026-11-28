"""VerilogEval spec-to-RTL adapter, pilot selection and Icarus grader.

Runbook: docs/BENCHMARK_PILOT.md; plan: docs/ROADMAP.md. This
module reads a pinned VerilogEval checkout, builds a benchmark.artifacts
manifest, deterministically selects pilot tasks and grades sealed candidates
with the official test and reference. It never runs generation, never feeds a
grade back to a run and never establishes OS/filesystem isolation.

Upstream strings (file suffixes, Icarus flags, the "Mismatches: N in M samples"
summary) follow the authors' spec-to-RTL release and must be confirmed against
the pinned commit's Makefile and analysis script before pilot grading.
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from autortl.fileio import file_sha256

SUFFIXES = {"prompt": "_prompt.txt", "test": "_test.sv", "ref": "_ref.sv"}
TOP = "TopModule"
TB_TOP = "tb"
CATEGORIES = ("combinational_logic", "combinational_arithmetic", "sequential", "fsm_control")
RANK_PREFIX = "autortl-public-v1"
# Pilot validates adaptation, so clocked categories (reset, latency and clock
# semantics) get two slots; the small arithmetic category keeps its tasks for
# final selection. Fixed before any trial (November14).
PILOT_SLOTS = {"combinational_logic": 1, "combinational_arithmetic": 1, "sequential": 2, "fsm_control": 2}
COMPILE_FLAGS = ("-Wall", "-Winfloop", "-Wno-timescale", "-g2012")
SIM_TIMEOUT_S = 30.0
COMPILE_TIMEOUT_S = 120.0
VERDICTS = ("pass", "fail", "compile_error", "runtime_error", "timeout", "no_result")

_TASK_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*\Z")
_COMMIT = re.compile(r"[0-9a-f]{40}\Z")
_SUMMARY = re.compile(r"^\s*Mismatches:\s*(\d+)\s+in\s+(\d+)\s+samples\s*$", re.MULTILINE)


class AdapterError(ValueError):
    """The dataset, catalog or request is malformed; nothing was graded."""


class GraderUnavailable(RuntimeError):
    """Infrastructure: the simulator could not be started. Never a design verdict."""


@dataclass(frozen=True)
class Task:
    id: str
    prompt: Path
    test: Path
    ref: Path


def sha256_file(path: Path) -> str:
    return file_sha256(Path(path))


def _check_id(task_id: str) -> str:
    if type(task_id) is not str or not _TASK_ID.match(task_id):
        raise AdapterError(f"invalid task id {task_id!r}")
    return task_id


def _check_commit(commit: str, label: str) -> str:
    if type(commit) is not str or not _COMMIT.match(commit):
        raise AdapterError(f"{label} must be a full 40-character lowercase commit")
    return commit


def list_tasks(root: Path) -> list[str]:
    """Task IDs with a prompt file directly in root, sorted."""
    root = Path(root)
    if not root.is_dir():
        raise AdapterError(f"dataset directory not found: {root}")
    suffix = SUFFIXES["prompt"]
    return sorted(p.name[: -len(suffix)] for p in root.iterdir()
                  if p.is_file() and p.name.endswith(suffix))


def load_task(root: Path, task_id: str) -> Task:
    """Resolve one task's three files; every file must be a regular file."""
    root = Path(root)
    _check_id(task_id)
    paths = {}
    for key, suffix in SUFFIXES.items():
        path = root / (task_id + suffix)
        if path.is_symlink() or not path.is_file():
            raise AdapterError(f"task {task_id}: missing {key} file {path.name}")
        paths[key] = path
    return Task(task_id, paths["prompt"], paths["test"], paths["ref"])


# --------------------------------------------------------------- selection
def rank(commit: str, name: str) -> str:
    return hashlib.sha256(f"{RANK_PREFIX}|{commit}|{name}".encode("utf-8")).hexdigest()


def select_pilot(catalog: dict, commit: str, slots: dict | None = None) -> dict:
    """Choose pilot tasks, one per family, with fixed slots per category.

    catalog maps task id -> {"category": one of CATEGORIES, "family": name}; it is
    the reviewed classification, made from statements only, before any trial.
    slots defaults to PILOT_SLOTS. Families are ranked by SHA-256 of
    RANK_PREFIX|commit|family; a category takes its best-ranked families, and
    each family contributes its best-ranked task. All pilot families are
    excluded from final selection.
    """
    _check_commit(commit, "dataset commit")
    slots = dict(PILOT_SLOTS if slots is None else slots)
    if set(slots) != set(CATEGORIES) or any(type(n) is not int or n < 1 for n in slots.values()):
        raise AdapterError("slots need a positive integer for every category")
    families: dict[str, list[str]] = {}
    family_category: dict[str, str] = {}
    for task_id, entry in sorted(catalog.items()):
        _check_id(task_id)
        if not isinstance(entry, dict) or set(entry) != {"category", "family"}:
            raise AdapterError(f"catalog entry {task_id} needs exactly category and family")
        category, family = entry["category"], entry["family"]
        if category not in CATEGORIES:
            raise AdapterError(f"catalog entry {task_id}: unknown category {category!r}")
        if type(family) is not str or not family:
            raise AdapterError(f"catalog entry {task_id}: empty family")
        if family_category.setdefault(family, category) != category:
            raise AdapterError(f"family {family} spans categories; classify it once")
        families.setdefault(family, []).append(task_id)
    queues = {c: sorted((f for f, cat in family_category.items() if cat == c),
                        key=lambda f: (rank(commit, f), f)) for c in CATEGORIES}
    short = [f"{c} ({len(queues[c])} < {slots[c]})" for c in CATEGORIES if len(queues[c]) < slots[c]]
    if short:
        raise AdapterError(f"too few families for categories: {', '.join(short)}")
    chosen = [(min(families[f], key=lambda t: (rank(commit, t), t)), c, f)
              for c in CATEGORIES for f in queues[c][:slots[c]]]
    return {"rule": f"{RANK_PREFIX}|<commit>|<family>, fixed slots per category",
            "slots": slots, "commit": commit,
            "pilot": [{"task": t, "category": c, "family": f} for t, c, f in chosen],
            "excluded_families": sorted(f for _, _, f in chosen)}


# ---------------------------------------------------------------- manifest
def build_manifest(root: Path, task_ids: list[str], *, dataset_commit: str, source_commit: str,
                   runtime_commit: str, runtime_sha256: str, requested_model: str,
                   budgets: dict, trials: int = 1) -> dict:
    """A benchmark.artifacts schema-1 manifest: prompt public, test/ref private.

    budgets maps each arm to run -> {"model_calls", "tool_seconds", "wall_seconds"};
    only the arms named there get cells. The ablation arm declares
    skip_generated_tb_mutations; every other arm declares full verification.
    The opt-in full_xcheck arm also declares spec_cross_check request_traces;
    no other cell carries that key, so other manifests are unchanged.
    """
    from . import artifacts

    _check_commit(dataset_commit, "dataset commit")
    if type(trials) is not int or trials < 1:
        raise AdapterError("trials must be a positive integer")
    if len(set(task_ids)) != len(task_ids) or not task_ids:
        raise AdapterError("task ids must be nonempty and unique")
    tasks = []
    for task_id in task_ids:
        task = load_task(root, task_id)
        tasks.append({
            "id": task_id,
            "public_files": [{"path": task.prompt.name, "sha256": sha256_file(task.prompt)}],
            "private_files": [{"path": p.name, "sha256": sha256_file(p)} for p in (task.test, task.ref)],
        })
    cells = [{"task": t, "trial": trial, "arm": arm, "budget": dict(budgets[arm]),
              "verification_policy": "skip_generated_tb_mutations" if arm == "ablation" else "full",
              **({"spec_cross_check": "request_traces"} if arm == "full_xcheck" else {})}
             for t in task_ids for trial in range(trials) for arm in sorted(budgets)]
    manifest = {"schema": artifacts.SCHEMA,
                "identity": {"dataset": {"commit": dataset_commit, "format": "verilogeval"},
                             "source_commit": source_commit,
                             "runtime": {"commit": runtime_commit, "sha256": runtime_sha256},
                             "requested_model": requested_model, "observed_model": None},
                "tasks": tasks, "cells": cells}
    artifacts._manifest(manifest)  # same strict validation load_manifest applies
    return manifest


# ------------------------------------------------------------------ grading
def parse_sim_output(text: str, exit_code: int | None, timed_out: bool = False) -> dict:
    """Classify one simulation from its real exit and the testbench summary.

    pass needs exit 0 and a final "Mismatches: 0 in M samples" with M > 0. A
    printed summary never overrides a nonzero exit or a timeout.
    """
    found = _SUMMARY.findall(text or "")
    mismatches, samples = (int(found[-1][0]), int(found[-1][1])) if found else (None, None)
    if timed_out:
        status = "timeout"
    elif exit_code != 0:
        status = "runtime_error"
    elif not found:
        status = "no_result"
    elif mismatches == 0 and samples > 0:
        status = "pass"
    else:
        status = "fail"
    return {"status": status, "mismatches": mismatches, "samples": samples,
            "summaries_seen": len(found)}


# Upstream sv-iv-analyze (pinned c498220d0a52248f8e3fdffe279075215bde2da6,
# analyze_result) codes: '.' pass, S syntax, e cast, 0 zero-width constant,
# n no sensitivities, w declared as wire, m unknown module, c/p unbound
# clk/wire, T timeout, C other compile error, r reset-style runtime, R runtime
# or mismatch. Only '.' passes.
UPSTREAM_PASS = "."
_UPSTREAM_MISMATCH = re.compile(r"^Mismatches: (\d+) in \d+ samples$")
# Checked in this order after "syntax error" and the plain "error" flag.
_UPSTREAM_BREAKS = (
    ("error: This assignment requires an explicit cast", "e"),
    ("error: Sized numeric constant must have a size greater than zero", "0"),
    ("warning: always_comb process has no sensitivities", "n"),
    ("found no sensitivities so it will never trigger", "n"),
    ("is declared here as wire", "w"),
    ("Unknown module type", "m"),
)


def upstream_passfail(log_text: str, verilog_text: str) -> str:
    """Line-for-line port of upstream analyze_result over the combined log.

    The upstream log holds compile output, then simulation output, then a
    "TIMEOUT" line when `timeout 30` expired; verilog_text is the candidate.
    """
    code, error_c, error_p, no_mismatch = "?", False, False, False
    for line in log_text.splitlines():
        if "syntax error" in line:
            code = "S"
            break
        if "error" in line:
            error_c = True
        hit = next((c for needle, c in _UPSTREAM_BREAKS if needle in line), None)
        if hit:
            code = hit
            break
        if "Unable to bind wire/reg" in line:
            error_p = True
        if "Unable to bind wire/reg/memory `clk'" in line:
            code = "c"
            break
        if "TIMEOUT" in line:
            code = "T"
            break
        match = _UPSTREAM_MISMATCH.match(line)
        if match and int(match.group(1)) == 0:
            no_mismatch = True
    if code == "?" and error_p:
        code = "p"
    if code == "?" and error_c:
        code = "C"
    if code == "?" and no_mismatch:
        code = UPSTREAM_PASS
    if code == "?":
        code = "R"
        for line in verilog_text.splitlines():
            if "posedge reset" in line or "negedge reset" in line or "posedge r)" in line:
                code = "r"
                break
    return code


def _run(runner, cmd, cwd, timeout):
    t0 = time.monotonic()
    try:
        done = runner(cmd, cwd=str(cwd), capture_output=True, text=True,
                      errors="replace", timeout=timeout)
        return done.returncode, (done.stdout or "") + (done.stderr or ""), False, time.monotonic() - t0
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or b""
        out = out.decode("utf-8", "replace") if isinstance(out, bytes) else out
        return None, out, True, time.monotonic() - t0
    except (FileNotFoundError, PermissionError) as exc:
        raise GraderUnavailable(f"cannot start {cmd[0]}: {exc}") from exc


def grade(candidates: list[Path], task: Task, workdir: Path, *, iverilog: str = "iverilog",
          vvp: str = "vvp", sim_timeout: float = SIM_TIMEOUT_S,
          compile_timeout: float = COMPILE_TIMEOUT_S, runner=subprocess.run) -> dict:
    """Compile candidate + official test + reference with top tb, then simulate.

    workdir must not exist yet; logs and the compiled image stay there. Raises
    GraderUnavailable when a tool cannot start (infrastructure, not a verdict).
    """
    candidates = [Path(c) for c in candidates]
    if not candidates or any(not c.is_file() for c in candidates):
        raise AdapterError("grade needs existing candidate files")
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=False)
    image = workdir / "sim.vvp"
    inputs = {"candidates": [{"path": str(c), "sha256": sha256_file(c)} for c in candidates],
              "test": {"path": str(task.test), "sha256": sha256_file(task.test)},
              "ref": {"path": str(task.ref), "sha256": sha256_file(task.ref)}}
    compile_cmd = [iverilog, *COMPILE_FLAGS, "-s", TB_TOP, "-o", str(image),
                   *map(str, candidates), str(task.test), str(task.ref)]
    code, out, timed_out, seconds = _run(runner, compile_cmd, workdir, compile_timeout)
    (workdir / "compile.log").write_text(out, encoding="utf-8")
    result = {"task": task.id, "inputs": inputs,
              "compile": {"cmd": compile_cmd, "exit": code, "timed_out": timed_out,
                          "seconds": round(seconds, 3), "log": "compile.log"},
              "simulate": None}
    verilog_text = "\n".join(c.read_text(encoding="utf-8", errors="replace") for c in candidates)
    compile_out = out
    if timed_out or code != 0 or not image.is_file():
        result.update(status="compile_error", mismatches=None, samples=None)
        return _with_upstream(result, compile_out, verilog_text)
    sim_cmd = [vvp, "-n", str(image)]
    code, out, timed_out, seconds = _run(runner, sim_cmd, workdir, sim_timeout)
    (workdir / "sim.log").write_text(out, encoding="utf-8")
    result["simulate"] = {"cmd": sim_cmd, "exit": code, "timed_out": timed_out,
                          "seconds": round(seconds, 3), "log": "sim.log"}
    result.update(parse_sim_output(out, code, timed_out))
    combined = compile_out + ("" if compile_out.endswith("\n") or not compile_out else "\n") + out
    return _with_upstream(result, combined + ("\nTIMEOUT\n" if timed_out else ""), verilog_text)


def _with_upstream(result: dict, combined_log: str, verilog_text: str) -> dict:
    """Add the upstream classification beside the strict exit-based status.

    upstream_pass is the official-compatible functional endpoint; status adds the
    real exit/timeout checks. Disagreement is recorded, never resolved silently.
    """
    code = upstream_passfail(combined_log, verilog_text)
    result.update(upstream_code=code, upstream_pass=code == UPSTREAM_PASS,
                  agree=(code == UPSTREAM_PASS) == (result["status"] == "pass"))
    return result


def candidate_files(receipt_dir: Path, receipt: dict) -> list[Path]:
    """Ordered RTL paths inside a loaded candidate receipt's directory."""
    if receipt.get("kind") != "candidate":
        raise AdapterError("only candidate receipts have RTL to grade")
    return [Path(receipt_dir) / record["path"] for record in receipt["files"]]


def tool_paths(iverilog: str | None = None, vvp: str | None = None) -> tuple[str, str]:
    """Explicit tool paths, else AUTORTL_IVERILOG / AUTORTL_VVP, else PATH names."""
    return (iverilog or os.environ.get("AUTORTL_IVERILOG") or "iverilog",
            vvp or os.environ.get("AUTORTL_VVP") or "vvp")
