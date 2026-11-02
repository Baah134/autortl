"""Resource objectives compare lexicographically between feasible designs.

Taxonomy: equal_lut_ff_saving_discarded. crc16_stream_build (explore-tier4-01
iteration 3: 16 LUT, 34 -> 18 FF; explore-tier4-02 iteration 2: 16 LUT,
34 -> 19 FF) verified and met timing but was rejected under minimize_luts
because the LUT count was already at its floor. minimize_luts now compares
(lut_used, ff_used) and minimize_ffs (ff_used, lut_used); maximize_freq and
minimize_power are unchanged, and a missing secondary gives no tie-break.
"""
import json
from unittest.mock import Mock

import pytest

from autortl import fsm, prompts
from autortl.bestofn import Candidate, select
from autortl.config import RunConfig
from autortl.contract_context import render_fixed_optimize_contract, run_evidence
from autortl.objectives import improvement_kind, tie_break_field
from autortl.report_parser import VivadoMetrics
from tests.test_fsm_resume import WINNER, configuration, install_models, install_tools


def metric(**changes):
    result = dict(sim_passed=True, sim_error="", synth_error="", timing_met=True,
                  wns_ns=.445, whs_ns=.1, lut_used=16, ff_used=34, dynamic_power_w=.018)
    result.update(changes)
    return result


@pytest.mark.parametrize("new, expected", [
    (dict(lut_used=16, ff_used=18), "objective"),   # equal LUTs, fewer FFs (crc16 iteration 3)
    (dict(lut_used=16, ff_used=34), None),          # equal LUTs, equal FFs
    (dict(lut_used=15, ff_used=40), "objective"),   # fewer LUTs, more FFs
    (dict(lut_used=17, ff_used=10), None),          # more LUTs never wins on FFs
    (dict(lut_used=16, ff_used=35), None),          # equal LUTs, more FFs
])
def test_minimize_luts_is_lexicographic(new, expected):
    assert improvement_kind(metric(**new), metric(), "minimize_luts") == expected


@pytest.mark.parametrize("new, expected", [
    (dict(ff_used=34, lut_used=12), "objective"),   # equal FFs, fewer LUTs
    (dict(ff_used=34, lut_used=16), None),
    (dict(ff_used=30, lut_used=40), "objective"),   # fewer FFs, more LUTs
    (dict(ff_used=35, lut_used=1), None),           # more FFs never wins on LUTs
])
def test_minimize_ffs_mirrors_it(new, expected):
    assert improvement_kind(metric(**new), metric(), "minimize_ffs") == expected


@pytest.mark.parametrize("missing", [None, float("nan"), float("inf"), True, "18", -1])
@pytest.mark.parametrize("side", ["new", "best"])
def test_missing_or_non_finite_secondary_gives_no_tie_break(missing, side):
    values = {"new": 18, "best": 34}
    values[side] = missing
    new, best = metric(ff_used=values["new"]), metric(ff_used=values["best"])
    assert tie_break_field("minimize_luts", new, best) is None
    assert improvement_kind(new, best, "minimize_luts") is None
    # The primary comparison is unchanged.
    assert improvement_kind(metric(lut_used=15, ff_used=values["new"]), best, "minimize_luts") == "objective"


@pytest.mark.parametrize("objective", ["maximize_freq", "minimize_power"])
def test_other_objectives_have_no_tie_break(objective):
    assert tie_break_field(objective, metric(), metric()) is None
    assert improvement_kind(metric(ff_used=1, lut_used=1), metric(), objective) is None


def test_tie_break_never_applies_outside_feasible_comparison():
    infeasible = metric(timing_met=False, wns_ns=-.2)
    # Fewer FFs does not make an infeasible design better than a feasible one.
    assert improvement_kind(metric(timing_met=False, wns_ns=-.1, ff_used=1), metric(), "minimize_luts") is None
    # Recovery and progress are unchanged.
    assert improvement_kind(metric(ff_used=60), infeasible, "minimize_luts") == "timing_recovery"
    assert improvement_kind(metric(timing_met=False, wns_ns=-.2, ff_used=1), infeasible,
                            "minimize_luts", progress=True) is None
    assert improvement_kind(metric(ff_used=18, sim_passed=False), metric(), "minimize_luts") is None


def test_selection_ranks_equal_luts_by_ffs_before_code_length():
    short = Candidate("module a; endmodule", "standard", 5, metric(ff_used=34))
    fewer_ff = Candidate("module bbbbbb; endmodule", "share", 5, metric(ff_used=18))
    assert select([short, fewer_ff], "minimize_luts") is fewer_ff
    fewer_lut = Candidate("module cccccccccc; endmodule", "narrow", 5, metric(lut_used=15, ff_used=60))
    assert select([short, fewer_ff, fewer_lut], "minimize_luts") is fewer_lut
    assert select([Candidate("module a; endmodule", "standard", 5, metric(lut_used=20)),
                   Candidate("module bbbbbb; endmodule", "share", 5, metric(lut_used=12))],
                  "minimize_ffs").metrics["lut_used"] == 12


