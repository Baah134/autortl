"""Metrics integrity gate (defence #10).

Parsed metrics must be sane before they may influence selection.
A metrics parse failure is an INFRA failure, never a score of zero.
"""
from __future__ import annotations
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
    if not (-1000.0 < m.wns_ns < 1000.0):
        problems.append(f"wns_ns={m.wns_ns} implausible")
    if problems:
        raise MetricsGateError("metrics failed integrity gate: " + "; ".join(problems))
