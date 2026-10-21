"""Testbench qualification by bug injection (defence #7 — the untested oracle).

A generated testbench must FAIL a sabotaged copy of a known-good module
before it is allowed to grade anything. Mutation operators are simple; qualification requires an observed assertion failure.
"""
from __future__ import annotations
import re
import hashlib
import json
from pathlib import Path
from .config import RunConfig
from .vivado import xsim_run
from .triage import FailureKind
from .verilog_interface import infer_module
from .linter import stub_verilog
from .state import atomic_write_text

_MUTATIONS = [
    (r"(?<![<>=!])<(?![<=])", ">", "flip < to >"),
    (r"(?<![=!<>])==(?!=)", "!=", "flip == to !="),
    (r"&&", "||", "flip && to ||"),
]


def mutate(verilog: str) -> tuple[str, str] | None:
    """Apply the first applicable mutation once. Returns (mutated, description)."""
    visible = re.sub(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"',
                     lambda match: " " * len(match[0]), verilog, flags=re.S)
    for pat, repl, desc in _MUTATIONS:
        match = re.search(pat, visible)
        if match:
            return verilog[:match.start()] + repl + verilog[match.end():], desc
    increment = re.search(r"\+\s*(?:(\d+)'([sS]?)([bBoOdDhH])([0-9a-fA-F_]+)|(1)\b)", visible)
    if increment:
        if increment[5]:
            replacement = "+ 2"
        else:
            width, signed, base, digits = increment.group(1, 2, 3, 4)
            radix = {"b": 2, "o": 8, "d": 10, "h": 16}[base.lower()]
            try:
                value = int(digits.replace("_", ""), radix)
            except ValueError:
                return None
            if value != 1:
                return None
            new_value = 0 if int(width) == 1 else 2
            encoded = format(new_value, {2: "b", 8: "o", 10: "d", 16: "x"}[radix])
            replacement = f"+ {width}'{signed}{base}{encoded}"
        return verilog[:increment.start()] + replacement + verilog[increment.end():], "change increment"
    return None


def qualification_mutations(source: str, name: str) -> list[tuple[str, str, str]]:
    """Bounded sensitivity probes; equivalent or irrelevant mutations may be missed."""
    variants = []
    primary = mutate(source)
    if primary is not None:
        variants.append(("mutant", primary[0], primary[1]))
    try:
        contract = infer_module(source, name)
        outputs = [port for port in contract.ports if port.direction == "output"]
        if outputs:
            stub = stub_verilog(contract)
            prefix = "`timescale 1ns/1ps\n"
            if contract.latency_known:
                prefix += f"// @latency {contract.latency}\n"
            for label, value, description in (("stuck_zero", "0", "stuck-zero outputs"),
                                               ("stuck_one", "-1", "stuck-one outputs")):
                assignments = "\n".join(f"assign {port.name} = {value};" for port in outputs)
                head, tail = stub.rsplit("endmodule", 1)
                replacement = prefix + head + assignments + "\nendmodule" + tail
                variants.append((label, replacement, description))
    except (ValueError, TypeError, KeyError):
        # Legacy snippets can still exercise the unchanged primary mutation API.
        pass
    seen = {source.encode("utf-8")}
    result = []
    for label, replacement, description in variants:
        data = replacement.encode("utf-8")
        if data not in seen:
            result.append((label, replacement, description))
            seen.add(data)
    return result[:3]


