"""Paired PPA report statistics on synthetic graded rows and records; no tools or models."""
import json
import math

import pytest

from benchmark import ppa, ppa_report as pr
from benchmark.report import ReportError

FLOW = dict(ppa.FLOW, template_sha256="a" * 64)


def row(task, arm, trial, passed, termination="done"):
    return {"task": task, "arm": arm, "trial": trial, "upstream_pass": passed, "termination": termination,
            "status": "pass" if passed else "fail"}


def rec(task, arm, trial, lut, ff=10, wns=1.0, whs=0.1, status="measured", flow=FLOW, tool="Vivado v.2025.2"):
    metrics = None if status != "measured" else {
        "lut": lut, "ff": ff, "dsp": 0, "bram": 0.0, "wns_ns": wns, "whs_ns": whs,
        "timing_met": wns >= 0 and whs >= 0, "no_timing_paths": False}
    return {"cell": {"task": task, "arm": arm, "trial": trial}, "status": status, "metrics": metrics,
            "flow": flow, "tool_version": tool}


def grid(luts, trials=1):
    """luts[task] = (lut_A, lut_C); None = functionally failing."""
    rows, records = [], []
    for task, pair in luts.items():
        for arm, lut in zip((pr.ARM_A, pr.ARM_C), pair):
            for trial in range(trials):
                rows.append(row(task, arm, trial, lut is not None))
                if lut is not None:
                    records.append(rec(task, arm, trial, lut))
    return rows, records


def test_lut_ratio_is_a_geometric_mean_over_area_pairs_only():
    rows, records = grid({"t1": (99, 49), "t2": (39, 39), "t3": (None, 9), "t4": (19, 79)})
    s = pr.summarize(rows, records, samples=500)
    assert s["pairs"] == {"functional": 3, "area": 3, "tasks_without_functional_pair": ["t3"],
                          "functional_pairs_without_metrics": []}
    expected = math.exp((math.log(50 / 100) + 0 + math.log(80 / 20)) / 3)  # LUT + 1
    assert s["lut_ratio"]["geometric_mean_ratio"] == pytest.approx(expected)
    assert s["lut_ratio"]["per_task_ratio"] == pytest.approx({"t1": 0.5, "t2": 1.0, "t4": 4.0})
    assert (s["lut_ratio"]["tasks_smaller"], s["lut_ratio"]["tasks_equal"], s["lut_ratio"]["tasks_larger"]) == (1, 1, 1)
    low, high = s["lut_ratio"]["ci95_task_bootstrap"]
    assert low <= expected <= high
    assert s["arms"][pr.ARM_A]["functional_passes"] == 3 and s["arms"][pr.ARM_C]["functional_passes"] == 4


def test_trials_are_pooled_per_task_before_pairing():
    rows, records = grid({"t1": (9, 9)}, trials=2)
    records = [r for r in records if not (r["cell"]["arm"] == pr.ARM_C and r["cell"]["trial"] == 1)]
    records.append(rec("t1", pr.ARM_C, 1, 39))  # C trials: 9 and 39 -> geometric mean of 10 and 40 = 20
    s = pr.summarize(rows, records, samples=200)
    assert s["lut_ratio"]["per_task_ratio"]["t1"] == pytest.approx(2.0)


def test_failing_trials_never_enter_area_or_closure_of_the_passing_ones():
    rows = [row("t1", pr.ARM_A, 0, True), row("t1", pr.ARM_A, 1, False),
            row("t1", pr.ARM_C, 0, True), row("t1", pr.ARM_C, 1, True)]
    records = [rec("t1", pr.ARM_A, 0, 19), rec("t1", pr.ARM_C, 0, 19), rec("t1", pr.ARM_C, 1, 19, wns=-0.2)]
    s = pr.summarize(rows, records, samples=200)
    assert s["closure_difference"]["mean_difference"] == pytest.approx(0.5 - 1.0)
    assert s["arms"][pr.ARM_C]["closure_rate"] == 0.5 and s["arms"][pr.ARM_A]["closure_rate"] == 1.0


