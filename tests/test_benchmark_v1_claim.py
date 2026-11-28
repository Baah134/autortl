"""The proposed V1 decision rule (docs/V1_REGISTRATION_DRAFT.md) on synthetic summaries."""
import json
import shutil

import pytest

from benchmark import claim, finish, report, v1_claim
from tests.test_benchmark_archive import make_attempt
from tests.test_benchmark_report import row

TASKS = [f"t{i:02d}" for i in range(20)]
REDUCES = {"pass_ci": (-0.05, 0.08), "pass_mean": 0.01, "fa_ci": (-0.10, -0.01), "events": 4}


def arm(cells=120, not_evaluable=0, pass_rate=0.8, false_acceptances=0):
    return {"cells": cells - not_evaluable, "not_evaluable": not_evaluable, "pass_rate": pass_rate,
            "passes": round(pass_rate * (cells - not_evaluable)), "internally_accepted": 90,
            "false_acceptances": false_acceptances,
            "false_acceptance_rate": false_acceptances / 90,
            "false_acceptance_cells": [f"t{i:02d}#0" for i in range(false_acceptances)]}


def synthetic(pass_ci=(-0.02, 0.05), pass_mean=0.01, fa_ci=(-0.10, -0.01), events=4, blocked=(),
              off_not_evaluable=0, xcheck_not_evaluable=0, samples=10_000, policies=None, without_record=()):
    """A summarize()-shaped dict with exactly the fields the V1 rule reads."""
    return {"tasks": 40, "cells": 240, "bootstrap": {"samples": samples, "seed": 20261115, "unit": "task"},
            "arms": {"full": arm(not_evaluable=off_not_evaluable, false_acceptances=events),
                     "full_xcheck": arm(not_evaluable=xcheck_not_evaluable)},
            "paired": {"full_xcheck-full": {"tasks_compared": 40, "mean_difference": pass_mean,
                                            "ci95_task_bootstrap": list(pass_ci)}},
            "paired_false_acceptance": {"full_xcheck-full": {
                "tasks_compared": 40, "mean_difference": sum(fa_ci) / 2, "ci95_task_bootstrap": list(fa_ci),
                "tasks_with_false_acceptance": {"full_xcheck": 0, "full": events}}},
            "cross_check": {"cells": 120, "cells_checked": 110, "policies": policies or {"request_traces": 120},
                            "cells_without_record": list(without_record), "outcomes": {"agree": 100},
                            "replanned_cells": ["t01#0"], "disagreement_kept_cells": [],
                            "blocked_tasks": [{"task": t, "cells": [f"{t}#0"]} for t in blocked]}}


def test_constants_equal_the_draft():
    assert v1_claim.MAX_NOT_EVALUABLE == 0.10 and v1_claim.FALSE_ACCEPTANCE_MARGIN == 0.03
    assert v1_claim.PASS_RATE_MARGIN == 0.10 and v1_claim.PASS_RATE_FLOOR == -0.10
    assert v1_claim.MIN_EVENT_TASKS == 3
    assert v1_claim.BOOTSTRAP_SAMPLES == 10_000 == report.BOOTSTRAP_SAMPLES
    assert v1_claim.BOOTSTRAP_SEED == 20261115 == report.BOOTSTRAP_SEED
    assert v1_claim.PRIMARY == "full_xcheck-full" and v1_claim.FROZEN is False
    assert "proposal" in v1_claim.RULE and "PROPOSAL, NOT FROZEN" in v1_claim.__doc__


@pytest.mark.parametrize("kwargs, verdict", [
    # rule 2 before rule 3: both harms present
    ({"pass_ci": (-0.20, -0.01), "pass_mean": -0.1, "fa_ci": (0.01, 0.05)}, "blocks_correct_designs"),
    ({"fa_ci": (0.01, 0.08)}, "increases_false_acceptance"),
    ({"fa_ci": (0.01, 0.08), "events": 0}, "increases_false_acceptance"),  # rule 3 before rule 4
    ({**REDUCES, "events": 2}, "insufficient_events"),                     # rule 4 before rule 5
    (REDUCES, "reduces_false_acceptance"),
    ({**REDUCES, "events": 3}, "reduces_false_acceptance"),                # exactly the minimum
    ({**REDUCES, "pass_ci": (-0.10, 0.06), "pass_mean": 0.0}, "reduces_false_acceptance"),  # boundaries hold
    ({**REDUCES, "pass_ci": (-0.12, 0.06)}, "inconclusive"),               # floor missed
    ({**REDUCES, "pass_mean": -0.005}, "inconclusive"),                    # pass rate fell on average
    ({**REDUCES, "fa_ci": (-0.10, 0.0)}, "inconclusive"),                  # not entirely below 0
    ({"fa_ci": (-0.03, 0.03), "pass_ci": (-0.10, 0.10)}, "no_material_difference"),
    ({"fa_ci": (-0.02, -0.001), "pass_ci": (-0.05, 0.05), "pass_mean": -0.01}, "no_material_difference"),
    ({"fa_ci": (-0.031, 0.02), "pass_ci": (-0.05, 0.05)}, "inconclusive"),
    ({"fa_ci": (-0.02, 0.02), "pass_ci": (-0.11, 0.05)}, "inconclusive"),
])
def test_each_rule_in_order(kwargs, verdict):
    decision = v1_claim.decide(synthetic(**kwargs))
    assert decision["verdict"] == verdict and decision["verdict"] in v1_claim.VERDICTS
    assert decision["default_change_eligible"] is False  # never while the rule is not frozen


