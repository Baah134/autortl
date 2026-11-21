"""Pre-registered claim rule and the one-command finish, on synthetic graded rows."""
import json

import pytest

from benchmark import claim, finish, report
from tests.test_benchmark_archive import make_attempt
from tests.test_benchmark_report import grid, row

TASKS = [f"t{i:02d}" for i in range(20)]


def summary_of(a_pass, c_pass, b_pass=None, extra_rows=(), samples=2000, false_accept=()):
    """Harness arms reject their failing designs, except tasks listed in false_accept."""
    passes = {"single_call": {t: a_pass(i) for i, t in enumerate(TASKS)},
              "full": {t: c_pass(i) for i, t in enumerate(TASKS)}}
    if b_pass:
        passes["ablation"] = {t: b_pass(i) for i, t in enumerate(TASKS)}
    rows = grid(passes)
    for r in rows:
        if r["arm"] != "single_call" and not r["upstream_pass"] and r["task"] not in false_accept:
            r["internal"] = "rejected"
    return report.summarize(rows + list(extra_rows), samples=samples)


@pytest.mark.parametrize("ci, verdict", [
    ((0.01, 0.30), "harness_better"), ((-0.30, -0.02), "single_call_better"),
    ((-0.05, 0.08), "no_material_difference"), ((-0.10, 0.10), "no_material_difference"),
    ((-0.04, 0.25), "inconclusive"), ((0.0, 0.2), "inconclusive")])
def test_interval_rule(ci, verdict):
    assert claim.classify(ci) == verdict


def test_harness_better_with_cost_ratio_and_sentence():
    s = summary_of(lambda i: [i < 8] * 3, lambda i: [i < 18] * 3)
    c = claim.decide(s)
    assert c["verdict"] == "harness_better" and c["ci95"][0] > 0
    assert c["calls_per_pass_ratio"] == pytest.approx((6 * 60 / 54) / (60 / 24))
    assert "passes more tasks than a single model call" in c["sentence"] and "20 tasks" in c["sentence"]
    assert c["flags"] == [] and c["disclosures"] == []


def test_identical_arms_are_no_material_difference():
    s = summary_of(lambda i: [i < 15] * 3, lambda i: [i < 15] * 3, b_pass=lambda i: [i < 15] * 3)
    c = claim.decide(s)
    assert c["verdict"] == "no_material_difference" and c["ci95"] == [0.0, 0.0]
    assert set(c["secondary"]) == {"full-ablation", "ablation-single_call"}
    assert "same within 10 pp" in c["sentence"]


def test_small_noisy_difference_is_inconclusive():
    s = summary_of(lambda i: [i < 10] * 3, lambda i: [i < 12] * 3)
    c = claim.decide(s)
    assert c["verdict"] == "inconclusive" and "too wide" in c["sentence"]


def test_false_acceptances_are_disclosed_by_cell_and_flagged_above_limit():
    once = claim.decide(summary_of(lambda i: [True] * 3, lambda i: [i != 0] * 3, false_accept={"t00"}))
    assert any("t00#0, t00#1, t00#2" in d for d in once["disclosures"])
    assert once["flags"] == []  # 3 of 60 accepted is exactly the 5% limit, not above it
    twice = claim.decide(summary_of(lambda i: [True] * 3, lambda i: [i > 1] * 3, false_accept={"t00", "t01"}))
    assert "unreliable_acceptance:full" in twice["flags"]


def test_infrastructure_share_above_limit_downgrades_the_verdict():
    blocked = [row(f"t{i:02d}", "full", 3, False, termination="model_blocked") for i in range(10)]
    s = summary_of(lambda i: [i < 8] * 3 + [i < 8], lambda i: [i < 18] * 3, extra_rows=blocked)
    c = claim.decide(s)
    assert c["verdict"] == "inconclusive" and "downgraded_from:harness_better" in c["flags"]
    assert any("descriptive only" in d for d in c["disclosures"])


def test_missing_primary_comparison_is_refused():
    s = report.summarize(grid({"single_call": {"t1": [True]}}), samples=10)
    with pytest.raises(claim.ClaimError):
        claim.decide(s)


def test_readme_row_is_one_table_line():
    c = claim.decide(summary_of(lambda i: [i < 8] * 3, lambda i: [i < 18] * 3))
    line = claim.readme_row(c, {"tasks": 20}, "[results](evidence/x/README.md)")
    assert line.startswith("| **Registered comparison") and line.endswith("| [results](evidence/x/README.md) |")
    assert "\n" not in line


def test_cli_writes_claim(tmp_path, capsys):
    path = tmp_path / "report.json"
    path.write_text(json.dumps(summary_of(lambda i: [True] * 3, lambda i: [True] * 3)))
    assert claim.main(["--report", str(path), "--out", str(tmp_path / "claim.json")]) == 0
    assert json.loads((tmp_path / "claim.json").read_text())["verdict"] == "no_material_difference"


# ------------------------------------------------------------------ finish
def test_finish_archives_claims_writes_readme_seals_and_audits(tmp_path):
    attempt, out, audits = make_attempt(tmp_path), tmp_path / "evidence" / "final", []
    result = finish.finish(tmp_path / "m.json", tmp_path, attempt, out, catalog=None, title="Synthetic final",
                           forbidden=("someone",), links="[r](x)", run_audit=lambda: audits.append(1))
    assert audits == [1] and result["verdict"] == "no_material_difference"
    assert result["readme_row"].endswith("| [r](x) |")
    readme = (out / "README.md").read_text()
    assert readme.startswith("# Synthetic final") and "Verdict: `no_material_difference`" in readme
    assert "### Functional correctness" in readme and "someone" not in readme
    recorded = json.loads((out / "archive-manifest.json").read_text())
    assert {"README.md", "claim.json", "report.md"} <= set(recorded)


def test_finish_grades_only_when_ungraded_and_never_overwrites(tmp_path):
    attempt = make_attempt(tmp_path, graded=False)
    with pytest.raises(finish.FinishError, match="not graded"):
        finish.finish(tmp_path / "m.json", tmp_path, attempt, tmp_path / "o", catalog=None, title="t", audit=False)
    graded = make_attempt(tmp_path / "g")
    calls = []
    finish.finish(tmp_path / "m.json", tmp_path, graded, tmp_path / "o2", catalog=None, title="t", audit=False,
                  grade=lambda *a: calls.append(a))
    assert calls == []  # an existing summary is reused, never regraded
    with pytest.raises(finish.FinishError, match="already exists"):
        finish.finish(tmp_path / "m.json", tmp_path, graded, tmp_path / "o2", catalog=None, title="t", audit=False)
