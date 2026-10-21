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
    o,synthesis=create(tmp_path,monkeypatch);o.cfg.generate_golden=True;o.cfg.max_fix_attempts=1
    expected_hash=hashlib.sha256(o.cfg.testbench_path.read_bytes()).hexdigest()
    monkeypatch.setattr(o.generator,"golden_model",Mock(return_value=COUNTER.replace('"count": 99','"count": 0')))
    candidate="module counter8(input clk,input rst,input enable,output [7:0] count); counter8_core other(.clk(clk),.rst(rst),.enable(!enable),.count(count)); endmodule"
    monkeypatch.setattr(o.generator,"generate",Mock(side_effect=[RTL,candidate]))
    repair=Mock(return_value=candidate);monkeypatch.setattr(o.generator,"fix",repair)
    original_sim=fsm.vivado.xsim_run;checked=[]
    def simulate(files,tb,top,cfg,work,**kwargs):
        if top=="counter8_tb":
            checked.append((work,hashlib.sha256(tb.read_bytes()).hexdigest()))
            if "cand_standard" in work.parts:
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


@pytest.mark.parametrize("kind",[FailureKind.INFRA,FailureKind.UNKNOWN])
def test_qualification_infrastructure_cause_is_retained_in_public_build_summary(tmp_path,monkeypatch,kind):
    import json
    o,synthesis=create(tmp_path,monkeypatch,mutant_kind=kind)
    result=o.run()
    assert result["status"]=="build_blocked" and result["failure_kind"]==kind.value
    assert result["stage"]=="qualification mutant"
    assert result["error"]=="license unavailable"
    assert result["testbench"].endswith("counter8_core_tb.v")
    assert json.loads((o.state.run_dir/"run_summary.json").read_text())==result
    assert o.state.read_designs()==[]
    synthesis.assert_not_called();o.generator.fix.assert_not_called()


def test_exhausted_independent_child_infrastructure_is_typed_before_qualification(tmp_path,monkeypatch):
    from tests.test_golden_reset_protocol import COUNTER
    o,synthesis=create(tmp_path,monkeypatch);o.cfg.generate_golden=True;o.cfg.max_infra_retries=1
    monkeypatch.setattr(o.generator,"golden_model",Mock(return_value=COUNTER.replace('"count": 99','"count": 0')))
    qualification=Mock(side_effect=AssertionError("incomplete source must not qualify"))
    monkeypatch.setattr(o,"_qualify_source",qualification)
    original=fsm.vivado.xsim_run;blocked=[]
    def simulate(files,tb,top,cfg,work,**kwargs):
        if work.name=="independent":
            blocked.append(work)
            return False,"license unavailable",FailureKind.INFRA
        return original(files,tb,top,cfg,work,**kwargs)
    monkeypatch.setattr(fsm.vivado,"xsim_run",simulate)
    result=o.run()
    assert result["status"]=="build_blocked" and result["failure_kind"]=="infra"
    assert result["stage"]=="independent child verification"
    assert result["error"]=="license unavailable" and len(blocked)==2
    assert "independent_" in result["testbench"]
    synthesis.assert_not_called();o.generator.fix.assert_not_called();qualification.assert_not_called()
    assert o.state.read_designs()==[]


def test_fsm_qualification_retains_missed_primary_before_observable_fault(tmp_path,monkeypatch):
    import json
    o=fsm.Orchestrator(RunConfig(mode="build"),tmp_path/"run")
    tb=tmp_path/"m_tb.v";tb.write_text("// controlled independent test")
    source="module m(input [7:0] a,b,output y); assign y=a<b; endmodule"
    calls=[]
    def tool(name,files,tb,top,cfg,work):
        calls.append(work.name)
        if work.name=="stuck_zero":
            (work/"sim_log.txt").write_text("FAIL wrong payload\nTEST FAILED: 1 errors\n")
            return False,"testbench reported failure",FailureKind.DESIGN
        (work/"sim_log.txt").write_text("TEST PASSED\n")
        return True,"",FailureKind.DESIGN
    monkeypatch.setattr(o,"_tool",tool)
    qualified,reason=o._qualify_source(source,tb,"m",tmp_path)
    assert qualified and "missed:" in reason
    assert calls==["control","mutant","stuck_zero"]
    record=json.loads((tmp_path/"tbqual/qualification.json").read_text())
    assert record["qualified"] and record["missed"][0]["label"]=="mutant"
    assert record["attempts"][-1]["assertion_detected"] is True
    assert all(len(row["source_sha256"])==64 for row in record["attempts"])


