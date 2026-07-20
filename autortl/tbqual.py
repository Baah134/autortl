"""Testbench qualification by bug injection (defence #7 — the untested oracle).

A generated testbench must FAIL a sabotaged copy of a known-good module
before it is allowed to grade anything. Mutation operators are simple and
guaranteed-behavior-changing.
"""
from __future__ import annotations
import re
from pathlib import Path
from .config import RunConfig
from .vivado import xsim_run

_MUTATIONS = [
    (r"(?<![<>=!])<(?![<=])", ">", "flip < to >"),
    (r"(?<![=!<>])==(?!=)", "!=", "flip == to !="),
    (r"\+\s*1\b", "+ 2", "off-by-one increment"),
    (r"&&", "||", "flip && to ||"),
]


def mutate(verilog: str) -> tuple[str, str] | None:
    """Apply the first applicable mutation once. Returns (mutated, description)."""
    for pat, repl, desc in _MUTATIONS:
        if re.search(pat, verilog):
            return re.sub(pat, repl, verilog, count=1), desc
    return None


def qualify(good_verilog: str, tb_path: Path, module_name: str,
            cfg: RunConfig, work_dir: Path) -> tuple[bool, str]:
    """Returns (qualified, reason). Qualified means the tb catches an injected bug."""
    m = mutate(good_verilog)
    if m is None:
        return True, "no applicable mutation operator; qualification skipped"
    mutated, desc = m
    qdir = work_dir / "tbqual"
    qdir.mkdir(parents=True, exist_ok=True)
    mv = qdir / f"{module_name}.v"
    mv.write_text(mutated)
    passed, err, _ = xsim_run([mv], tb_path, f"{module_name}_tb", cfg, qdir)
    if passed:
        return False, (f"testbench PASSED a sabotaged design ({desc}) — "
                       f"the oracle cannot detect bugs and must be regenerated")
    return True, f"testbench correctly failed sabotage ({desc})"
