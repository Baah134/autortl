"""Which frozen companions a trusted testbench tests directly, and whether a
candidate still uses them.

A build's child modules become frozen companions: compiled unchanged beside
every candidate top. A candidate may inline a companion's logic instead of
instantiating it. When the trusted testbench instantiates that companion
directly, though, the companion is part of what the testbench verifies, and
an inlined candidate leaves those checks running against the stale companion
file instead of the candidate (taxonomy: stale_companion_masks_inlined_candidate).

Instantiation discovery is lexical: comments and strings are removed, module
headers are dropped, and a known module name followed by `#(` or by an
instance name and `(` counts as an instantiation. Only known module names are
searched, so keywords and other identifiers cannot match.
"""
from __future__ import annotations
import re
from pathlib import Path

from .verilog_interface import IDENT, strip_comments

_MODULE = re.compile(rf"\bmodule\s+({IDENT})\b(.*?)\bendmodule\b", re.S)


def _clean(text):
    return re.sub(r'"(?:\\.|[^"\\])*"', '""', strip_comments(text))


def module_bodies(text):
    """Map each module declared in text to its body (header name removed)."""
    return {match[1]: match[2] for match in _MODULE.finditer(_clean(text))}


def instantiated(text, names):
    """The subset of names instantiated somewhere in text (already cleaned or not)."""
    body = re.sub(rf"\bmodule\s+{IDENT}", "module", _clean(text))
    found = set()
    for name in names:
        if re.search(rf"(?<![\w$]){re.escape(name)}\s*(?:#\s*\(|{IDENT}\s*(?:\[[^\]]*\]\s*)?\()", body):
            found.add(name)
    return found


def companion_modules(extra_sources):
    """Map each module declared in the companion files to its body."""
    modules = {}
    for path in extra_sources:
        modules.update(module_bodies(Path(path).read_text(encoding="utf-8", errors="replace")))
    return modules


def required_by_testbench(tb, extra_sources):
    """Companions the trusted testbench instantiates directly, sorted."""
    if tb is None or not extra_sources:
        return []
    names = set(companion_modules(extra_sources))
    return sorted(instantiated(Path(tb).read_text(encoding="utf-8", errors="replace"), names))


def unreachable(candidate_verilog, top, extra_sources, required):
    """Required companions that the candidate top no longer reaches."""
    if not required:
        return []
    companions = companion_modules(extra_sources)
    own = module_bodies(candidate_verilog)
    bodies = {**companions, **own}             # a candidate may define helpers, never companions
    reached, frontier = set(), [top]
    while frontier:
        name = frontier.pop()
        if name in reached or name not in bodies:
            continue
        reached.add(name)
        frontier.extend(instantiated(bodies[name], set(bodies) - reached))
    return sorted(set(required) - reached)


def violation(candidate_verilog, top, extra_sources, tb):
    """A repair-ready error message, or "" when the candidate is acceptable."""
    required = required_by_testbench(tb, extra_sources)
    missing = unreachable(candidate_verilog, top, extra_sources, required)
    if not missing:
        return ""
    names = ", ".join(missing)
    return (f"ERROR: candidate top {top} no longer instantiates frozen companion(s) {names}, which the trusted "
            f"testbench {Path(tb).name} instantiates directly; those checks would test the stale companion, not "
            f"this candidate. Keep instantiating {names} from {top}.")
