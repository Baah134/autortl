"""Deterministic generation/repair gates use the selected module's annotation."""
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from autortl import fsm
from autortl.bestofn import Candidate
from autortl.config import RunConfig
from autortl.report_parser import VivadoMetrics
from autortl.triage import FailureKind
from llm.client import declared_latency
from tests.test_fsm_resume import SOURCE
from tests.test_doctor_fsm import lineage

def annotated(cycles):
    return f"// @latency {cycles}\n" + SOURCE

def helper_first(top_latency, helper_latency):
    return (f"// @latency {helper_latency}\nmodule helper(output z); assign z=0; endmodule\n"
            + annotated(top_latency))

def setup(tmp_path):
    o=fsm.Orchestrator(RunConfig(mode="optimize",top_module="m",max_fix_attempts=0,best_of_n=1),tmp_path/"run")
    tb=tmp_path/"tb.v";tb.write_text("// controlled temporal fixture",encoding="utf-8")
    return o,tb,o._infer_contract(annotated(1),"m")

@pytest.mark.parametrize("top_latency,helper_latency,accepted",[(1,2,True),(2,1,False)])
def test_candidate_latency_ignores_helper(tmp_path,monkeypatch,top_latency,helper_latency,accepted):
    o,tb,contract=setup(tmp_path)
    tool=Mock(return_value=(True,"",FailureKind.DESIGN));monkeypatch.setattr(o,"_tool",tool)
    candidate=Candidate(helper_first(top_latency,helper_latency),"standard")
    o._verify_optimization_candidate(candidate,contract,tb,[],o.state.iter_dir(1),[])
    assert candidate.alive is accepted
    assert tool.call_count==(2 if accepted else 0)
    if not accepted:assert "latency" in candidate.fail_reason

@pytest.mark.parametrize("top_latency,helper_latency,accepted",[(1,2,True),(2,1,False)])
def test_typed_generation_latency_ignores_helper(tmp_path,monkeypatch,top_latency,helper_latency,accepted):
    o,tb,contract=setup(tmp_path)
    source=helper_first(top_latency,helper_latency)
    monkeypatch.setattr(o.generator,"generate",Mock(return_value=source))
    tool=Mock(return_value=(True,"",FailureKind.DESIGN));monkeypatch.setattr(o,"_tool",tool)
    directory=tmp_path/"module";directory.mkdir()
    result=o._generate_verified(contract,"","preserve",tb,directory)
    assert (result is not None) is accepted
    assert tool.call_count==(2 if accepted else 0)

@pytest.mark.parametrize("top_latency,helper_latency,accepted",[(1,2,True),(2,1,False)])
def test_baseline_repair_latency_ignores_helper(tmp_path,monkeypatch,top_latency,helper_latency,accepted):
    o,tb,contract=setup(tmp_path);o.cfg.max_fix_attempts=1
    original=annotated(1);replacement=helper_first(top_latency,helper_latency)
    path=tmp_path/"m.v";path.write_text(original,encoding="utf-8")
    monkeypatch.setattr(o.generator,"fix",Mock(return_value=replacement))
    success=VivadoMetrics(sim_passed=True)
    flow=Mock(return_value=success);monkeypatch.setattr(o,"_full_flow",flow)
    o._last_flow_failure_kind=FailureKind.DESIGN
    result,metric=o._fix_loop(original,VivadoMetrics(sim_passed=False,sim_error="FAIL controlled design"),tb,path,tmp_path,[])
    assert (result==replacement) is accepted
    assert flow.call_count==(1 if accepted else 0)
    assert metric.sim_passed is accepted

@pytest.mark.parametrize("top_latency,helper_latency,accepted",[(1,2,True),(2,1,False)])
def test_doctor_latency_ignores_helper(lineage,monkeypatch,top_latency,helper_latency,accepted):
    o,parent,origin,source,tb,metric=lineage
    contract=o._infer_contract("// @latency 1\n"+source,"m")
    replacement=(f"// @latency {helper_latency}\nmodule helper(output z); assign z=0; endmodule\n"
                 +f"// @latency {top_latency}\n"+source)
    monkeypatch.setattr(o.doctor,"surgery",Mock(return_value=replacement))
    before=VivadoMetrics.from_dict(metric.to_dict());before.wns_ns=-.9;before.timing_met=False
    diagnosis=SimpleNamespace(action="rtl_surgery",instruction="shorten path",detail="controlled",
                              category=SimpleNamespace(value="logic_depth"),wns_ns=-.9)
    result=o._doctor_trial(source,before,contract,tb,[],parent,diagnosis,verification_dir=origin)
    assert (result is not None) is accepted
    assert fsm.vivado.xsim_run.call_count==(1 if accepted else 0)
    if not accepted:assert o._last_doctor_trial["reason"]=="latency_violation"

def test_client_backward_compatible_single_module_and_explicit_selection():
    assert declared_latency(annotated(1))==1
    assert declared_latency(helper_first(2,1),"m")==2
    assert declared_latency(helper_first(2,1)) is None

def test_malformed_candidate_annotation_is_design_rejection_before_tools(tmp_path,monkeypatch):
    o,tb,contract=setup(tmp_path)
    candidate=Candidate("// @latency nope\n"+SOURCE,"standard")
    tool=Mock(side_effect=AssertionError("malformed metadata must fail static checks"))
    monkeypatch.setattr(o,"_tool",tool)
    o._verify_optimization_candidate(candidate,contract,tb,[],o.state.iter_dir(1),[])
    assert candidate.alive is False
    assert "latency" in candidate.fail_reason.lower()
    tool.assert_not_called()

