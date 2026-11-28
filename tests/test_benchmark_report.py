"""Benchmark grading gate and report statistics on synthetic rows; no tools or models."""
import json
import subprocess
from pathlib import Path

import pytest

from benchmark import pilot, report
from benchmark import verilogeval as ve

DATA = Path(__file__).parent / "fixtures" / "verilogeval" / "dataset"
REPO = Path(__file__).resolve().parents[1]


def row(task, arm, trial, passed, internal=None, status=None, calls=1, **extra):
    base = {"task": task, "arm": arm, "trial": trial, "termination": "done",
            "internal": internal if internal is not None else ("unverified" if arm == "single_call" else "accepted"),
            "status": status or ("pass" if passed else "fail"), "upstream_code": "." if passed else "R",
            "upstream_pass": passed, "mismatches": 0 if passed else 3, "samples": 10, "run_status": "done",
            "llm_calls": calls, "input_tokens": 1000 * calls, "output_tokens": 50 * calls,
            "seconds": 10.0 * calls, "tool_seconds": 0.0}
    base.update(extra)
    return base


def grid(passes):
    """passes[arm][task] = list of booleans per trial."""
    return [row(task, arm, trial, ok, calls=1 if arm == "single_call" else 6)
            for arm, tasks in passes.items() for task, trials in tasks.items() for trial, ok in enumerate(trials)]


# ---------------------------------------------------------------- statistics
def test_wilson_matches_known_values():
    low, high = report.wilson(8, 10)
    assert round(low, 4) == 0.4902 and round(high, 4) == 0.9433  # standard Wilson 95% for 8/10
    assert report.wilson(0, 0) == (0.0, 1.0)
    assert report.wilson(0, 5)[0] == 0.0 and report.wilson(5, 5)[1] == 1.0


def test_cluster_bootstrap_is_deterministic_and_degenerate_cases_are_exact():
    values = {f"t{i}": v for i, v in enumerate([1, 1, 0, 1, 0, 1, 1, 0, 1, 1])}
    first = report.cluster_bootstrap(values, samples=2000)
    assert first == report.cluster_bootstrap(dict(reversed(list(values.items()))), samples=2000)
    assert first[0] < 0.7 < first[1] and 0.3 < first[0] and first[1] <= 1.0
    assert report.cluster_bootstrap({"a": 1.0, "b": 1.0}, samples=200) == (1.0, 1.0)
    with pytest.raises(report.ReportError):
        report.cluster_bootstrap({})


def test_summary_counts_rates_missing_and_cost():
    rows = grid({"single_call": {"t1": [True, True], "t2": [False, True]},
                 "full": {"t1": [True, True], "t2": [True, True]}})
    rows[-1].update(status="missing", upstream_pass=False, upstream_code=None, internal=None,
                    termination="failed")  # the harness produced nothing: a real failure
    s = report.summarize(rows, samples=500)
    a, c = s["arms"]["single_call"], s["arms"]["full"]
    assert (a["passes"], a["cells"], a["pass_rate"]) == (3, 4, 0.75)
    assert (c["passes"], c["missing"], c["pass_rate"]) == (3, 1, 0.75)  # missing counts as failure
    assert c["terminations"] == {"done": 3, "failed": 1} and c["not_evaluable"] == 0
    assert a["llm_calls"] == 4 and c["llm_calls"] == 24 and c["calls_per_pass"] == 8.0
    assert a["tasks_always_pass"] == 1 and a["tasks_never_pass"] == 0
    assert s["tasks"] == 2 and s["cells"] == 8 and s["bootstrap"]["unit"] == "task"


@pytest.mark.parametrize("termination", report.INFRA_TERMINATIONS)
def test_infrastructure_stops_are_not_verdicts(termination):
    """Hard rule: quota blocks and interruptions never count as design failures."""
    rows = grid({"single_call": {"t1": [True, True], "t2": [True, True]},
                 "full": {"t1": [True, True], "t2": [True, True]}})
    rows[1].update(status="missing", upstream_pass=False, upstream_code=None, internal=None,
                   termination=termination)  # single_call, t1, trial 1
    s = report.summarize(rows, samples=300)
    a = s["arms"]["single_call"]
    assert (a["passes"], a["cells"], a["pass_rate"], a["missing"]) == (3, 3, 1.0, 0)
    assert a["not_evaluable"] == 1 and a["not_evaluable_cells"] == ["t1#1"]
    assert a["terminations"][termination] == 1 and a["llm_calls"] == 4  # cost is still charged
    assert s["paired"]["full-single_call"]["mean_difference"] == 0.0
    assert "| A single call | 3/3 | 100.0% |" in report.render_markdown(s) and "| 0 | 1 |" in report.render_markdown(s)


