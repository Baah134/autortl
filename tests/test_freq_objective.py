"""maximize_freq compares logic timing, not pad delay, between feasible designs.

Taxonomy: maximize_freq_ranks_on_pad_delay (follows io_dominated_timing_metric).
Acceptance, feasibility, infeasible ranking and timing_progress stay on the
full I/O-constrained wns_ns/whs_ns; only the objective comparison between two
timing-feasible verified designs uses reg2reg_wns_ns, and only when both
report a finite value (otherwise wns_ns for both, never mixed).
"""
import shutil
from pathlib import Path

import pytest

from autortl.bestofn import Candidate, select
from autortl.contract_context import render_fixed_optimize_contract, run_evidence
from autortl.objectives import improvement_kind, objective_field, timing_feasible
from autortl.report_parser import VivadoMetrics, parse_all
from tests.test_fsm_resume import configuration

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "reg2reg"


def metric(**changes):
    result = dict(sim_passed=True, sim_error="", synth_error="", timing_met=True,
                  wns_ns=.3, whs_ns=.1, lut_used=13, ff_used=6, dynamic_power_w=.05)
    result.update(changes)
    return result


def test_both_reporting_compares_reg2reg_even_when_pad_wns_disagrees():
    best = metric(wns_ns=.3, reg2reg_wns_ns=1.0)
    # Lower pad-limited WNS but better logic timing: an objective improvement.
    assert improvement_kind(metric(wns_ns=.2, reg2reg_wns_ns=2.0), best, "maximize_freq") == "objective"
    # Higher pad-limited WNS but worse logic timing: not an improvement.
    assert improvement_kind(metric(wns_ns=.5, reg2reg_wns_ns=.9), best, "maximize_freq") is None
    assert improvement_kind(metric(wns_ns=.5, reg2reg_wns_ns=1.0), best, "maximize_freq") is None
    assert objective_field("maximize_freq", best, metric(reg2reg_wns_ns=2.0)) == "reg2reg_wns_ns"


@pytest.mark.parametrize("missing", [None, float("nan"), float("inf"), True, "1.0"])
@pytest.mark.parametrize("side", ["new", "best"])
def test_one_side_without_a_finite_reg2reg_falls_back_to_wns_for_both(missing, side):
    values = {"new": 5.0, "best": 1.0}
    values[side] = missing
    new = lambda wns: metric(wns_ns=wns, reg2reg_wns_ns=values["new"])
    best = metric(wns_ns=.3, reg2reg_wns_ns=values["best"])
    assert objective_field("maximize_freq", new(.3), best) == "wns_ns"
    assert improvement_kind(new(.4), best, "maximize_freq") == "objective"
    assert improvement_kind(new(.2), best, "maximize_freq") is None


def test_feasibility_and_recovery_stay_on_full_wns():
    # Great logic timing never makes a pad-failing design feasible.
    failing = metric(timing_met=False, wns_ns=-.1, reg2reg_wns_ns=3.0)
    assert not timing_feasible(failing)
    assert improvement_kind(failing, metric(reg2reg_wns_ns=1.0), "maximize_freq") is None
    # A feasible design recovers an infeasible incumbent whatever its reg2reg slack.
    assert improvement_kind(metric(reg2reg_wns_ns=.1), metric(timing_met=False, wns_ns=-.5, reg2reg_wns_ns=4.0),
                            "maximize_freq") == "timing_recovery"
    # timing_progress compares setup WNS, not reg2reg.
    worse_r2r = metric(timing_met=False, wns_ns=-.2, reg2reg_wns_ns=.1)
    incumbent = metric(timing_met=False, wns_ns=-.5, reg2reg_wns_ns=4.0)
    assert improvement_kind(worse_r2r, incumbent, "maximize_freq", progress=True) == "timing_progress"


def test_contradictory_negative_reg2reg_on_a_feasible_design_never_wins():
    assert improvement_kind(metric(reg2reg_wns_ns=-.1), metric(reg2reg_wns_ns=-.5), "maximize_freq") is None


