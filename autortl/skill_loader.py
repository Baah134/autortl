"""Harness-side skill loader: the RAG pipeline collapsed into one function.

Claude Code loads .claude/skills natively; for headless single-turn calls and
non-Claude backends, the harness matches spec metadata against SKILL.md
frontmatter descriptions and injects selected bodies into the prompt.

Conventions vs skills: autortl-conventions rides in the SYSTEM prompt for
every call (law); skills are optional expertise injected per task.
"""
from __future__ import annotations
import re
from pathlib import Path
from .spec import ModuleSpec

SKILLS_DIR = Path(__file__).resolve().parent.parent / ".claude" / "skills"


def _frontmatter(text: str) -> dict:
    m = re.match(r"---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            out[k.strip()] = v.strip().strip('"')
    return out


def _body(text: str) -> str:
    return re.sub(r"^---\s*\n.*?\n---\s*\n", "", text, flags=re.DOTALL)


def load_skill(name: str) -> str:
    p = SKILLS_DIR / name / "SKILL.md"
    return _body(p.read_text()) if p.exists() else ""


def conventions() -> str:
    """The law. Always injected into the system prompt."""
    return load_skill("autortl-conventions")


def select_for_module(spec: ModuleSpec) -> list[str]:
    """Protocol-first, name-second matching (Pothole 5)."""
    chosen: list[str] = ["verilog-idioms"]     # always useful for generation
    if len(spec.clock_domains) > 1:
        chosen.append("cdc")
    behavior = spec.behavior.lower()
    if any(w in behavior for w in ("multiply", "mac", "filter", "fir", "dsp",
                                   "memory", "ram", "buffer")):
        chosen.append("xilinx-inference")
    return chosen


def select_for_timing() -> list[str]:
    return ["timing-closure", "vivado-messages"]


def inject(skill_names: list[str], limit_chars: int = 12000) -> str:
    parts = []
    used = 0
    for n in skill_names:
        body = load_skill(n)
        if body and used + len(body) <= limit_chars:
            parts.append(f"### Reference: {n}\n{body}")
            used += len(body)
    return "\n\n".join(parts)