def test_selection_without_a_secondary_everywhere_falls_back_to_code_length():
    short = Candidate("module a; endmodule", "standard", 5, metric(ff_used=34))
    fewer_ff = Candidate("module bbbbbb; endmodule", "share", 5, metric(ff_used=18))
    bare = Candidate("module cccccccccc; endmodule", "narrow", 5, metric(ff_used=None))
    assert select([fewer_ff, short, bare], "minimize_luts") is short
    # Infeasible candidates keep ranking on setup WNS, below feasible ones.
    late = Candidate("module a; endmodule", "standard", 5, metric(timing_met=False, wns_ns=-.1, ff_used=1))
    assert select([late, short], "minimize_luts") is short


@pytest.mark.parametrize("objective, wording", [
    ("minimize_luts", "strictly lower lut_used, or equal lut_used with strictly lower ff_used,"),
    ("minimize_ffs", "strictly lower ff_used, or equal ff_used with strictly lower lut_used,"),
])
def test_contract_states_the_lexicographic_comparison(tmp_path, objective, wording):
    cfg = configuration(tmp_path)
    cfg.objective = objective
    facts = run_evidence(cfg, VivadoMetrics(), [cfg.design_path], cfg.testbench_path,
                         tmp_path, {"tools": "t"})
    contract = render_fixed_optimize_contract(facts)
    assert wording in contract and "compared lexicographically" in contract
    primary = "lut_used" if objective == "minimize_luts" else "ff_used"
    assert f"Higher {primary} is never an objective improvement." in contract
    assert "(lut_used, ff_used)" in facts["objective_policy"]
    assert "(ff_used, lut_used)" in facts["objective_policy"]
    assert "no tie-break" in facts["objective_policy"]


@pytest.mark.parametrize("objective", ["maximize_freq", "minimize_power"])
def test_contract_for_other_objectives_has_no_tie_break(tmp_path, objective):
    cfg = configuration(tmp_path)
    cfg.objective = objective
    facts = run_evidence(cfg, VivadoMetrics(), [cfg.design_path], cfg.testbench_path,
                         tmp_path, {"tools": "t"})
    assert "compared lexicographically" not in render_fixed_optimize_contract(facts)


def test_evaluator_and_planner_prompts_state_the_tie_break():
    flat = lambda text: " ".join(text.split())
    evaluate, plan = flat(prompts.EVALUATE), flat(prompts.PLAN)
    for text in (evaluate, plan):
        assert "minimize_luts compares (LUTs, FFs) and minimize_ffs compares (FFs, LUTs) lexicographically" in text
    assert "never reject it for an unchanged primary count" in evaluate
    assert "a higher primary count is never an improvement" in evaluate
    assert "a higher primary count never is" in plan


def test_full_loop_promotes_equal_lut_fewer_ff_candidate(tmp_path, monkeypatch):
    cfg = configuration(tmp_path); cfg.max_iterations = 2
    assert cfg.objective == "minimize_luts"
    o = fsm.Orchestrator(cfg, tmp_path / "run")
    install_models(o); install_tools(monkeypatch)
    later = WINNER.replace("y=1", "y=rst")
    monkeypatch.setattr(o.generator, "generate", Mock(side_effect=[WINNER, later]))
    # Iteration 1: crc16 iteration 3 (16 LUT, 34 -> 18 FF). Iteration 2: more LUTs, fewer FFs.
    shape = {0: (16, 34), 1: (16, 18), 2: (17, 10)}
    def metrics(work):
        it = next(int(p[5:]) for p in work.parts if p.startswith("iter_"))
        lut, ff = shape[it]
        return VivadoMetrics(sim_passed=True, lut_used=lut, lut_total=20800, ff_used=ff, ff_total=41600,
                             wns_ns=.445, whs_ns=.1, timing_met=True)
    monkeypatch.setattr(fsm.vivado, "full_metrics", metrics)
    result = o.run()
    designs = o.state.read_designs()
    assert [(d["iteration"], d["is_best"], d.get("improvement_kind")) for d in designs] == [
        (0, True, None), (1, True, "objective"), (2, False, None)]
    facts = json.loads((o.state.run_dir / "iter_001/evaluation_facts.json").read_text())
    assert facts["improvement_kind"] == "objective" and facts["measured_improvement"] is True
    worse = json.loads((o.state.run_dir / "iter_002/evaluation_facts.json").read_text())
    assert worse["improvement_kind"] is None and worse["measured_improvement"] is False
    assert result["best_iteration"] == 1 and result["improvement_kind"] == "objective"
    assert result["timing_closed"] is True
    assert (result["best_metrics"]["lut_used"], result["best_metrics"]["ff_used"]) == (16, 18)
    assert (o.state.run_dir / "m_best.v").read_text() == WINNER
    resumed = fsm.Orchestrator(RunConfig.load(o.state.run_dir / "config.json"), o.state.run_dir)
    install_models(resumed, forbidden=True)
    assert resumed.run() == result
