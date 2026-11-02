"""Failure triage: infra vs design vs target (defence #9).

An infra failure must NEVER mutate the design, enter history, or count
against fix attempts. It is retried with backoff, then surfaced.

A target failure (io_overutilization_sent_to_fixer) means the design's
contract-fixed interface does not fit the configured device, so no RTL repair
can help: it never reaches the fixer or the Timing Doctor, never mutates the
design, is never retried, and stops the run as target_infeasible. Unlike
infrastructure it is a deterministic outcome of the run configuration.
"""
from __future__ import annotations
import re
from enum import Enum


class FailureKind(Enum):
    INFRA = "infra"
    DESIGN = "design"
    UNKNOWN = "unknown"
    TARGET = "target"


# Outcomes that are final for their inputs: committed to the stage journal and
# never retried. INFRA and UNKNOWN stay uncommitted so a resume can retry them.
SETTLED_KINDS = (FailureKind.DESIGN, FailureKind.TARGET)


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
_INFORMATIONAL = re.compile(r"^\s*(?:INFO|WARNING)\s*:", re.IGNORECASE)

# I/O overutilization: more top-level I/O ports than package user I/O. Only an
# ERROR line at the start of a line counts (never quoted names or INFO text).
_TARGET_ERROR_LINE = re.compile(r"^\s*ERROR:\s*\[Place\s+30-415\]", re.IGNORECASE)
_TARGET_DETAIL = re.compile(
    r"\[Place\s+30-415\][^\n]*?(?P<ports>\d+)\s+I/O ports"
    r"(?:[\s\S]{0,200}?device:\s*(?P<device>[\w.-]+))?"
    r"(?:\s+package:\s*(?P<package>[\w.-]+))?"
    r"(?:[\s\S]{0,200}?only\s+(?P<available>\d+)\s+available user I/O)?",
    re.IGNORECASE)


def target_capacity(text: str) -> dict | None:
    """Port count and package capacity of a [Place 30-415] failure, else None.

    Vivado prints the message on two lines: the port count on the ERROR line
    and the device, package and available user I/O on the next one. A part the
    message does not state stays None; it is never guessed.
    """
    lines = (text or "").splitlines()
    for index, line in enumerate(lines):
        if not _TARGET_ERROR_LINE.match(line):
            continue
        excerpt = "\n".join(lines[index:index + 2])
        match = _TARGET_DETAIL.search(excerpt)
        number = lambda name: int(match.group(name)) if match and match.group(name) else None
        return {"message_id": "Place 30-415", "io_ports": number("ports"),
                "available_user_io": number("available"),
                "device": match.group("device") if match else None,
                "package": match.group("package") if match else None,
                "excerpt": excerpt.strip()[:600]}
    return None


def describe_target(capacity: dict) -> str:
    """One deterministic sentence for summaries and error text."""
    ports = capacity.get("io_ports")
    available = capacity.get("available_user_io")
    where = " ".join(part for part in (
        f"device {capacity['device']}" if capacity.get("device") else "",
        f"package {capacity['package']}" if capacity.get("package") else "") if part) or "the target"
    return (f"target_infeasible: the top has {ports if ports is not None else 'an unknown number of'} I/O ports "
            f"but {where} has {available if available is not None else 'fewer'} available user I/O "
            "([Place 30-415]); the contract fixes the ports, so this is not a design repair")


def classify(text: str) -> FailureKind:
    t = text or ""
    lines = t.splitlines()
    # Informational lines never decide infrastructure: every synthesis log says
    # "INFO: [Common 17-349] Got license for feature 'Synthesis'".
    decisive = "\n".join(l for l in lines if not _INFORMATIONAL.match(l))
    for sig in _INFRA_SIGNATURES:
        if re.search(sig, decisive, re.IGNORECASE):
            return FailureKind.INFRA
    # io_overutilization_sent_to_fixer: the [Place 30-68] not-placed and
    # [Place 30-99] placer-failed errors that follow are consequences, so the
    # whole log is a target-capacity failure, never a design bug.
    if any(_TARGET_ERROR_LINE.match(line) for line in lines):
        return FailureKind.TARGET
    # Real host failures across the entire log outrank downstream design errors.
    if any(_DESIGN_ERROR_LINE.match(line) for line in lines):
        return FailureKind.DESIGN
    content = "\n".join(l for l in lines if not re.match(r"^\s*INFO\s*:", l, re.IGNORECASE))
    for sig in _DESIGN_SIGNATURES:
        if re.search(sig, content, re.IGNORECASE):
            return FailureKind.DESIGN
    return FailureKind.UNKNOWN
