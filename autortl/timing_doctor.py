"""Timing Doctor (Pothole 6): deterministic triage of timing failures with a
tool-knobs-first escalation ladder.

Setup escalation: tool knobs -> behavior-preserving RTL surgery -> replan.
Hold violations require physical fixes or review of the real constraints.
"""
from __future__ import annotations
import re
import math
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from .report_parser import VivadoMetrics, parse_timing


class TimingCategory(Enum):
    LOGIC_DEPTH = "logic_depth"     # rebalance existing stages without new latency
    HIGH_FANOUT = "high_fanout"     # one net drives too much -> replicate / max_fanout
    CDC = "cdc"                     # cross-clock path -> synchroniser / constraint
    HOLD = "hold"                   # physical minimum-delay violation
    UNKNOWN = "unknown"


@dataclass
class Diagnosis:
    category: TimingCategory
    wns_ns: float
    detail: str
    action: str          # "tool_knobs" | "rtl_surgery" | "replan"
    instruction: str     # surgical instruction for the generator (if rtl_surgery)


KNOB_THRESHOLD_NS = -0.5    # deficits smaller than this: try knobs first
SURGERY_THRESHOLD_NS = -3.0 # deficits worse than this: knobs won't save you


def parse_worst_path(timing_rpt: Path) -> tuple[float, int, int, str]:
    """Returns (wns, logic_levels, fanout_est, raw_path_snippet)."""
    if not timing_rpt.exists():
        return -999.0, 0, 0, ""
    text = timing_rpt.read_text(errors="replace")
    metrics = VivadoMetrics()
    parse_timing(timing_rpt, metrics)
    wns = metrics.wns_ns
    levels = 0
    m = re.search(r"Logic Levels:\s*(\d+)", text)
    if m:
        levels = int(m.group(1))
    fanout = 0
    fanouts = [int(x) for x in re.findall(r"fanout=(\d+)", text)]
    if fanouts:
        fanout = max(fanouts)
    snippet = ""
    m = re.search(r"(Slack \(VIOLATED\).*?)(?:\n\s*\n|\Z)", text, re.DOTALL)
    if m:
        snippet = "\n".join(m.group(1).splitlines()[:15])
    return wns, levels, fanout, snippet


def diagnose(work_dir: Path, already_tried_knobs: bool) -> Diagnosis:
    rpt = work_dir / "timing_routed.rpt"
    if not rpt.exists():
        rpt = work_dir / "timing.rpt"
    wns, levels, fanout, snippet = parse_worst_path(rpt)
    metrics = VivadoMetrics()
    parse_timing(rpt, metrics)
    whs = metrics.whs_ns

    if any(not math.isfinite(value) or value == -999.0 for value in (wns, whs)):
        return Diagnosis(TimingCategory.UNKNOWN, wns,
                         "setup/hold report is missing or invalid", "replan",
                         "Restore complete timing reports and verify the real clock and I/O constraints. "
                         "Do not change RTL, clock requirements, or observable latency to hide missing evidence.")

    if whs < 0:
        action = "replan" if already_tried_knobs else "tool_knobs"
        return Diagnosis(TimingCategory.HOLD, wns, f"hold slack {whs} ns\n{snippet}", action,
                         "Use physical placement/routing hold-fix options first. If hold still fails, "
                         "replan after checking the real clock and I/O constraints against the design contract. "
                         "Do not relax the clock, change latency or throughput, or add RTL delay chains.")

    if metrics.timing_met:
        return Diagnosis(TimingCategory.UNKNOWN, wns, "timing met", "none", "")

    # categorise
    if levels >= 8:
        cat = TimingCategory.LOGIC_DEPTH
        surgery = (f"The critical path has {levels} logic levels. Rebalance existing pipeline "
                   "stages, retime existing registers where behavior is preserved, or factor logic "
                   "within the current cycle budget. Keep the @latency declaration unchanged.")
    elif fanout >= 64:
        cat = TimingCategory.HIGH_FANOUT
        surgery = (f"A net on the critical path has fanout {fanout}. Replicate the "
                   f"driving register (duplicate the FF and split the loads) to "
                   f"reduce fanout per copy.")
    elif re.search(r"clk\w*\s*->\s*clk\w*", snippet) and "clk ->" not in snippet:
        cat = TimingCategory.CDC
        return Diagnosis(cat, wns, snippet, "replan",
                         "Check the actual clock-domain relationship and specified CDC protocol. "
                         "Do not insert synchronizers, change latency, or waive real timing paths "
                         "without an independently approved contract change.")
    else:
        cat = TimingCategory.UNKNOWN
        surgery = ("Shorten the worst combinational path by factoring or restructuring logic "
                   "within its existing cycle budget:\n" + snippet)

    surgery += (" Preserve observable latency, throughput, interface, reset semantics, and parameter behavior. "
                "Do not add pipeline stages, extra cycles, new clocks, or RTL delay chains.")

    # escalation ladder
    if wns > KNOB_THRESHOLD_NS and not already_tried_knobs:
        action = "tool_knobs"
    elif wns > SURGERY_THRESHOLD_NS or already_tried_knobs:
        action = "rtl_surgery"
    else:
        action = "rtl_surgery"   # even big deficits get one surgery before replan
    return Diagnosis(cat, wns, snippet, action, surgery)
