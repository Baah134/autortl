"""Paired area and timing report for the optimisation benchmark (ROADMAP B3).

    python -m benchmark.ppa_report render --attempt DIR --out REPORT.md

Reads the graded rows (`DIR/grades/summary.json`, from `benchmark.report grade`)
and the sealed PPA records (`DIR/ppa/*/ppa.json`, from `benchmark.ppa measure`).
Pure apart from reading those files; standard library only.

What is compared, and only where both arms are functionally correct:
- Arm A (single call, `single_call`) against arm C-opt (`full` cells run with
  the optimisation settings of the registration).
- The unit of independence is the task. A task is a functional pair when each
  arm has at least one trial that passes the official testbench; an area pair
  when each arm also has at least one such trial with routed metrics.
- Area: per task and arm, the geometric mean of (LUT + 1) over that arm's
  measured passing trials; the task's log ratio is C-opt minus A. The primary
  number is the geometric-mean LUT ratio C-opt / A, exp(mean log ratio), with a
  95% task-clustered bootstrap interval (benchmark.report.cluster_bootstrap).
  The +1 keeps a wiring-only design finite and is negligible at 20+ LUTs.
- Timing closure: per task and arm, the share of passing trials whose routed
  design meets setup and hold (WNS >= 0 and WHS >= 0) at the registered period;
  a passing design that fails synthesis counts as not closed. Paired difference
  C-opt minus A over functional pairs, same bootstrap.
- FF ratio and WNS difference are descriptive.
- Records must cover every passing cell exactly, all with one flow identity
  (implementation, part, period, template hash, Vivado version); otherwise the
  report refuses. Cells stopped by infrastructure are excluded and counted.

The verdict rule (`decide`) is a DRAFT until the owner freezes the B3
registration (docs/DECISIONS.md); its thresholds are the constants below.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from autortl.fileio import read_json

from .report import BOOTSTRAP_SAMPLES, BOOTSTRAP_SEED, INFRA_TERMINATIONS, ReportError, cluster_bootstrap

ARM_A, ARM_C = "single_call", "full"
ARM_LABEL = {ARM_A: "A single call", ARM_C: "C-opt harness"}
LUT_OFFSET = 1
# DRAFT thresholds, awaiting the owner's approval of the B3 registration.
RULE = "DRAFT (docs/DECISIONS.md, B3 entry awaiting owner approval)"
EQUIVALENCE_RATIO = 1.10       # ratio interval inside [1/1.10, 1.10] -> no material difference
MIN_AREA_PAIRS = 10            # fewer paired tasks -> descriptive only
MAX_NOT_EVALUABLE = 0.10       # share of an arm's cells stopped by infrastructure
TIMING_MARGIN = 0.10           # secondary closure reading, as in benchmark.claim
VERDICTS = ("harness_smaller", "single_call_smaller", "no_material_difference", "inconclusive",
            "insufficient_pairs")


def _flow_key(record: dict) -> str:
    return json.dumps({"flow": record["flow"], "tool_version": record["tool_version"]}, sort_keys=True)


def _mean(values) -> float:
    values = list(values)
    return sum(values) / len(values)


def _log_ratio_summary(per_task: dict[str, float], samples: int) -> dict:
    low, high = cluster_bootstrap(per_task, samples)
    return {"tasks": len(per_task), "geometric_mean_ratio": math.exp(_mean(per_task.values())),
            "ci95_task_bootstrap": [math.exp(low), math.exp(high)],
            "tasks_smaller": sum(v < 0 for v in per_task.values()),
            "tasks_equal": sum(v == 0 for v in per_task.values()),
            "tasks_larger": sum(v > 0 for v in per_task.values()),
            "per_task_ratio": {t: math.exp(v) for t, v in sorted(per_task.items())}}


def summarize(rows: list[dict], records: list[dict], samples: int = BOOTSTRAP_SAMPLES) -> dict:
    """Paired LUT ratio, timing closure and descriptive FF/WNS for arms A and C-opt."""
    if not rows:
        raise ReportError("no graded rows")
    rows = [r for r in rows if r["arm"] in (ARM_A, ARM_C)]
    seen, cells = set(), {}
    for row in rows:
        key = (row["task"], row["arm"], row["trial"])
        if key in seen:
            raise ReportError(f"duplicate cell {key}")
        seen.add(key)
        cells[key] = row
    for arm in (ARM_A, ARM_C):
        if not any(r["arm"] == arm for r in rows):
            raise ReportError(f"arm {arm} has no graded cell")
    if {r["task"] for r in rows if r["arm"] == ARM_A} != {r["task"] for r in rows if r["arm"] == ARM_C}:
        raise ReportError("arms cover different tasks")

    by_cell = {}
    for record in records:
        key = (record["cell"]["task"], record["cell"]["arm"], record["cell"]["trial"])
        if key[1] not in (ARM_A, ARM_C):
            continue
        if key in by_cell:
            raise ReportError(f"two PPA records for {key}")
        if key not in cells:
            raise ReportError(f"PPA record for an unregistered cell {key}")
        if not cells[key]["upstream_pass"]:
            raise ReportError(f"PPA record for a functionally failing cell {key}")
        by_cell[key] = record
    evaluable = {k: r for k, r in cells.items() if r.get("termination") not in INFRA_TERMINATIONS}
    passing = {k for k, r in evaluable.items() if r["upstream_pass"]}
    unmeasured = sorted(passing - set(by_cell))
    if unmeasured:
        raise ReportError(f"{len(unmeasured)} passing cells have no sealed PPA record; first: {unmeasured[0]}")
    flows = {_flow_key(r) for r in by_cell.values()}
    if len(flows) > 1:
        raise ReportError("PPA records were not measured with one flow, part, period and Vivado version")

    tasks = sorted({k[0] for k in cells})
    out: dict = {"tasks": len(tasks), "arms": {}, "flow": json.loads(flows.pop()) if flows else None,
                 "bootstrap": {"samples": samples, "seed": BOOTSTRAP_SEED, "unit": "task"},
                 "lut_offset": LUT_OFFSET}
    for arm in (ARM_A, ARM_C):
        every = [k for k in cells if k[1] == arm]
        mine = [k for k in every if k in evaluable]
        good = [k for k in mine if k in passing]
        measured = [k for k in good if by_cell[k]["status"] == "measured"]
        closed = [k for k in measured if by_cell[k]["metrics"]["timing_met"]]
        out["arms"][arm] = {
            "cells": len(mine), "not_evaluable": len(every) - len(mine),
            "functional_passes": len(good), "measured": len(measured),
            "synth_failed_cells": sorted(f"{k[0]}#{k[2]}" for k in good if by_cell[k]["status"] == "synth_failed"),
            "timing_closed": len(closed),
            "closure_rate": len(closed) / len(good) if good else None,
            "median_lut": sorted(by_cell[k]["metrics"]["lut"] for k in measured)[len(measured) // 2]
            if measured else None}

    def trials(task, arm, measured_only):
        keys = [k for k in passing if k[0] == task and k[1] == arm]
        return [k for k in keys if by_cell[k]["status"] == "measured"] if measured_only else keys

    def log_mean(keys, metric):
        return _mean(math.log(by_cell[k]["metrics"][metric] + LUT_OFFSET) for k in keys)

    functional = [t for t in tasks if trials(t, ARM_A, False) and trials(t, ARM_C, False)]
    area = [t for t in functional if trials(t, ARM_A, True) and trials(t, ARM_C, True)]
    out["pairs"] = {"functional": len(functional), "area": len(area),
                    "tasks_without_functional_pair": [t for t in tasks if t not in functional],
                    "functional_pairs_without_metrics": [t for t in functional if t not in area]}
    if area:
        out["lut_ratio"] = _log_ratio_summary(
            {t: log_mean(trials(t, ARM_C, True), "lut") - log_mean(trials(t, ARM_A, True), "lut") for t in area},
            samples)
        out["ff_ratio"] = _log_ratio_summary(
            {t: log_mean(trials(t, ARM_C, True), "ff") - log_mean(trials(t, ARM_A, True), "ff") for t in area},
            samples)

        def wns(task, arm):
            return _mean(by_cell[k]["metrics"]["wns_ns"] for k in trials(task, arm, True))
        diff = {t: wns(t, ARM_C) - wns(t, ARM_A) for t in area}
        out["wns_difference_ns"] = {"tasks": len(diff), "mean": _mean(diff.values()),
                                    "ci95_task_bootstrap": list(cluster_bootstrap(diff, samples))}
    else:
        out["lut_ratio"] = out["ff_ratio"] = out["wns_difference_ns"] = None
    if functional:
        def closure(task, arm):
            keys = trials(task, arm, False)
            return _mean(1.0 if by_cell[k]["status"] == "measured" and by_cell[k]["metrics"]["timing_met"]
                         else 0.0 for k in keys)
        diff = {t: closure(t, ARM_C) - closure(t, ARM_A) for t in functional}
        out["closure_difference"] = {"tasks": len(diff), "mean_difference": _mean(diff.values()),
                                     "ci95_task_bootstrap": list(cluster_bootstrap(diff, samples)),
                                     "tasks_better": sum(v > 0 for v in diff.values()),
                                     "tasks_equal": sum(v == 0 for v in diff.values()),
                                     "tasks_worse": sum(v < 0 for v in diff.values())}
    else:
        out["closure_difference"] = None
    out["claim"] = decide(out)
    return out


def classify_ratio(ci, band: float = EQUIVALENCE_RATIO) -> str:
    low, high = ci
    if high < 1.0:
        return "harness_smaller"
    if low > 1.0:
        return "single_call_smaller"
    if 1.0 / band <= low and high <= band:
        return "no_material_difference"
    return "inconclusive"


def decide(summary: dict) -> dict:
    """The DRAFT B3 decision rule over a summarize() result."""
    flags, disclosures = [], []
    lut = summary.get("lut_ratio")
    pairs = summary["pairs"]["area"]
    if lut is None or pairs < MIN_AREA_PAIRS:
        verdict = "insufficient_pairs"
        disclosures.append(f"Only {pairs} tasks are functionally correct and measured in both arms "
                           f"(registered minimum {MIN_AREA_PAIRS}); the result is descriptive only.")
    else:
        verdict = classify_ratio(lut["ci95_task_bootstrap"])
    for arm, a in summary["arms"].items():
        registered = a["cells"] + a["not_evaluable"]
        share = a["not_evaluable"] / registered if registered else 0.0
        if share > MAX_NOT_EVALUABLE:
            flags.append(f"incomplete:{arm}")
            disclosures.append(f"{a['not_evaluable']} of {registered} cells of {arm} were stopped by "
                               "infrastructure; the result is descriptive only.")
        if a["synth_failed_cells"]:
            disclosures.append(f"{arm}: functionally correct but failed synthesis: "
                               f"{', '.join(a['synth_failed_cells'])}.")
    if any(f.startswith("incomplete:") for f in flags) and verdict not in ("inconclusive", "insufficient_pairs"):
        flags.append(f"downgraded_from:{verdict}")
        verdict = "inconclusive"
    if summary["pairs"]["tasks_without_functional_pair"]:
        disclosures.append(f"{len(summary['pairs']['tasks_without_functional_pair'])} of {summary['tasks']} "
                           "tasks have no trial correct in both arms and carry no PPA comparison.")
    timing = summary.get("closure_difference")
    timing_reading = None
    if timing:
        from .claim import classify
        reading = classify(tuple(timing["ci95_task_bootstrap"]), TIMING_MARGIN)
        timing_reading = {"harness_better": "harness_closes_more",
                          "single_call_better": "single_call_closes_more"}.get(reading, reading)
    return {"rule": RULE, "primary": "lut_ratio C-opt/A", "verdict": verdict, "flags": flags,
            "timing_reading": timing_reading, "disclosures": disclosures,
            "thresholds": {"equivalence_ratio": EQUIVALENCE_RATIO, "min_area_pairs": MIN_AREA_PAIRS,
                           "max_not_evaluable": MAX_NOT_EVALUABLE, "timing_margin": TIMING_MARGIN}}


# ---------------------------------------------------------------- rendering
def _ratio(r) -> str:
    return f"{r['geometric_mean_ratio']:.3f} (95% CI {r['ci95_task_bootstrap'][0]:.3f} to " \
           f"{r['ci95_task_bootstrap'][1]:.3f}; {r['tasks']} tasks, smaller/equal/larger " \
           f"{r['tasks_smaller']}/{r['tasks_equal']}/{r['tasks_larger']})"


def render_markdown(summary: dict, title: str = "Optimisation benchmark (B3)") -> str:
    flow = summary["flow"] or {}
    f = flow.get("flow", {})
    lines = [f"# {title}", "",
             f"{summary['tasks']} tasks. Every passing design synthesised and routed out of context on "
             f"{f.get('part', 'n/a')} at {f.get('period_ns', 'n/a')} ns ({flow.get('tool_version') or 'n/a'}). "
             f"Only tasks functionally correct in both arms are compared. Intervals are 95% task-clustered "
             f"bootstrap ({summary['bootstrap']['samples']} resamples, seed {summary['bootstrap']['seed']}).", "",
             f"**Verdict ({summary['claim']['rule']}):** `{summary['claim']['verdict']}`", "",
             "## Arms", "",
             "| Arm | Functional passes | Measured | Synthesis failed | Timing closed | Closure rate | Median LUT |",
             "|---|---|---|---|---|---|---|"]
    for arm, a in summary["arms"].items():
        rate = "n/a" if a["closure_rate"] is None else f"{100 * a['closure_rate']:.1f}%"
        lines.append(f"| {ARM_LABEL[arm]} | {a['functional_passes']}/{a['cells']} | {a['measured']} | "
                     f"{len(a['synth_failed_cells'])} | {a['timing_closed']} | {rate} | {a['median_lut']} |")
    p = summary["pairs"]
    lines += ["", "## Paired comparison (C-opt over A)", "",
              f"Functional pairs: {p['functional']}; area pairs: {p['area']}.", ""]
    if summary["lut_ratio"]:
        lines += [f"- LUT ratio (primary, geometric mean of (LUT+{summary['lut_offset']})): "
                  + _ratio(summary["lut_ratio"]),
                  "- FF ratio (descriptive): " + _ratio(summary["ff_ratio"]),
                  f"- WNS difference (descriptive): {summary['wns_difference_ns']['mean']:+.3f} ns (95% CI "
                  f"{summary['wns_difference_ns']['ci95_task_bootstrap'][0]:+.3f} to "
                  f"{summary['wns_difference_ns']['ci95_task_bootstrap'][1]:+.3f})"]
    if summary["closure_difference"]:
        c = summary["closure_difference"]
        lines.append(f"- Timing closure difference: {100 * c['mean_difference']:+.1f} pp (95% CI "
                     f"{100 * c['ci95_task_bootstrap'][0]:+.1f} to {100 * c['ci95_task_bootstrap'][1]:+.1f}; "
                     f"better/equal/worse {c['tasks_better']}/{c['tasks_equal']}/{c['tasks_worse']})")
    if summary["lut_ratio"]:
        lines += ["", "| Task | LUT ratio C-opt/A |", "|---|---|"]
        lines += [f"| {t} | {r:.3f} |" for t, r in summary["lut_ratio"]["per_task_ratio"].items()]
    if summary["claim"]["disclosures"]:
        lines += ["", "## Disclosures", ""] + [f"- {d}" for d in summary["claim"]["disclosures"]]
    lines += ["", "Limits: out-of-context timing covers internal clocked paths only (ports are unconstrained "
              "unless the design has no register-to-register path); one part and period; one model.", ""]
    return "\n".join(lines)


def main(argv=None) -> int:
    from . import ppa
    parser = argparse.ArgumentParser(prog="python -m benchmark.ppa_report")
    sub = parser.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render")
    r.add_argument("--attempt", required=True, type=Path)
    r.add_argument("--title", default="Optimisation benchmark (B3)")
    r.add_argument("--out", required=True, type=Path)
    a = parser.parse_args(argv)
    summary = summarize(read_json(a.attempt / "grades" / "summary.json"), ppa.collect(a.attempt))
    with a.out.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(render_markdown(summary, a.title))
    a.out.with_suffix(".json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps({"report": str(a.out), "verdict": summary["claim"]["verdict"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