def test_synthesis_failure_counts_as_not_closed_and_has_no_area():
    rows = [row("t1", pr.ARM_A, 0, True), row("t1", pr.ARM_C, 0, True)]
    records = [rec("t1", pr.ARM_A, 0, 30), rec("t1", pr.ARM_C, 0, None, status="synth_failed")]
    s = pr.summarize(rows, records, samples=200)
    assert s["pairs"]["area"] == 0 and s["pairs"]["functional_pairs_without_metrics"] == ["t1"]
    assert s["lut_ratio"] is None and s["closure_difference"]["mean_difference"] == -1.0
    assert s["arms"][pr.ARM_C]["synth_failed_cells"] == ["t1#0"]
    assert s["claim"]["verdict"] == "insufficient_pairs"
    assert any("failed synthesis" in d for d in s["claim"]["disclosures"])


def test_report_refuses_incomplete_mixed_or_impossible_records():
    rows, records = grid({"t1": (19, 9), "t2": (29, 29)})
    with pytest.raises(ReportError, match="no sealed PPA record"):
        pr.summarize(rows, records[:-1], samples=50)
    mixed = records[:-1] + [rec("t2", pr.ARM_C, 0, 29, flow=dict(FLOW, period_ns=5.0))]
    with pytest.raises(ReportError, match="one flow"):
        pr.summarize(rows, mixed, samples=50)
    other_tool = records[:-1] + [rec("t2", pr.ARM_C, 0, 29, tool="Vivado v.2024.1")]
    with pytest.raises(ReportError, match="one flow"):
        pr.summarize(rows, other_tool, samples=50)
    failing = [dict(r, upstream_pass=False) if (r["task"], r["arm"]) == ("t1", pr.ARM_A) else r for r in rows]
    with pytest.raises(ReportError, match="functionally failing"):
        pr.summarize(failing, records, samples=50)
    with pytest.raises(ReportError, match="two PPA records"):
        pr.summarize(rows, records + [records[0]], samples=50)
    with pytest.raises(ReportError, match="unregistered"):
        pr.summarize(rows, records + [rec("t9", pr.ARM_A, 0, 5)], samples=50)
    with pytest.raises(ReportError, match="different tasks"):
        pr.summarize(rows + [row("t3", pr.ARM_A, 0, False)], records, samples=50)


def test_infrastructure_cells_are_excluded_and_can_downgrade_the_verdict():
    luts = {f"t{i}": (99, 49) for i in range(12)}
    rows, records = grid(luts)
    s = pr.summarize(rows, records, samples=500)
    assert s["claim"]["verdict"] == "harness_smaller" and s["lut_ratio"]["ci95_task_bootstrap"][1] < 1
    stopped = {("t0", pr.ARM_C), ("t1", pr.ARM_C)}
    rows2 = [dict(r, termination="model_blocked", upstream_pass=False) if (r["task"], r["arm"]) in stopped else r
             for r in rows]
    records2 = [r for r in records if (r["cell"]["task"], r["cell"]["arm"]) not in stopped]
    s2 = pr.summarize(rows2, records2, samples=500)
    assert s2["arms"][pr.ARM_C]["not_evaluable"] == 2 and s2["pairs"]["area"] == 10
    assert s2["claim"]["verdict"] == "inconclusive" and "downgraded_from:harness_smaller" in s2["claim"]["flags"]


@pytest.mark.parametrize("ci,verdict", [((0.5, 0.9), "harness_smaller"), ((1.01, 2.0), "single_call_smaller"),
                                        ((0.95, 1.05), "no_material_difference"), ((0.8, 1.2), "inconclusive")])
def test_ratio_classification(ci, verdict):
    assert pr.classify_ratio(ci) == verdict


def test_too_few_pairs_is_descriptive_only():
    rows, records = grid({f"t{i}": (99, 49) for i in range(pr.MIN_AREA_PAIRS - 1)})
    s = pr.summarize(rows, records, samples=200)
    assert s["claim"]["verdict"] == "insufficient_pairs" and s["claim"]["rule"].startswith("DRAFT")


def test_rendered_report_states_flow_verdict_and_per_task_ratios():
    rows, records = grid({"t1": (99, 49), "t2": (39, 39)})
    s = pr.summarize(rows, records, samples=200)
    text = pr.render_markdown(s)
    assert "xc7a35tcpg236-1 at 10.0 ns (Vivado v.2025.2)" in text
    assert "`insufficient_pairs`" in text and "| t1 | 0.500 |" in text and "Timing closure difference" in text
    json.dumps(s)  # the summary is plain JSON
