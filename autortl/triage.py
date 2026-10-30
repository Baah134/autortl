"""Failure triage: infra vs design (defence #9).

An infra failure must NEVER mutate the design, enter history, or count
against fix attempts. It is retried with backoff, then surfaced.
"""
from __future__ import annotations
import re
from enum import Enum


class FailureKind(Enum):
    INFRA = "infra"
    DESIGN = "design"
    UNKNOWN = "unknown"


_INFRA_SIGNATURES = [
    r"\[Common 17-53\].*No open design",
    # A license failure, not Vivado's routine "Attempting to get a license" / "Got license".
    r"(?:could not|cannot|unable to|failed to)\s+(?:obtain|get|check\s*out|find)[^\n]*license"
    r"|\blicense\b[^\n]*(?:not (?:found|available|valid)|expired|denied|unavailable|checkout failed)",
    r"cannot (?:open|create|write).*\.(?:pb|wdb|jou|log)",  # file locks (xsim holds handles)
    r"Permission denied",
    r"used by another process",
    r"Connection (?:refused|reset|timed out)",
    r"No space left on device",
    r"vivado(?:\.bat)? .*not (?:found|recognized)",
    r"timed out after \d+(?:\.\d+)?s",
    r"HTTP (?:429|5\d\d)",
]

_DESIGN_SIGNATURES = [
    r"\[(?:Synth|XSIM|Timing|Opt|Place|Route|Common)\s+\d+-\d+\]",
    r"syntax error",
    r"port .* (?:mismatch|not found)",
    r"TEST FAILED",
    r"FAIL",
]


# Tool-ID errors that describe the design (triage_misreads_license_info_as_infra).
# Only ERROR lines: a host failure still outranks a promoted CRITICAL WARNING.
_DESIGN_ERROR_LINE = re.compile(
    r"^\s*ERROR:\s*\[(?:Synth|VRFC|XSIM|Opt|Place|Route|Timing|DRC)\s+\d+-\d+\]",
    re.IGNORECASE)
# Infrastructure problems that can still arrive on a tool-ID line.
_HOST_PROBLEM = re.compile(r"cannot (?:open|create|write).*\.(?:pb|wdb|jou|log)|used by another process"
                           r"|No space left on device", re.IGNORECASE)
_INFORMATIONAL = re.compile(r"^\s*(?:INFO|WARNING)\s*:", re.IGNORECASE)


def classify(text: str) -> FailureKind:
    t = text or ""
    lines = t.splitlines()
    # A design error reported by the tool decides, unless the host itself failed.
    if any(_DESIGN_ERROR_LINE.match(l) and not _HOST_PROBLEM.search(l) for l in lines):
        return FailureKind.DESIGN
    # Informational lines never decide infrastructure: every synthesis log says
    # "INFO: [Common 17-349] Got license for feature 'Synthesis'".
    decisive = "\n".join(l for l in lines if not _INFORMATIONAL.match(l))
    for sig in _INFRA_SIGNATURES:
        if re.search(sig, decisive, re.IGNORECASE):
            return FailureKind.INFRA
    content = "\n".join(l for l in lines if not re.match(r"^\s*INFO\s*:", l, re.IGNORECASE))
    for sig in _DESIGN_SIGNATURES:
        if re.search(sig, content, re.IGNORECASE):
            return FailureKind.DESIGN
    return FailureKind.UNKNOWN
