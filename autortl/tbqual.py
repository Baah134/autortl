"""Testbench qualification by bug injection (defence #7 — the untested oracle).

A generated testbench must FAIL a sabotaged copy of a known-good module
before it is allowed to grade anything. Mutation operators are simple; qualification requires an observed assertion failure.
"""
from __future__ import annotations
import re
from pathlib import Path
from .config import RunConfig
from .vivado import xsim_run
from .triage import FailureKind

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
    """Returns (qualified, reason). Qualified means the tb catches an injected bug."""
    m = mutate(good_verilog)
    if m is None:
        return False, "no applicable mutation operator; qualification not established"
    mutated, desc = m
    qdir = work_dir / "tbqual"
    qdir.mkdir(parents=True, exist_ok=True)
    control_dir = qdir / "control"
    control_dir.mkdir(exist_ok=True)
    control = control_dir / f"{module_name}.v"
    control.write_text(good_verilog)
    passed, err, _ = xsim_run([control], tb_path, f"{module_name}_tb", cfg, control_dir)
    if not passed:
        return False, f"qualification control did not pass: {err}"
    mv = qdir / f"{module_name}.v"
    mv.write_text(mutated)
    passed, err, kind = xsim_run([mv], tb_path, f"{module_name}_tb", cfg, qdir)
    if passed:
        return False, (f"testbench PASSED a sabotaged design ({desc}) — "
                       f"the oracle cannot detect bugs and must be regenerated")
    if kind != FailureKind.DESIGN or not (
        err.startswith("Testbench failures:") or err == "testbench reported failure"
    ):
        return False, f"sabotage did not produce a testbench verdict: {err}"
    proven, reason = assertion_failure_proof(qdir)
    return (True, f"testbench correctly failed sabotage ({desc})") if proven else (False, reason)
