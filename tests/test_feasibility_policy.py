"""Timing feasibility takes priority without weakening verification or objective gates."""
import json
import pytest
from autortl.objectives import timing_feasible, improvement_kind
from autortl.bestofn import Candidate, select
from autortl.contract_context import run_evidence, render_fixed_optimize_contract
from autortl.config import RunConfig
from autortl.report_parser import VivadoMetrics
from autortl import prompts

OBJECTIVES=("minimize_luts","minimize_ffs","maximize_freq","minimize_power")


def metric(**changes):
    result=dict(sim_passed=True,sim_error="",synth_error="",timing_met=True,
                wns_ns=.3,whs_ns=.1,lut_used=13,ff_used=6,dynamic_power_w=.05)
    result.update(changes)
    return result


@pytest.mark.parametrize("objective",OBJECTIVES)
@pytest.mark.parametrize("more_resources",[False,True])
def test_timing_recovery_wins_even_when_selected_resource_objective_does_not_improve(objective,more_resources):
    old=metric(timing_met=False,wns_ns=-.931)
    new=metric(lut_used=14 if more_resources else 13,ff_used=9 if more_resources else 6,
               dynamic_power_w=.2 if more_resources else .05)
    assert improvement_kind(new,old,objective)=="timing_recovery"
    assert improvement_kind(VivadoMetrics.from_dict(new),VivadoMetrics.from_dict(old),objective)=="timing_recovery"


@pytest.mark.parametrize("objective",OBJECTIVES)
def test_hold_recovery_is_also_a_feasibility_recovery(objective):
    assert improvement_kind(metric(lut_used=20),metric(timing_met=False,whs_ns=-.01),objective)=="timing_recovery"


@pytest.mark.parametrize("objective",OBJECTIVES)
def test_feasible_incumbent_cannot_be_replaced_by_unclosed_cheap_candidate(objective):
    for bad in (metric(lut_used=1,timing_met=False,wns_ns=-.01),metric(lut_used=1,timing_met=False,whs_ns=-.01)):
        assert improvement_kind(bad,metric(),objective) is None


@pytest.mark.parametrize("objective,field,better,worse",[
    ("minimize_luts","lut_used",12,14),("minimize_ffs","ff_used",5,7),
    ("maximize_freq","wns_ns",.4,.2),("minimize_power","dynamic_power_w",.04,.06)])
def test_strict_objective_comparison_when_both_are_feasible(objective,field,better,worse):
    old=metric()
    assert improvement_kind(metric(**{field:better}),old,objective)=="objective"
    assert improvement_kind(metric(),old,objective) is None
    assert improvement_kind(metric(**{field:worse}),old,objective) is None


@pytest.mark.parametrize("field,value",[
    ("timing_met",None),("timing_met",1),("timing_met",False),
    ("wns_ns",None),("wns_ns",float("nan")),("whs_ns",float("inf")),
    ("wns_ns",True),("wns_ns",-999.),("whs_ns",-.01)])
def test_unknown_or_contradictory_candidate_timing_never_passes(field,value):
    candidate=metric(**{field:value})
    assert not timing_feasible(candidate)
    assert improvement_kind(candidate,metric(timing_met=False,wns_ns=-.931),"minimize_luts") is None


@pytest.mark.parametrize("field",["timing_met","wns_ns","whs_ns"])
def test_missing_candidate_timing_is_unknown(field):
    candidate=metric(); del candidate[field]
    assert not timing_feasible(candidate)
    assert improvement_kind(candidate,metric(),"minimize_luts") is None


@pytest.mark.parametrize("old",[
    {},metric(timing_met=False),metric(timing_met=True,wns_ns=-.1),
    metric(timing_met=None),metric(wns_ns=float("nan")),metric(wns_ns=-999.)])
def test_unknown_or_contradictory_incumbent_cannot_establish_recovery(old):
    assert improvement_kind(metric(),old,"minimize_luts") is None


@pytest.mark.parametrize("field,value",[("sim_passed",False),("sim_passed",1),("sim_error","FAIL"),("synth_error","failed")])
def test_unverified_candidate_cannot_win_timing_recovery(field,value):
    assert improvement_kind(metric(**{field:value}),metric(timing_met=False,wns_ns=-1),"minimize_luts") is None


@pytest.mark.parametrize("value",[None,float("nan"),float("inf"),True,-1])
def test_unknown_or_invalid_selected_objective_cannot_be_promoted(value):
    assert improvement_kind(metric(lut_used=value),metric(timing_met=False,wns_ns=-1),"minimize_luts") is None


def test_unknown_objective_is_explicitly_rejected():
    with pytest.raises(ValueError,match="unsupported objective"):
        improvement_kind(metric(),metric(),"imaginary")


@pytest.mark.parametrize("objective",OBJECTIVES)
def test_selection_ranks_feasibility_before_objective(objective):
    cheap=Candidate("cheap","standard",5,metric(timing_met=False,wns_ns=-.931,lut_used=1,ff_used=1,dynamic_power_w=.001))
    closed=Candidate("closed","pipeline",5,metric(lut_used=14,ff_used=9,dynamic_power_w=.2))
    assert select([cheap,closed],objective) is closed
    partial=Candidate("partial","narrow",4,metric(lut_used=0))
    assert select([cheap,partial],objective) is cheap  # completed rung priority is unchanged


def test_selection_handles_missing_or_nonfinite_objective_without_unstable_ranking():
    invalid=Candidate("bad","a",5,metric(lut_used=None))
    valid=Candidate("good","b",5,metric())
    assert select([invalid,valid],"minimize_luts") is valid


@pytest.mark.parametrize("objective",OBJECTIVES)
def test_rendered_contract_and_evaluator_explain_recovery_without_claiming_savings(tmp_path,objective):
    source=tmp_path/"m.v";source.write_text("module m(input clk,output y);assign y=0;endmodule")
    tb=tmp_path/"m_tb.v";tb.write_text("// controlled fixture")
    cfg=RunConfig(mode="optimize",top_module="m",design_path=source,testbench_path=tb,objective=objective)
    facts=run_evidence(cfg,VivadoMetrics.from_dict(metric(timing_met=False,wns_ns=-.931)),[source],tb,tmp_path,{})
    text=render_fixed_optimize_contract(facts)
    assert "timing_recovery" in text and "even when area or power increases" in text
    assert "not resource or power savings" in text
    assert "Once both designs are timing-feasible" in text
    assert "WNS >= 0" in text and "WHS >= 0" in text
    assert "timing_recovery" in facts["objective_policy"]
    assert text==render_fixed_optimize_contract(json.loads(json.dumps(facts)))
    assert "Never reject a valid timing recovery solely for higher area" in prompts.EVALUATE