def test_a_blocked_task_prevents_adoption_and_is_named():
    decision = v1_claim.decide(synthetic(**REDUCES, blocked=("t07",)))
    assert decision["verdict"] == "inconclusive" and decision["blocked_tasks"][0]["task"] == "t07"
    assert any("Blocked tasks" in d and "t07 (t07#0)" in d for d in decision["disclosures"])
    narrow = v1_claim.decide(synthetic(fa_ci=(-0.02, -0.01), pass_ci=(-0.05, 0.05), events=4, blocked=("t07",)))
    assert narrow["verdict"] == "no_material_difference"  # rule 6 does not look at blocked tasks


@pytest.mark.parametrize("arm_name", ["full", "full_xcheck"])
def test_infrastructure_above_ten_percent_downgrades_either_arm(arm_name):
    key = "off_not_evaluable" if arm_name == "full" else "xcheck_not_evaluable"
    decision = v1_claim.decide(synthetic(**REDUCES, **{key: 13}))  # 13 of 120 > 10%
    assert decision["verdict"] == "inconclusive"
    assert f"incomplete:{arm_name}" in decision["flags"]
    assert "downgraded_from:reduces_false_acceptance" in decision["flags"]
    assert any("descriptive only" in d for d in decision["disclosures"])
    at_limit = v1_claim.decide(synthetic(**REDUCES, **{key: 12}))  # exactly 10% is not above it
    assert at_limit["verdict"] == "reduces_false_acceptance"
    assert any("excluded from rates" in d for d in at_limit["disclosures"])


def test_downgrade_flag_only_when_the_verdict_changed():
    decision = v1_claim.decide(synthetic(fa_ci=(-0.05, 0.02), pass_ci=(-0.05, 0.05), off_not_evaluable=20))
    assert decision["verdict"] == "inconclusive"
    assert not any(f.startswith("downgraded_from:") for f in decision["flags"])


def test_unfrozen_rule_is_flagged_and_a_frozen_one_can_make_the_default_eligible(monkeypatch):
    decision = v1_claim.decide(synthetic(**REDUCES))
    assert decision["flags"] == ["rule_not_frozen"] and decision["frozen"] is False
    assert "has not been frozen" in decision["disclosures"][0]
    monkeypatch.setattr(v1_claim, "FROZEN", True)
    frozen = v1_claim.decide(synthetic(**REDUCES))
    assert frozen["default_change_eligible"] is True and frozen["flags"] == []
    assert v1_claim.decide(synthetic(**{**REDUCES, "events": 2}))["default_change_eligible"] is False


def test_policy_and_record_problems_are_disclosed():
    decision = v1_claim.decide(synthetic(policies={"off": 2, "request_traces": 117, "None": 1},
                                         without_record=("t03#2",)))
    assert any("another cross-check policy: off 2" in d for d in decision["disclosures"])
    assert any("1 full_xcheck cell(s) have no cross-check record: t03#2" in d for d in decision["disclosures"])


@pytest.mark.parametrize("damage, message", [
    (lambda s: s["arms"].pop("full_xcheck"), "needs arms"),
    (lambda s: s["paired"].pop("full_xcheck-full"), "needs arms"),
    (lambda s: s["bootstrap"].update(samples=2000), "10000 resamples"),
    (lambda s: s["bootstrap"].update(seed=1), "seed"),
    (lambda s: s.pop("paired_false_acceptance"), "false-acceptance"),
    (lambda s: s["cross_check"].update(blocked_tasks=None), "blocked tasks"),
    (lambda s: s.pop("cross_check"), "blocked tasks"),
])
def test_missing_inputs_are_refused(damage, message):
    summary = synthetic()
    damage(summary)
    with pytest.raises(v1_claim.ClaimError, match=message):
        v1_claim.decide(summary)
    assert issubclass(v1_claim.ClaimError, claim.ClaimError)