def test_task_with_no_verdict_in_one_arm_is_dropped_from_that_pair_only():
    rows = grid({"single_call": {"t1": [True], "t2": [False]}, "full": {"t1": [True], "t2": [True]}})
    rows[1].update(status="missing", upstream_pass=False, termination="model_blocked", internal=None)  # A, t2
    s = report.summarize(rows, samples=200)
    pair = s["paired"]["full-single_call"]
    assert pair["tasks_compared"] == 1 and pair["mean_difference"] == 0.0
    assert s["arms"]["full"]["cells"] == 2 and s["arms"]["single_call"]["cells"] == 1
    only_blocked = grid({"single_call": {"t1": [True]}})
    only_blocked[0]["termination"] = "interrupted"
    with pytest.raises(report.ReportError, match="no evaluable cell"):
        report.summarize(only_blocked, samples=50)


def test_false_acceptance_uses_internally_accepted_denominator():
    rows = grid({"single_call": {"t1": [True], "t2": [True]},
                 "full": {"t1": [True], "t2": [False]}})
    s = report.summarize(rows, samples=200)
    full = s["arms"]["full"]
    assert (full["internally_accepted"], full["false_acceptances"], full["false_acceptance_rate"]) == (2, 1, 0.5)
    assert full["false_acceptance_cells"] == ["t2#0"]
    single = s["arms"]["single_call"]  # never internally verified: no accepted set
    assert single["internally_accepted"] == 0 and single["false_acceptance_rate"] is None


def test_paired_difference_is_by_task_and_signed():
    rows = grid({"single_call": {"t1": [True, True], "t2": [False, False], "t3": [True, False]},
                 "ablation": {"t1": [True, True], "t2": [False, True], "t3": [True, True]},
                 "full": {"t1": [True, True], "t2": [True, True], "t3": [True, False]}})
    s = report.summarize(rows, samples=1000)
    p = s["paired"]["full-single_call"]
    assert round(p["mean_difference"], 4) == round((0 + 1 + 0) / 3, 4)
    assert (p["tasks_better"], p["tasks_equal"], p["tasks_worse"]) == (1, 2, 0)
    q = s["paired"]["full-ablation"]
    assert (q["tasks_better"], q["tasks_worse"]) == (1, 1) and abs(q["mean_difference"]) < 1e-9
    assert q["ci95_task_bootstrap"][0] <= 0 <= q["ci95_task_bootstrap"][1]
    assert set(s["paired"]) == {"full-single_call", "full-ablation", "ablation-single_call"}


def test_grader_disagreement_and_strict_counts_are_reported():
    rows = grid({"full": {"t1": [True], "t2": [True]}})
    rows[1]["status"] = "runtime_error"  # upstream says pass, strict exit check does not
    full = report.summarize(rows, samples=100)["arms"]["full"]
    assert full["passes"] == 2 and full["strict_passes"] == 1 and full["grader_disagreements"] == 1


def test_category_breakdown_and_markdown():
    rows = grid({"single_call": {"t1": [True], "t2": [False]}, "full": {"t1": [True], "t2": [True]}})
    catalog = {"t1": {"category": "sequential", "family": "t1"}, "t2": {"category": "fsm_control", "family": "t2"}}
    s = report.summarize(rows, catalog, samples=200)
    assert s["categories"]["fsm_control"]["single_call"] == {"tasks": 1, "pass_rate": 0.0}
    text = report.render_markdown(s, "Synthetic")
    assert text.startswith("# Synthetic")
    assert "| C full harness | 2/2 | 100.0% | 34.2 to 100.0 (Wilson*) |" in text  # degenerate bootstrap
    assert "| A single call | 1/2 | 50.0% |" in text and "bootstrap cannot vary" in text
    assert "C full harness minus A single call | +50.0 |" in text
    assert "| fsm_control | 1 | 0.0% | 100.0% |" in text
    assert "An interval that includes 0 does not show a difference." in text


