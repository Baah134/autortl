"""Cross-attempt comparison of one arm on synthetic graded rows; no tools or models."""
import json

import pytest

from benchmark import compare, report
from tests.test_benchmark_report import grid


def runs(passes):
    """passes[task] = list of booleans per trial, as single-call rows."""
    return grid({"single_call": passes})


def test_identical_runs_give_zero_difference_with_zero_interval():
    rows = runs({"t1": [True, False], "t2": [False, False], "t3": [True, True]})
    r = compare.compare(rows, "single_call", rows, "single_call", "X", "Y", samples=500)
    p = r["paired"]
    assert p["mean_difference"] == 0.0 and tuple(p["ci95_task_bootstrap"]) == (0.0, 0.0)
    assert (p["tasks_better"], p["tasks_equal"], p["tasks_worse"], p["tasks_compared"]) == (0, 3, 0, 3)
    assert r["a"]["pass_rate"] == r["b"]["pass_rate"] == 0.5
    text = compare.render_markdown(r)
    assert text.startswith("# Y versus X") and "| Y minus X | 3 | +0.0 | +0.0 to +0.0 | 0 / 3 / 0 |" in text
    assert "None: every task has the same pass rate" in text
    assert "An interval that includes 0 does not show a difference." in text


def test_clearly_better_run_has_interval_above_zero_and_is_listed_per_task():
    tasks = [f"t{i}" for i in range(12)]
    a = runs({t: [False] for t in tasks})
    b = grid({"full": {t: [i != 0] for i, t in enumerate(tasks)}})  # a different arm name in run B
    r = compare.compare(a, "single_call", b, "full", "Old", "New", samples=1000)
    p = r["paired"]
    assert round(p["mean_difference"], 6) == round(11 / 12, 6) and p["ci95_task_bootstrap"][0] > 0
    assert (p["tasks_better"], p["tasks_equal"]) == (11, 1)
    assert r["b"]["arm"] == "full" and r["b"]["calls_per_pass"] == 72 / 11 and r["a"]["calls_per_pass"] is None
    text = compare.render_markdown(r, "Synthetic")
    assert text.startswith("# Synthetic") and "| t1 | 0.0% | 100.0% | +100.0 |" in text
    assert "| t0 |" not in text  # equal tasks are not listed


@pytest.mark.parametrize("termination", report.INFRA_TERMINATIONS)
def test_infrastructure_rows_are_excluded(termination):
    a = runs({"t1": [True], "t2": [True]})
    b = runs({"t1": [True], "t2": [False]})
    b[1].update(status="missing", upstream_pass=False, internal=None, termination=termination)
    r = compare.compare(a, "single_call", b, "single_call", "A", "B", samples=200)
    assert (r["b"]["cells"], r["b"]["passes"], r["b"]["pass_rate"], r["b"]["not_evaluable"]) == (1, 1, 1.0, 1)
    assert r["b"]["llm_calls"] == 2  # cost is still charged
    assert r["paired"]["tasks_compared"] == 1 and r["paired"]["mean_difference"] == 0.0
    assert {"task": "t2", "a": 1.0, "b": None, "difference": None} in r["per_task"]
    assert "| t2 | 100.0% | excluded | n/a |" in compare.render_markdown(r)


def test_mismatched_task_sets_are_refused():
    with pytest.raises(report.ReportError, match="different tasks"):
        compare.compare(runs({"t1": [True]}), "single_call", runs({"t2": [True]}), "single_call", samples=50)


def test_missing_arm_is_refused():
    with pytest.raises(report.ReportError, match="no rows for arm 'full'"):
        compare.compare(runs({"t1": [True]}), "full", runs({"t1": [True]}), "single_call", samples=50)


def test_cli_writes_both_files_and_refuses_to_overwrite(tmp_path):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text(json.dumps(runs({"t1": [True], "t2": [False]})))
    b.write_text(json.dumps(runs({"t1": [True], "t2": [True]})))
    out = tmp_path / "compare.md"
    argv = ["--a", str(a), "--a-arm", "single_call", "--a-label", "Model one",
            "--b", str(b), "--b-arm", "single_call", "--b-label", "Model two", "--out", str(out)]
    assert compare.main(argv) == 0
    text = out.read_text(encoding="utf-8")
    assert "| Model two minus Model one | 2 | +50.0 |" in text and "registered and run separately" in text
    data = json.loads(out.with_suffix(".json").read_text())
    assert data["a"]["label"] == "Model one" and data["paired"]["tasks_better"] == 1
    with pytest.raises(FileExistsError):
        compare.main(argv)
