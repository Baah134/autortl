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
from .report_parser import VivadoMetrics, parse_timing_text


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


PATH_EXCERPT_CHARS = 6000


def first_violated_path(text: str, *, category: str | None = None) -> dict | None:
    """Select one real negative-slack path without mixing report-wide metadata.

    Category comes from that path's explicit Path Type. Missing path identity
    remains unknown; report-wide WNS/WHS never supplies an invented path type.
    """
    metrics = VivadoMetrics()
    parse_timing_text(text, metrics)
    if any(not math.isfinite(n) or n == -999.0 for n in (metrics.wns_ns, metrics.whs_ns)) or metrics.timing_met:
        return None
    markers = list(re.finditer(r"^\s*Slack\s*\((VIOLATED|MET)\)\s*:\s*(-?\d+(?:\.\d+)?)\s*ns[^\r\n]*", text, re.MULTILINE))
    for index, marker in enumerate(markers):
        slack = float(marker[2])
        if marker[1] != "VIOLATED" or slack >= 0:
            continue
        end = markers[index+1].start() if index+1<len(markers) else len(text)
        block = text[marker.start():end]
        # Stop before the next section even when it has no printed path.
        section = re.search(r"^\s*(?:Max|Min) Delay Paths\s*$", block, re.MULTILINE)
        if section:
            block = block[:section.start()]
        path_type = re.search(r"^\s*Path Type:\s*([^\r\n]+)", block, re.MULTILINE)
        kind = None
        if path_type:
            label = path_type[1].strip().lower()
            if re.match(r"(?:hold\b|min\b)",label): kind="hold"
            elif re.match(r"(?:setup\b|max\b)",label): kind="setup"
        if kind is None or (category is not None and kind!=category):
            continue
        summary_slack = metrics.whs_ns if kind=="hold" else metrics.wns_ns
        if summary_slack>=0 or slack<summary_slack-0.001:
            continue
        source = re.search(r"^\s*Source:\s*([^\r\n]+)",block,re.MULTILINE)
        destination = re.search(r"^\s*Destination:\s*([^\r\n]+)",block,re.MULTILINE)
        if source is None or destination is None:
            continue
        levels = re.search(r"^\s*Logic Levels:\s*(\d+)",block,re.MULTILINE)
        fanouts = [int(n) for n in re.findall(r"(?:fanout\s*=|\bfo\s*=)\s*(\d+)",block)]
        block=block.rstrip("\r\n")
        return {"category":kind,"slack_ns":slack,
                "source":source[1].strip() if source else None,
                "destination":destination[1].strip() if destination else None,
                "logic_levels":int(levels[1]) if levels else None,
                "fanout":max(fanouts) if fanouts else None,
                "text":block[:PATH_EXCERPT_CHARS],"truncated":len(block)>PATH_EXCERPT_CHARS,
                "preview_policy":"First complete identifiable violated path in report order, at most 6000 characters. "
                                 "Slack, endpoints, levels and fanout describe this path only, not global WNS/WHS. "
                                 "Resource text is retained verbatim; absent fields are unknown."}
    return None


def _report_path(text):
    metrics=VivadoMetrics()
    parse_timing_text(text,metrics)
    category="hold" if metrics.whs_ns<0 and metrics.whs_ns!=-999.0 else "setup"
    path=first_violated_path(text,category=category)
    return metrics,path


def parse_worst_path(timing_rpt: Path) -> tuple[float, int, int, str]:
    """Return global setup WNS plus metadata from one selected violated path.

    Hold takes priority when violated. WNS is a report-wide setup metric and is
    never labeled as the selected hold path's slack.
    """
    if not timing_rpt.exists():
        return -999.0,0,0,""
    metrics,path=_report_path(timing_rpt.read_bytes().decode("utf-8",errors="replace"))
    return (metrics.wns_ns,path["logic_levels"] or 0,path["fanout"] or 0,path["text"]) if path else (metrics.wns_ns,0,0,"")


def diagnose(work_dir: Path, already_tried_knobs: bool) -> Diagnosis:
    rpt = work_dir / "timing_routed.rpt"
    if not rpt.exists():
        rpt = work_dir / "timing.rpt"
    text = rpt.read_bytes().decode("utf-8",errors="replace") if rpt.is_file() else ""
    metrics,path = _report_path(text)
    wns,whs = metrics.wns_ns,metrics.whs_ns
    levels = path["logic_levels"] or 0 if path else 0
    fanout = path["fanout"] or 0 if path else 0
    snippet = path["text"] if path else ""

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