# ------------------------------------------------- end to end through summarize
def graded(off_false_accept, blocked=()):
    """C-off falsely accepts trial 0 of the listed tasks; C-xcheck passes every cell except blocked tasks."""
    rows = []
    for i, t in enumerate(TASKS):
        for n in range(3):
            if t in blocked:
                rows += [row(t, "full", n, True),
                         row(t, "full_xcheck", n, False, internal="rejected",
                             cross_check_policy="request_traces", cross_check_outcomes=["replanned", "agree"])]
                continue
            rows.append(row(t, "full", n, not (i in off_false_accept and n == 0)))
            rows.append(row(t, "full_xcheck", n, True, cross_check_policy="request_traces",
                            cross_check_outcomes=["agree"]))
    return report.summarize(rows)  # the registered 10,000 resamples


def test_end_to_end_reduction_is_adopted():
    s = graded(off_false_accept=range(8))
    decision = v1_claim.decide(s)
    assert decision["verdict"] == "reduces_false_acceptance", decision
    assert decision["events"] == {"off_tasks_with_false_acceptance": 8, "minimum": 3}
    assert decision["false_acceptance"]["mean_difference"] == pytest.approx(-8 / 3 / 20)
    assert decision["false_acceptance"]["ci95"][1] < 0 and decision["pass_rate"]["mean_difference"] > 0
    assert decision["cross_check"]["outcomes"] == {"agree": 60}


def test_end_to_end_few_events_are_insufficient():
    assert v1_claim.decide(graded(off_false_accept=(0, 1)))["verdict"] == "insufficient_events"


def test_end_to_end_blocked_task_stops_adoption():
    s = graded(off_false_accept=range(2, 10), blocked=("t00",))
    assert s["cross_check"]["blocked_tasks"] == [{"task": "t00", "cells": ["t00#0", "t00#1", "t00#2"]}]
    assert v1_claim.decide(s)["verdict"] != "reduces_false_acceptance"


def test_cli_writes_the_claim_and_refuses_a_non_v1_report(tmp_path, capsys):
    path = tmp_path / "report.json"
    path.write_text(json.dumps(synthetic(**REDUCES)))
    assert v1_claim.main(["--report", str(path), "--out", str(tmp_path / "claim.json")]) == 0
    assert json.loads((tmp_path / "claim.json").read_text())["verdict"] == "reduces_false_acceptance"
    other = report.summarize([row("t1", "single_call", 0, True, internal="unverified"), row("t1", "full", 0, True)])
    path.write_text(json.dumps(other))
    assert v1_claim.main(["--report", str(path)]) == 2
    assert "v1_claim refused" in capsys.readouterr().err


# ------------------------------------------------------------------- finish
def v1_attempt(tmp_path):
    """make_attempt with arms C-off and C-xcheck instead of A and C."""
    attempt = make_attempt(tmp_path)
    for top in ("runs", "grades"):
        shutil.move(str(attempt / top / "t1-single_call-0"), str(attempt / top / "t1-full_xcheck-0"))
    record = json.loads((attempt / "runs" / "t1-full_xcheck-0" / "run.json").read_text())
    record["cell"]["arm"] = "full_xcheck"
    (attempt / "runs" / "t1-full_xcheck-0" / "run.json").write_text(json.dumps(record))
    rows = json.loads((attempt / "grades" / "summary.json").read_text())
    for r in rows:
        if r["arm"] == "single_call":
            r.update(arm="full_xcheck", internal="accepted", cross_check_policy="request_traces",
                     cross_check_outcomes=["agree"])
    (attempt / "grades" / "summary.json").write_text(json.dumps(rows))
    return attempt


def test_finish_applies_the_v1_rule_to_a_v1_run(tmp_path):
    attempt, out = v1_attempt(tmp_path), tmp_path / "evidence" / "v1"
    result = finish.finish(tmp_path / "m.json", tmp_path, attempt, out, catalog=None, title="V1 synthetic",
                           forbidden=("someone",), audit=False, links="[r](x)")
    assert result["verdict"] == "insufficient_events"  # one task, no false acceptance in C-off
    assert result["readme_row"].startswith("| **Request cross-check (V1, rule proposed, not frozen).**")
    readme = (out / "README.md").read_text()
    assert "## Claim (docs/V1_REGISTRATION_DRAFT.md decision rule (proposal, not frozen))" in readme
    assert "pre-registered rule" not in readme and "Verdict: `insufficient_events`" in readme
    assert "Arms C (full harness) and C-xcheck (full harness with the request cross-check)" in readme
    assert "\n## Request cross-check" not in readme and "\n### Request cross-check" in readme
    assert json.loads((out / "claim.json").read_text())["rule"] == v1_claim.RULE


def test_finish_keeps_the_registered_claim_heading_for_arms_a_and_c(tmp_path):
    out = tmp_path / "evidence" / "final"
    finish.finish(tmp_path / "m.json", tmp_path, make_attempt(tmp_path), out, catalog=None, title="t", audit=False)
    assert "## Claim (pre-registered rule, docs/DECISIONS.md 2026-11-20)" in (out / "README.md").read_text()