@pytest.mark.parametrize("objective", ["minimize_luts", "minimize_ffs", "minimize_power"])
def test_other_objectives_ignore_reg2reg(objective):
    assert objective_field(objective, metric(reg2reg_wns_ns=1.0), metric(reg2reg_wns_ns=2.0)) != "reg2reg_wns_ns"
    assert improvement_kind(metric(reg2reg_wns_ns=9.0), metric(reg2reg_wns_ns=1.0), objective) is None


def test_selection_ranks_feasible_candidates_on_reg2reg_when_all_report_it():
    pad = Candidate("module a; endmodule", "standard", 5, metric(wns_ns=.6, reg2reg_wns_ns=1.0))
    logic = Candidate("module bb; endmodule", "pipeline", 5, metric(wns_ns=.2, reg2reg_wns_ns=3.0))
    assert select([pad, logic], "maximize_freq") is logic


def test_selection_uses_wns_for_every_feasible_candidate_when_one_lacks_reg2reg():
    pad = Candidate("module a; endmodule", "standard", 5, metric(wns_ns=.6, reg2reg_wns_ns=1.0))
    logic = Candidate("module bb; endmodule", "pipeline", 5, metric(wns_ns=.2, reg2reg_wns_ns=3.0))
    bare = Candidate("module ccc; endmodule", "infer", 5, metric(wns_ns=.4, reg2reg_wns_ns=None))
    assert select([pad, logic, bare], "maximize_freq") is pad


def test_infeasible_candidates_still_rank_on_setup_wns_and_below_feasible_ones():
    close = Candidate("module a; endmodule", "standard", 5,
                      metric(timing_met=False, wns_ns=-.1, reg2reg_wns_ns=.2))
    far = Candidate("module bb; endmodule", "pipeline", 5,
                    metric(timing_met=False, wns_ns=-.9, reg2reg_wns_ns=4.0))
    assert select([far, close], "maximize_freq") is close
    feasible = Candidate("module ccc; endmodule", "infer", 5, metric(wns_ns=.01, reg2reg_wns_ns=.01))
    assert select([far, close, feasible], "maximize_freq") is feasible


def test_parsed_reg2reg_reaches_the_comparison(tmp_path):
    shutil.copy(FIXTURES / "timing_routed.rpt", tmp_path / "timing_routed.rpt")
    shutil.copy(FIXTURES / "met.rpt", tmp_path / "timing_reg2reg.rpt")
    parsed = parse_all(tmp_path)
    parsed.sim_passed, parsed.sim_error = True, ""  # this fixture has no simulation log
    assert parsed.reg2reg_wns_ns == 1.460 and parsed.wns_ns == 0.126
    # Same pad-limited WNS, better logic slack: wins only through reg2reg.
    best = VivadoMetrics.from_dict({**parsed.to_dict(), "reg2reg_wns_ns": 1.0})
    assert improvement_kind(parsed, best, "maximize_freq") == "objective"
    assert improvement_kind(VivadoMetrics.from_dict(parsed.to_dict()), best, "maximize_freq") == "objective"
    candidate = Candidate("module a; endmodule", "standard", 5, parsed.to_dict())
    other = Candidate("module bb; endmodule", "pipeline", 5, best.to_dict())
    assert select([other, candidate], "maximize_freq") is candidate


def test_contract_states_the_maximize_freq_comparison(tmp_path):
    cfg = configuration(tmp_path)
    cfg.objective = "maximize_freq"
    facts = run_evidence(cfg, VivadoMetrics(), [cfg.design_path], cfg.testbench_path,
                         tmp_path, {"tools": "t"})
    contract = render_fixed_optimize_contract(facts)
    assert "reg2reg_wns_ns" in contract and "otherwise wns_ns for both, never mixed" in contract
    assert "reg2reg_wns_ns" in facts["objective_policy"]
    assert "feasibility stays on full WNS and WHS" in facts["objective_policy"]
    assert "WNS >= 0" in contract and "WHS >= 0" in contract