def test_invalid_rows_are_refused():
    good = grid({"full": {"t1": [True]}})
    with pytest.raises(report.ReportError, match="no graded rows"):
        report.summarize([])
    with pytest.raises(report.ReportError, match="duplicate cell"):
        report.summarize(good + good)
    with pytest.raises(report.ReportError, match="unknown arm"):
        report.summarize([dict(good[0], arm="bogus")])
    with pytest.raises(report.ReportError, match="different tasks"):
        report.summarize(grid({"single_call": {"t1": [True]}, "full": {"t2": [True]}}), samples=50)


# ------------------------------------------------------------- grading gate
@pytest.fixture
def attempt(tmp_path, monkeypatch):
    manifest = ve.build_manifest(DATA, ["Prob900_inv"], dataset_commit="a" * 40, source_commit="b" * 40,
                                 runtime_commit="c" * 40, runtime_sha256="d" * 64,
                                 requested_model="unobserved-cli-default",
                                 budgets={k: pilot.PROVISIONAL_BUDGETS[k] for k in ("single_call", "full")})
    monkeypatch.setattr(pilot, "vivado_tools", lambda: {})
    task = ve.load_task(DATA, "Prob900_inv")
    reply = "```verilog\nmodule TopModule(input a, output y);\n  assign y = ~a;\nendmodule\n```\n"
    pilot.run_single_call(manifest, task, tmp_path / "runs" / "Prob900_inv-single_call-0",
                          ask=lambda *a, **k: reply)
    return manifest, tmp_path


def test_grading_refuses_until_every_cell_is_sealed(attempt):
    manifest, root = attempt
    with pytest.raises(report.ReportError, match="1 of 2 cells are not sealed"):
        report.grade_attempt(manifest, DATA, root)
    assert not (root / "grades").exists()


def test_grade_attempt_writes_rows_for_all_cells(attempt, monkeypatch):
    manifest, root = attempt

    def blocked(cmd, **kwargs):  # the full arm ends without a winner: sealed missing
        run_dir = Path(cmd[cmd.index("--output-dir") + 1])
        run_dir.mkdir(parents=True)
        (run_dir / "run_summary.json").write_text(json.dumps({"status": "model_blocked"}))
        return subprocess.CompletedProcess(cmd, 1, "", "")

    pilot.run_full(manifest, ve.load_task(DATA, "Prob900_inv"), root / "runs" / "Prob900_inv-full-0", runner=blocked)
    monkeypatch.setattr(ve, "grade", lambda files, task, workdir, **kw: (
        Path(workdir).mkdir(parents=True) or {"task": task.id, "status": "pass", "upstream_code": ".",
                                                "upstream_pass": True, "mismatches": 0, "samples": 20}))
    rows = report.grade_attempt(manifest, DATA, root)
    assert [(r["arm"], r["status"], r["upstream_pass"], r["termination"]) for r in rows] == [
        ("full", "missing", False, "model_blocked"), ("single_call", "pass", True, "done")]
    assert json.loads((root / "grades" / "summary.json").read_text()) == rows
    assert set(rows[0]) == set(report.ROW_KEYS)
    with pytest.raises(FileExistsError):  # an attempt is graded once
        report.grade_attempt(manifest, DATA, root)


def test_render_cli_reads_pilot_summaries_without_trial(tmp_path):
    rows = [{k: v for k, v in r.items() if k != "trial"}
            for r in grid({"single_call": {"t1": [True]}, "full": {"t1": [True]}})]
    summary = tmp_path / "summary.json"
    summary.write_text(json.dumps(rows))
    out = tmp_path / "report.md"
    assert report.main(["render", "--summary", str(summary), "--out", str(out)]) == 0
    assert "| C full harness | 1/1 | 100.0% |" in out.read_text(encoding="utf-8")
    assert json.loads(out.with_suffix(".json").read_text())["arms"]["full"]["passes"] == 1
    with pytest.raises(FileExistsError):
        report.main(["render", "--summary", str(summary), "--out", str(out)])
