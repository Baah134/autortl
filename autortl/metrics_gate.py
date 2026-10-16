"""Metrics integrity gate (defence #10).

Parsed metrics must be sane before they may influence selection.
A metrics parse failure is an INFRA failure, never a score of zero.
"""
from __future__ import annotations
import math
from .report_parser import VivadoMetrics


class MetricsGateError(Exception):
    pass


def validate(m: VivadoMetrics, synthesis_ran: bool) -> None:
    """Raise MetricsGateError when metrics are internally inconsistent."""
    if not synthesis_ran:
        return  # sim-only results carry no resource claims
    problems = []
    if m.lut_total <= 0:
        problems.append(f"lut_total={m.lut_total} (must be > 0 after synthesis)")
    if m.ff_total <= 0:
        problems.append(f"ff_total={m.ff_total} (must be > 0 after synthesis)")
    if m.lut_used < 0 or m.lut_used > max(m.lut_total, 1):
        problems.append(f"lut_used={m.lut_used} outside [0, {m.lut_total}]")
    if m.ff_used < 0 or m.ff_used > max(m.ff_total, 1):
        problems.append(f"ff_used={m.ff_used} outside [0, {m.ff_total}]")
    for name in ("wns_ns", "whs_ns"):
        value = getattr(m, name)
        if not math.isfinite(value) or value == -999.0 or not (-1000.0 < value < 1000.0):
            problems.append(f"{name}={value} missing or implausible")
    if problems:
        raise MetricsGateError("metrics failed integrity gate: " + "; ".join(problems))
