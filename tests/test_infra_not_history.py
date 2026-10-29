"""An infrastructure-blocked bench entry never enters the curriculum history.

Taxonomy: infra_blocked_entry_enters_history (tier1-campaign-02, host standby).
"""
import json

from curriculum import runner
from tests.test_curriculum import curriculum, records, successful_metrics  # noqa: F401


def entry_outcomes(orch, outcome_for):
    construct = orch.side_effect

    def build(cfg, run_dir):
        instance = construct(cfg, run_dir)
        instance.run.side_effect = lambda: outcome_for(run_dir.name)
        return instance

    orch.side_effect = build


def test_an_infra_blocked_entry_gives_the_campaign_no_verdict(curriculum):  # noqa: F811
    _, orch, output = curriculum
    assert runner.run_tier(0, output_root=output) == 0  # one qualifying run first
    before = runner.RESULTS.read_bytes()
    entry_outcomes(orch, lambda name: {"status": "baseline_blocked", "failure_kind": "infra",
                                       "error": "timed out after 120s"} if name == "b"
                   else {"status": "done", "best_metrics": successful_metrics()})
    assert runner.run_tier(0, output_root=output) == 3
    assert runner.RESULTS.read_bytes() == before  # the streak is neither advanced nor reset
    summaries = [json.loads(p.read_text()) for p in output.rglob("summary.json")]
    assert [s.get("infra_blocked_entries") for s in summaries].count(["b"]) == 1


def test_a_design_failure_still_enters_the_history(curriculum):  # noqa: F811
    _, orch, output = curriculum
    entry_outcomes(orch, lambda name: {"status": "baseline_blocked", "failure_kind": "design",
                                       "error": "baseline simulation failed"} if name == "b"
                   else {"status": "done", "best_metrics": successful_metrics()})
    assert runner.run_tier(0, output_root=output) == 0  # 4/5 = 80% still qualifies
    record = records()[-1]
    assert (record["passed"], record["total"]) == (4, 5)
    assert "infra_blocked_entries" not in record
