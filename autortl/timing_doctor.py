"""Timing Doctor (Pothole 6): deterministic triage of timing failures with a
tool-knobs-first escalation ladder.

Escalation: tool knobs (free, zero-risk) -> RTL surgery -> replan.
Slack magnitude picks the rung: small deficits get knobs, big ones get surgery.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class TimingCategory(Enum):
    LOGIC_DEPTH = "logic_depth"     # too many logic levels between FFs -> pipeline
    HIGH_FANOUT = "high_fanout"     # one net drives too much -> replicate / max_fanout
    CDC = "cdc"                     # cross-clock path -> synchroniser / constraint
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
    wns = -999.0
    m = re.search(r"WNS\(ns\)\s+TNS\(ns\).*?\n\s*(-?[\d.]+)", text, re.DOTALL)
    if m:
        wns = float(m.group(1))
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

    if wns >= 0:
        return Diagnosis(TimingCategory.UNKNOWN, wns, "timing met", "none", "")

    # categorise
    if levels >= 8:
        cat = TimingCategory.LOGIC_DEPTH
        surgery = (f"The critical path has {levels} logic levels. Insert a pipeline "
                   f"register mid-path to cut combinational depth roughly in half; "
                   f"update the '// @latency' header accordingly.")
    elif fanout >= 64:
        cat = TimingCategory.HIGH_FANOUT
        surgery = (f"A net on the critical path has fanout {fanout}. Replicate the "
                   f"driving register (duplicate the FF and split the loads) to "
                   f"reduce fanout per copy.")
    elif re.search(r"clk\w*\s*->\s*clk\w*", snippet) and "clk ->" not in snippet:
        cat = TimingCategory.CDC
        surgery = ("The failing path crosses clock domains. Insert a two-flop "
                   "synchroniser for single-bit signals or an async FIFO for buses.")
    else:
        cat = TimingCategory.UNKNOWN
        surgery = ("Shorten the worst combinational path shown below by splitting "
                   "the computation across two cycles:\n" + snippet)

    # escalation ladder
    if wns > KNOB_THRESHOLD_NS and not already_tried_knobs:
        action = "tool_knobs"
    elif wns > SURGERY_THRESHOLD_NS or already_tried_knobs:
        action = "rtl_surgery"
    else:
        action = "rtl_surgery"   # even big deficits get one surgery before replan
    return Diagnosis(cat, wns, snippet, action, surgery)