def test_fsm_portfolio_cannot_try_another_fault_after_infrastructure(tmp_path,monkeypatch):
    import json
    o=fsm.Orchestrator(RunConfig(mode="build"),tmp_path/"run")
    tb=tmp_path/"m_tb.v";tb.write_text("// controlled test")
    source="module m(input [7:0] a,b,output y); assign y=a<b; endmodule"
    calls=[]
    def tool(name,files,tb,top,cfg,work):
        calls.append(work.name)
        return (True,"",FailureKind.DESIGN) if work.name=="control" else (False,"no license",FailureKind.INFRA)
    monkeypatch.setattr(o,"_tool",tool)
    assert not o._qualify_source(source,tb,"m",tmp_path)[0]
    assert calls==["control","mutant"]
    assert o._build_blocker["error"]=="no license"
    assert json.loads((tmp_path/"tbqual/qualification.json").read_text())["status"]=="blocked"


def test_module_evidence_uses_utf8_for_non_ascii_model_comments(tmp_path):
    o=fsm.Orchestrator(RunConfig(mode="build"),tmp_path/"run")
    source="// 中文 Ω\nmodule m(output y); assign y=0; endmodule\n"
    path=o._write_tmp(tmp_path,"m",source)
    # Windows newline conversion is allowed; text encoding must remain UTF-8.
    assert path.read_text(encoding="utf-8")==source


def test_adapted_trusted_tb_preserves_utf8_comments(dual,monkeypatch):
    o,spec,directory,generated,trusted=dual
    text=trusted.read_text(encoding="utf-8")+"\n// 中文 Ω independent authority\n"
    trusted.write_text(text,encoding="utf-8")
    monkeypatch.setattr(o.generator,"generate",Mock(return_value=RTL))
    simulator(monkeypatch,generated)
    assert o._build_module(spec,directory)
    adapted=o._qualify_source.call_args.args[1]
    assert "中文 Ω independent authority" in adapted.read_text(encoding="utf-8")
    assert trusted.read_text(encoding="utf-8")==text



def test_qualification_journal_replay_restores_raw_assertions_and_misses(tmp_path, monkeypatch):
    import json
    from tests.test_fsm_resume import write_mock_tool_receipts
    cfg = RunConfig(mode="build")
    run = tmp_path / "run"
    tb = tmp_path / "m_tb.v"
    tb.write_text("// controlled qualification fixture")
    source = "module m(input [7:0] a,b,output y); assign y=a<b; endmodule"
    calls = []
    def simulate(files, tb, top, config, work, **kwargs):
        calls.append(work.name)
        write_mock_tool_receipts(work, ("xvlog", "xelab", "xsim"))
        detected = work.name == "stuck_zero"
        (work / "sim_log.txt").write_text("FAIL wrong payload\nTEST FAILED: 1 errors\n" if detected else "TEST PASSED\n")
        return not detected, "Testbench failures: FAIL wrong payload" if detected else "", FailureKind.DESIGN
    monkeypatch.setattr(fsm.vivado, "xsim_run", simulate)
    monkeypatch.setattr(fsm.vivado, "vivado_seconds", lambda: 0)
    def orchestrator():
        o = fsm.Orchestrator(cfg, run)
        o._prepare_inputs()
        o._journal_enabled = True
        o._scope = "qualification-replay"
        return o
    first = orchestrator()
    work = run / "module"
    assert first._qualify_source(source, tb, "m", work)[0]
    report = work / "tbqual/qualification.json"
    original = json.loads(report.read_text())
    proof = work / "tbqual/stuck_zero/sim_log.txt"
    miss = work / "tbqual/mutant/sim_log.txt"
    proof.unlink()
    miss.write_text("FAIL forged proof\nTEST FAILED: 1 errors\n")
    assert orchestrator()._qualify_source(source, tb, "m", work)[0]
    assert calls == ["control", "mutant", "stuck_zero"]
    assert proof.read_text() == "FAIL wrong payload\nTEST FAILED: 1 errors\n"
    assert miss.read_text() == "TEST PASSED\n"
    assert json.loads(report.read_text()) == original
    assert original["missed"][0]["label"] == "mutant"


@pytest.mark.parametrize("artifact", ["qualification.json", "mutant/sim_log.txt"])
def test_done_rejects_changed_qualification_proof(tmp_path, monkeypatch, artifact):
    import json
    o, synthesis = create(tmp_path, monkeypatch)
    assert o.run()["status"] == "done"
    target = o.state.run_dir / "modules/counter8_core/tbqual" / artifact
    snapshot = json.loads((o.state.run_dir / "state.json").read_text())
    assert str(target.resolve()) in snapshot["final_artifacts"]
    original_history = o.state.read_designs()
    calls = synthesis.call_count
    target.write_text("tampered qualification evidence")
    resumed = fsm.Orchestrator(RunConfig.load(o.state.run_dir / "config.json"), o.state.run_dir)
    forbidden = Mock(side_effect=AssertionError("DONE must not repeat generation"))
    monkeypatch.setattr(resumed.generator, "generate", forbidden)
    with pytest.raises(ValueError, match="Completed"):
        resumed.run()
    forbidden.assert_not_called()
    assert synthesis.call_count == calls
    assert o.state.read_designs() == original_history
