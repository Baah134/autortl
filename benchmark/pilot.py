"""VerilogEval pilot runners: arm A (one backend invocation) and arm C (full build).

Pilot scope only (docs/BENCHMARK_PILOT.md). Each run gets a fresh output
directory and ends in a sealed benchmark.artifacts receipt (candidate or
missing) before any grading. The official test and reference are never passed
to generation. Arm B (mutation-qualification ablation) is not implemented.

    python -m benchmark.pilot select   --catalog C.json --commit SHA --out pilot.json
    python -m benchmark.pilot manifest --dataset D --commit SHA --tasks ID... --out M.json
    python -m benchmark.pilot run      --manifest M.json --dataset D --task ID --arm full --out DIR
    python -m benchmark.pilot grade    --manifest M.json --dataset D --run DIR --out GRADE_DIR
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

from . import artifacts
from . import verilogeval as ve
from autortl.fileio import file_sha256, read_json

REPO = Path(__file__).resolve().parent.parent
ARMS = ("single_call", "ablation", "full")
# Nov6 provisional pilot ceilings. single_call uses no tool time; artifacts
# needs a positive value, so it declares a nominal one second.
PROVISIONAL_BUDGETS = {
    "single_call": {"model_calls": 1, "tool_seconds": 1.0, "wall_seconds": 2100},
    "ablation": {"model_calls": 16, "tool_seconds": 1500.0, "wall_seconds": 2100},
    "full": {"model_calls": 16, "tool_seconds": 1500.0, "wall_seconds": 2100},
}
OUTER_GRACE_S = 300
# Arm C pilot settings (November14). VerilogEval grades function only and RTL
# optimization cannot change function under a fixed contract, so the build is
# verified and synthesized with the minimum one optimization iteration (run.py
# rejects zero: pilot_runner_double_hid_cli_rejection); out-of-context
# implementation avoids board pin-capacity stops unrelated to function.
FULL_SETTINGS = {"best_of_n": 1, "iterations": 1, "implementation": "out_of_context"}
SINGLE_CALL_SYSTEM = (
    "You are a Verilog RTL designer. Implement exactly the module the user describes, "
    f"named {ve.TOP}, with exactly the described ports, widths and behavior. Return one "
    "complete synthesizable Verilog-2001 or SystemVerilog module in a single ```verilog "
    "fenced block. Do not include a testbench or any other module.")
# Run summaries mapped to benchmark terminations; anything else is failed.
TERMINATION = {"done": "done", "budget_exhausted": "budget", "model_blocked": "model_blocked",
               "infra_blocked": "interrupted"}


def _sha(path: Path) -> str:
    return file_sha256(Path(path))


def _cell(manifest: dict, task: str, arm: str, trial: int) -> dict:
    if arm not in ARMS:
        raise ve.AdapterError(f"arm {arm!r} is not implemented for the pilot")
    found = [c for c in manifest["cells"] if (c["task"], c["arm"], c["trial"]) == (task, arm, trial)]
    if len(found) != 1:
        raise ve.AdapterError("cell not registered in manifest")
    return found[0]


def _selector(cell: dict) -> dict:
    return {"task": cell["task"], "trial": cell["trial"], "arm": cell["arm"]}


def _finish(out_dir: Path, cell: dict, receipt: dict, accounting: dict) -> dict:
    record = {"cell": _selector(cell), "receipt_id": receipt["id"], "kind": receipt["kind"],
              "termination": receipt["termination"], "accounting": accounting}
    (out_dir / "run.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def has_top_module(verilog: str) -> bool:
    return bool(re.search(rf"(?m)^\s*module\s+{ve.TOP}\b", verilog)) and "endmodule" in verilog


# ------------------------------------------------------------------ arm A
def run_single_call(manifest: dict, task: ve.Task, out_dir: Path, *, trial: int = 0,
                    model: str | None = None, ask=None) -> dict:
    """One backend invocation, no feedback; the extracted module is sealed unverified."""
    from autortl.budget import Budget
    from llm import client

    ask = ask or client.ask
    cell = _cell(manifest, task.id, "single_call", trial)
    if cell["budget"]["model_calls"] != 1:
        raise ve.AdapterError("single_call must declare exactly one model call")
    out_dir = Path(out_dir)
    work = out_dir / "work"
    work.mkdir(parents=True, exist_ok=False)
    budget = Budget(1, cell["budget"]["tool_seconds"] / 60.0, cell["budget"]["wall_seconds"] / 60.0)
    started = time.monotonic()
    termination, text, error = None, None, None
    try:
        text = ask("generator", task.prompt.read_text(encoding="utf-8"), system=SINGLE_CALL_SYSTEM,
                   budget=budget, model=model)
    except client.ModelCallError as exc:
        termination, error = "model_blocked", f"{exc.code}: {exc}"
    except RuntimeError as exc:
        if not str(exc).startswith("LLM_BUDGET:"):
            raise
        termination, error = "budget", str(exc)
    accounting = {"seconds": round(time.monotonic() - started, 3), "llm_calls": budget.llm_calls,
                  "tokens": dict(budget.tokens),
                  "calls_without_token_usage": budget.calls_without_token_usage, "error": error}
    if text is not None:
        (work / "raw_reply.txt").write_text(text, encoding="utf-8")
        verilog = client.extract_verilog(text)
        if has_top_module(verilog):
            (work / f"{ve.TOP}.sv").write_text(verilog.rstrip() + "\n", encoding="utf-8")
            receipt = artifacts.seal_candidate(
                manifest, _selector(cell), source_root=work,
                files=[{"path": f"{ve.TOP}.sv", "sha256": _sha(work / f"{ve.TOP}.sv"), "role": "rtl"}],
                destination=out_dir / "submission", top=ve.TOP, internal_status="unverified",
                selection_reason="latest_complete", termination="done")
            return _finish(out_dir, cell, receipt, accounting)
        termination, accounting["error"] = "failed", f"reply has no complete module {ve.TOP}"
    receipt = artifacts.record_missing(manifest, _selector(cell), destination=out_dir / "submission",
                                       termination=termination)
    return _finish(out_dir, cell, receipt, accounting)


# ------------------------------------------------------------------ arm C
def vivado_tools() -> dict:
    """Absolute Vivado tool paths, resolved like `run.py doctor` (name, .bat, .exe).

    A bare name cannot launch a Windows .bat; an unresolved tool is an
    infrastructure stop before any run (pilot_vivado_tools_unresolved).
    """
    from autortl.doctor import TOOLS, _resolve
    found = {name: _resolve(None, name) for name in TOOLS}
    missing = [name for name, path in found.items() if not path]
    if missing:
        raise ve.GraderUnavailable("Vivado tools not found on PATH: " + ", ".join(missing))
    return found


def full_command(request: Path, run_dir: Path, budget: dict, *, python: str = sys.executable,
                 model: str | None = None, best_of_n: int | None = FULL_SETTINGS["best_of_n"],
                 iterations: int | None = FULL_SETTINGS["iterations"],
                 implementation: str | None = FULL_SETTINGS["implementation"],
                 tools: dict | None = None, verification_policy: str = "full") -> list[str]:
    """`run.py build` from the public prompt alone; never an official --tb.

    Arm B passes verification_policy skip_generated_tb_mutations, which skips only
    the generated testbench's mutation qualification (ablation_policy_seam_absent).
    """
    cmd = [python, str(REPO / "run.py"), "build", "--spec", str(request), "--top", ve.TOP,
           "--generate-golden", "--output-dir", str(run_dir),
           "--max-llm-calls", str(budget["model_calls"]),
           "--max-vivado-minutes", repr(budget["tool_seconds"] / 60.0),
           "--max-wall-minutes", repr(budget["wall_seconds"] / 60.0),
           "--max-infra-retries", "1"]
    if model:
        cmd += ["--model", model]
    if best_of_n is not None:
        cmd += ["--best-of-n", str(best_of_n)]
    if iterations is not None:
        cmd += ["--iterations", str(iterations)]
    if implementation is not None:
        cmd += ["--implementation", implementation]
    if verification_policy != "full":
        cmd += ["--verification-policy", verification_policy]
    for name, path in (tools or {}).items():
        cmd += [f"--{name}", path]
    return cmd


def run_full(manifest: dict, task: ve.Task, out_dir: Path, *, trial: int = 0, model: str | None = None,
             best_of_n: int | None = FULL_SETTINGS["best_of_n"],
             iterations: int | None = FULL_SETTINGS["iterations"],
             implementation: str | None = FULL_SETTINGS["implementation"],
             runner=subprocess.run, python: str = sys.executable, tools: dict | None = None,
             arm: str = "full") -> dict:
    """Full AutoRTL build; only a DONE run's verified winner is sealed (accepted incumbent).

    A run without a DONE winner is recorded missing. Selecting the latest complete
    candidate from non-DONE runs needs candidate bundles (deferred).
    """
    if arm not in ("full", "ablation"):
        raise ve.AdapterError(f"run_full runs the full or ablation arm, not {arm!r}")
    cell = _cell(manifest, task.id, arm, trial)
    expected = "skip_generated_tb_mutations" if arm == "ablation" else "full"
    if cell["verification_policy"] != expected:
        raise ve.AdapterError(f"{arm} cell must declare verification_policy {expected}")
    tools = vivado_tools() if tools is None else tools  # fail before creating the cell directory
    out_dir = Path(out_dir)
    work = out_dir / "work"
    work.mkdir(parents=True, exist_ok=False)
    request = work / task.prompt.name
    request.write_bytes(task.prompt.read_bytes())
    if _sha(request) != next(f["sha256"] for t in manifest["tasks"] if t["id"] == task.id
                             for f in t["public_files"]):
        raise ve.AdapterError("public prompt differs from the frozen manifest")
    run_dir = out_dir / "run"
    cmd = full_command(request, run_dir, cell["budget"], python=python, model=model,
                       best_of_n=best_of_n, iterations=iterations, implementation=implementation,
                       tools=tools, verification_policy=cell["verification_policy"])
    started = time.monotonic()
    outer_timeout = cell["budget"]["wall_seconds"] + OUTER_GRACE_S
    try:
        done = runner(cmd, cwd=str(REPO), capture_output=True, text=True, errors="replace",
                      timeout=outer_timeout)
        exit_code, output, timed_out = done.returncode, (done.stdout or "") + (done.stderr or ""), False
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or b""
        exit_code, timed_out = None, True
        output = out.decode("utf-8", "replace") if isinstance(out, bytes) else out
    (out_dir / "build_output.log").write_text(output, encoding="utf-8")
    summary_path = run_dir / "run_summary.json"
    summary = read_json(summary_path) if summary_path.is_file() else {}
    budget_path = run_dir / "budget.json"
    used = read_json(budget_path) if budget_path.is_file() else {}
    accounting = {"seconds": round(time.monotonic() - started, 3), "exit": exit_code,
                  "outer_timeout": timed_out, "run_status": summary.get("status"),
                  "llm_calls": used.get("llm_calls"), "tool_seconds": used.get("vivado_seconds"),
                  "tokens": used.get("tokens"), "command": cmd}
    status = summary.get("status")
    winner = run_dir / f"{summary.get('top_module') or ve.TOP}_best.v"
    # A DONE summary is written last, after its winner, so it stands even when the
    # outer wall-clock safety net fired (it counts sleep; the run's own budget does not).
    files = submission_files(run_dir, summary, winner) if status == "done" and winner.is_file() else None
    if files:
        receipt = artifacts.seal_candidate(
            manifest, _selector(cell), source_root=run_dir,
            files=[{"path": f, "sha256": _sha(run_dir / f), "role": "rtl"} for f in files],
            destination=out_dir / "submission", top=summary.get("top_module") or ve.TOP,
            internal_status="accepted", selection_reason="accepted_incumbent", termination="done")
    else:
        # A model block is named before the generic infrastructure check, so a quota
        # stop is not mislabelled interrupted (both are excluded from report rates).
        if not timed_out and status == "model_blocked":
            termination = "model_blocked"
        elif timed_out or not summary or summary.get("failure_kind") == "infra":
            termination = "interrupted"
        else:
            termination = TERMINATION.get(status, "failed")
        if termination == "done":  # DONE without its complete sources is not a submission
            termination = "failed"
        receipt = artifacts.record_missing(manifest, _selector(cell), destination=out_dir / "submission",
                                           termination=termination)
    return _finish(out_dir, cell, receipt, accounting)


def submission_files(run_dir: Path, summary: dict, winner: Path) -> list[str] | None:
    """Complete ordered RTL for a DONE build, relative to run_dir.

    whole_design: the winner holds every module. frozen_children: the optimizer
    edited only the mechanical top, so the verified children from the resolved
    spec come first, then the winning top (pilot_submission_missing_children).
    None when a declared child source is absent, or TopModule is never defined.
    """
    files = [winner.name]
    if summary.get("edit_scope") == "frozen_children":
        spec = read_json((run_dir / "design_spec.json"))
        children = [f"modules/{m['name']}/{m['name']}.v" for m in spec["modules"]]
        if any(not (run_dir / c).is_file() for c in children):
            return None
        files = children + files
    text = "\n".join((run_dir / f).read_text(encoding="utf-8", errors="replace") for f in files)
    return files if has_top_module(text) else None


# ---------------------------------------------------------------- grading
def grade_run(manifest: dict, task: ve.Task, run_dir: Path, grade_dir: Path, **tools) -> dict:
    """Grade one sealed run against the official test; a missing record is ungraded."""
    record = read_json((Path(run_dir) / "run.json"))
    submission = Path(run_dir) / "submission"
    receipt = artifacts.load_artifact(submission, expected_id=record["receipt_id"])
    if receipt["identity"] != manifest["identity"] or receipt["cell"]["task"] != task.id:
        raise ve.AdapterError("receipt belongs to a different manifest or task")
    if receipt["kind"] == "missing":
        verdict = {"task": task.id, "status": "missing", "termination": receipt["termination"]}
    else:
        verdict = ve.grade(ve.candidate_files(submission, receipt), task, Path(grade_dir), **tools)
    verdict.update(cell=_selector(receipt["cell"]), receipt_id=receipt["id"],
                   internal_status=receipt.get("internal_status"))
    Path(grade_dir).mkdir(parents=True, exist_ok=True)
    (Path(grade_dir) / "verdict.json").write_text(json.dumps(verdict, indent=2), encoding="utf-8")
    return verdict


# -------------------------------------------------------------------- CLI
def _git_head() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(REPO), capture_output=True,
                          text=True, check=True).stdout.strip()


def _load(args):
    root = Path(args.dataset)
    manifest = artifacts.load_manifest(Path(args.manifest), public_root=root, private_root=root)
    return manifest, root


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="python -m benchmark.pilot")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("select")
    s.add_argument("--catalog", required=True, type=Path)
    s.add_argument("--commit", required=True)
    s.add_argument("--out", required=True, type=Path)
    m = sub.add_parser("manifest")
    m.add_argument("--dataset", required=True, type=Path)
    m.add_argument("--commit", required=True)
    m.add_argument("--tasks", required=True, nargs="+")
    m.add_argument("--model", default="unobserved-cli-default")
    m.add_argument("--runtime-sha256", required=True,
                   help="SHA-256 naming the frozen runtime identity registered for the pilot")
    m.add_argument("--out", required=True, type=Path)
    r = sub.add_parser("run")
    g = sub.add_parser("grade")
    for q in (r, g):
        q.add_argument("--manifest", required=True, type=Path)
        q.add_argument("--dataset", required=True, type=Path)
    r.add_argument("--task", required=True)
    r.add_argument("--arm", required=True, choices=ARMS)
    r.add_argument("--trial", type=int, default=0)
    r.add_argument("--model")
    r.add_argument("--best-of-n", type=int, default=FULL_SETTINGS["best_of_n"])
    r.add_argument("--iterations", type=int, default=FULL_SETTINGS["iterations"])
    r.add_argument("--implementation", default=FULL_SETTINGS["implementation"])
    r.add_argument("--out", required=True, type=Path)
    g.add_argument("--run", required=True, type=Path)
    g.add_argument("--out", required=True, type=Path)
    g.add_argument("--iverilog")
    g.add_argument("--vvp")
    a = p.parse_args(argv)

    if a.cmd == "select":
        catalog = read_json(a.catalog)
        result = ve.select_pilot(catalog, a.commit)
        a.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    elif a.cmd == "manifest":
        head = _git_head()
        manifest = ve.build_manifest(a.dataset, a.tasks, dataset_commit=a.commit, source_commit=head,
                                     runtime_commit=head, runtime_sha256=a.runtime_sha256,
                                     requested_model=a.model, budgets=PROVISIONAL_BUDGETS)
        with a.out.open("x", encoding="utf-8") as stream:
            json.dump(manifest, stream, indent=2)
        result = {"manifest": str(a.out), "cells": len(manifest["cells"])}
    elif a.cmd == "run":
        manifest, root = _load(a)
        task = ve.load_task(root, a.task)
        if a.arm == "single_call":
            result = run_single_call(manifest, task, a.out, trial=a.trial, model=a.model)
        else:
            result = run_full(manifest, task, a.out, trial=a.trial, model=a.model, arm=a.arm,
                              best_of_n=a.best_of_n, iterations=a.iterations,
                              implementation=a.implementation)
    else:
        manifest, root = _load(a)
        record = read_json((a.run / "run.json"))
        iverilog, vvp = ve.tool_paths(a.iverilog, a.vvp)
        result = grade_run(manifest, ve.load_task(root, record["cell"]["task"]), a.run, a.out,
                           iverilog=iverilog, vvp=vvp)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