def assertion_failure_proof(work_dir: Path) -> tuple[bool, str]:
    """Require retained assertion evidence, not a wrapper's generic failure label."""
    path = Path(work_dir) / "sim_log.txt"
    if not path.is_file():
        return False, "raw simulation log is missing"
    raw = path.read_text(encoding="utf-8", errors="replace")
    if re.search(r"\b(?:watchdog|timeout|timed\s+out)\b", raw, re.I):
        return False, "watchdog/timeout is not an assertion detection"
    if re.search(r"(?m)^\s*TEST PASSED\b", raw):
        return False, "contradictory or successful verdict in mutant log"
    if not re.search(r"(?m)^\s*FAIL(?:\s|:)\s*\S", raw):
        return False, "raw assertion FAIL detail is missing"
    if not re.search(r"(?m)^\s*TEST FAILED(?:\s|:)\s*\S", raw):
        return False, "raw TEST FAILED verdict is missing"
    return True, "raw assertion detail and failure verdict retained"


def qualify(good_verilog: str, tb_path: Path, module_name: str,
            cfg: RunConfig, work_dir: Path) -> tuple[bool, str]:
    """Qualify against an ordered bounded portfolio; infrastructure never proves a fault."""
    variants = qualification_mutations(good_verilog, module_name)
    qdir = Path(work_dir) / "tbqual"
    qdir.mkdir(parents=True, exist_ok=True)
    def identity(path):
        path = Path(path)
        return {"path": str(path.resolve()), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()
                if path.is_file() else None}
    report = {"schema_version": 1, "module": module_name,
              "testbench": identity(tb_path), "reference_source_sha256": None,
              "control": None, "attempts": [], "qualified": False, "outcome": "pending"}
    def finish(qualified, outcome, reason):
        report.update(qualified=qualified, outcome=outcome, reason=reason[:2000])
        atomic_write_text(qdir / "qualification.json", json.dumps(report, indent=2))
        return qualified, reason
    if not variants:
        return finish(False, "unqualified", "no applicable mutation operator; qualification not established")
    control_dir = qdir / "control"
    control_dir.mkdir(exist_ok=True)
    control = control_dir / f"{module_name}.v"
    control.write_text(good_verilog, encoding="utf-8")
    report["reference_source_sha256"] = identity(control)["sha256"]
    passed, err, kind = xsim_run([control], tb_path, f"{module_name}_tb", cfg, control_dir)
    report["control"] = {"source": identity(control), "raw_log": identity(control_dir / "sim_log.txt"),
                         "passed": passed, "failure_kind": kind.value, "error": err[:2000]}
    if kind != FailureKind.DESIGN:
        return finish(False, "infra_blocked", "qualification control infrastructure blocked: " + err)
    if not passed:
        return finish(False, "control_failed", "qualification control did not pass: " + err)
    last_reason = "no behavioral mutant detection established"
    for label, mutated, description in variants:
        directory = qdir / label
        directory.mkdir(exist_ok=True)
        path = directory / f"{module_name}.v"
        path.write_text(mutated, encoding="utf-8")
        passed, err, kind = xsim_run([path], tb_path, f"{module_name}_tb", cfg, directory)
        record = {"label": label, "description": description, "source": identity(path),
                  "raw_log": identity(directory / "sim_log.txt"), "passed": passed,
                  "failure_kind": kind.value, "error": err[:2000], "assertion_detected": False}
        report["attempts"].append(record)
        if kind != FailureKind.DESIGN:
            record["outcome"] = "infra_blocked"
            return finish(False, "infra_blocked", "qualification mutant infrastructure blocked: " + err)
        explicit = not passed and (err.startswith("Testbench failures:") or err == "testbench reported failure")
        detected, proof_reason = assertion_failure_proof(directory) if explicit else (False, "no explicit assertion failure")
        record.update(assertion_detected=detected, outcome="detected" if detected else "missed",
                      proof_reason=proof_reason)
        if detected:
            return finish(True, "qualified", f"testbench detected {description}: {proof_reason}")
        last_reason = f"{label}: {proof_reason}" + ("; mutant passed" if passed else "; " + err[:500])
        # Preserve every missed probe before trying the next one; no TB changes.
        atomic_write_text(qdir / "qualification.json", json.dumps(report, indent=2))
    return finish(False, "unqualified", "qualification portfolio exhausted: " + last_reason)
