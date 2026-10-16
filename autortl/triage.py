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
    r"license",                       # license server hiccup
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


def classify(text: str) -> FailureKind:
    t = text or ""
    for sig in _INFRA_SIGNATURES:
        if re.search(sig, t, re.IGNORECASE):
            return FailureKind.INFRA
    for sig in _DESIGN_SIGNATURES:
        if re.search(sig, t, re.IGNORECASE):
            return FailureKind.DESIGN
    return FailureKind.UNKNOWN
