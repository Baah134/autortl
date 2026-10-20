"""Generated payload oracles and trusted temporal checks must both gate RTL."""
import hashlib
from unittest.mock import Mock
import pytest
from autortl import fsm
from autortl.config import RunConfig
from autortl.spec import DesignSpec
from autortl.triage import FailureKind
from tests.test_fsm_build import ROOT, RTL, create


@pytest.fixture
def dual(tmp_path,monkeypatch):
    trusted=tmp_path/"trusted.v"
    trusted.write_text("// INDEPENDENT CAPACITY AUTHORITY\nmodule counter8_tb; counter8 dut(); endmodule")
    cfg=RunConfig(mode="build",testbench_path=trusted,generate_golden=True,best_of_n=1,max_fix_attempts=1)
    o=fsm.Orchestrator(cfg,tmp_path/"run");o._build_single=True;o._build_top="counter8";o._journal_enabled=True
    spec=DesignSpec.load(ROOT/"curriculum/tier1/counter8_build/design_spec.json").modules[0]
    directory=tmp_path/"module";directory.mkdir()
    generated=directory/"generated_tb.v";generated.write_text("// GENERATED PAYLOAD TB")
    monkeypatch.setattr(o.generator,"golden_model",Mock(return_value="# controlled oracle"))
    monkeypatch.setattr(fsm,"GoldenModel",Mock())
    monkeypatch.setattr(fsm,"qualify_against_examples",Mock(return_value=[]))
    monkeypatch.setattr(fsm,"generate_tb",Mock(return_value=generated))
    monkeypatch.setattr(fsm.vivado,"xvlog_check",Mock(return_value=(True,"",FailureKind.DESIGN)))
    monkeypatch.setattr(o,"_qualify_source",Mock(return_value=(True,"controlled assertion evidence")))
    return o,spec,directory,generated,trusted


def simulator(monkeypatch,generated,*,bad_only=False,infra=False):
    seen=[]
    def simulate(files,tb,top,cfg,work,**kwargs):
        independent=Path(tb)!=generated
        seen.append(("independent" if independent else "generated",Path(work)))
        if independent and (infra or (bad_only and "count+2" in Path(files[0]).read_text())):
            return False,"license unavailable" if infra else "Testbench failures: FAIL independent capacity",FailureKind.INFRA if infra else FailureKind.DESIGN
        return True,"",FailureKind.DESIGN
    from pathlib import Path
    monkeypatch.setattr(fsm.vivado,"xsim_run",simulate)
    return seen


def test_child_repair_receives_independent_failure_and_reruns_both_tbs(dual,monkeypatch):
    o,spec,directory,generated,trusted=dual
    original=trusted.read_bytes()
    monkeypatch.setattr(o.generator,"generate",Mock(return_value=RTL.replace("count+1", "count+2")))
    fix=Mock(return_value=RTL);monkeypatch.setattr(o.generator,"fix",fix)
    seen=simulator(monkeypatch,generated,bad_only=True)
    result=o._build_module(spec,directory)
    assert result and "count+1" in result
    assert [kind for kind,_ in seen]==["generated","independent","generated","independent"]
    assert all(work.name=="independent" for kind,work in seen if kind=="independent")
    assert "FAIL independent capacity" in fix.call_args.args[2]
    assert "INDEPENDENT CAPACITY AUTHORITY" in fix.call_args.args[3]
    assert trusted.read_bytes()==original
    assert o._qualify_source.call_count==2
    assert o.state.read_designs()==[]


def test_independent_infrastructure_failure_never_mutates_or_qualifies_rtl(dual,monkeypatch):
    o,spec,directory,generated,_=dual
    monkeypatch.setattr(o.generator,"generate",Mock(return_value=RTL))
    fix=Mock();monkeypatch.setattr(o.generator,"fix",fix)
    seen=simulator(monkeypatch,generated,infra=True)
    assert o._build_module(spec,directory) is None
    assert [kind for kind,_ in seen]==["generated"] + ["independent"] * (o.cfg.max_infra_retries + 1)
    fix.assert_not_called();o._qualify_source.assert_not_called()
    assert o.state.read_designs()==[]


def test_supplied_independent_tb_must_also_qualify(dual,monkeypatch):
    o,spec,directory,generated,_=dual
    monkeypatch.setattr(o.generator,"generate",Mock(return_value=RTL))
    simulator(monkeypatch,generated)
    o._qualify_source.side_effect=[(True,"generated qualified"),(False,"independent missed fault")]
    assert o._build_module(spec,directory) is None
    assert o._qualify_source.call_count==2


@pytest.mark.parametrize("flag",[False,True])
def test_without_trusted_tb_generated_path_still_operates(dual,monkeypatch,flag):
    o,spec,directory,generated,_=dual;o.cfg.testbench_path=None;o.cfg.generate_golden=flag
    monkeypatch.setattr(o.generator,"generate",Mock(return_value=RTL))
    seen=simulator(monkeypatch,generated)
    assert o._build_module(spec,directory)
    assert [kind for kind,_ in seen]==["generated"]
    assert o._qualify_source.call_count==1


def test_independent_original_top_tb_blocks_optimization_candidate_before_synthesis(tmp_path,monkeypatch):
    from tests.test_golden_reset_protocol import COUNTER
    o,synthesis=create(tmp_path,monkeypatch);o.cfg.generate_golden=True;o.cfg.max_fix_attempts=0
    expected_hash=hashlib.sha256(o.cfg.testbench_path.read_bytes()).hexdigest()
    monkeypatch.setattr(o.generator,"golden_model",Mock(return_value=COUNTER.replace('"count": 99','"count": 0')))
    candidate="module counter8(input clk,input rst,input enable,output [7:0] count); counter8_core other(.clk(clk),.rst(rst),.enable(!enable),.count(count)); endmodule"
    monkeypatch.setattr(o.generator,"generate",Mock(side_effect=[RTL,candidate]))
    repair=Mock(return_value=candidate);monkeypatch.setattr(o.generator,"fix",repair)
    original_sim=fsm.vivado.xsim_run;checked=[]
    def simulate(files,tb,top,cfg,work,**kwargs):
        if top=="counter8_tb":
            checked.append((work,hashlib.sha256(tb.read_bytes()).hexdigest()))
            if work.name=="cand_standard":
                return False,"Testbench failures: FAIL inverted enable",FailureKind.DESIGN
        return original_sim(files,tb,top,cfg,work,**kwargs)
    monkeypatch.setattr(fsm.vivado,"xsim_run",simulate)
    result=o.run()
    assert result["status"]=="done" and result["best_iteration"]==0
    assert synthesis.call_count==1
    assert any(work.name=="cand_standard" for work,_ in checked)
    assert all(digest==expected_hash for _,digest in checked)
    repair.assert_called_once()
    assert "counter8" in repair.call_args.args[3]
    o.evaluator.evaluate.assert_not_called()
