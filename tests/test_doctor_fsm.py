"""Physical-only Doctor changes reuse identified verification, never imaginary reruns."""
import hashlib
import json
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from autortl import fsm
from autortl.config import RunConfig
from autortl.report_parser import VivadoMetrics
from autortl.triage import FailureKind


@pytest.fixture
def lineage(tmp_path, monkeypatch):
    o = fsm.Orchestrator(RunConfig(mode="optimize", top_module="m"), tmp_path / "run")
    parent = o.state.iter_dir(1)
    origin = parent / "cand_standard"
    origin.mkdir()
    source = "module m(output y); assign y=0; endmodule"
    (origin / "m.v").write_text(source)
    (origin / "sim_log.txt").write_text("TEST PASSED")
    from tests.test_fsm_resume import write_mock_tool_receipts
    write_mock_tool_receipts(origin, ("xvlog", "xelab", "xsim"))
    tb = tmp_path / "tb.v"; tb.write_text("// independent testbench fixture")
    metric = VivadoMetrics(sim_passed=True, lut_used=10, lut_total=100, ff_used=5, ff_total=200,
                           wns_ns=1, whs_ns=0.1, timing_met=True)
    monkeypatch.setattr(fsm.vivado,"run_synthesis",Mock(return_value=(True,"",FailureKind.DESIGN)))
    monkeypatch.setattr(fsm.vivado,"full_metrics",Mock(return_value=metric))
    monkeypatch.setattr(fsm.vivado,"xsim_run",Mock(return_value=(True,"",FailureKind.DESIGN)))
    monkeypatch.setattr(fsm.vivado,"vivado_seconds",lambda:0)
    (origin / "verification_inputs.log").write_text(json.dumps(fsm._verification_inputs([origin / "m.v"], tb)))
    actual_tool=o._tool
    def mocked_tool_with_receipts(name,*args,**kwargs):
        result=actual_tool(name,*args,**kwargs)
        mapping={"xvlog_check":(2,("xvlog",)),"xsim_run":(4,("xvlog","xelab","xsim")),"run_synthesis":(3,("vivado",))}
        if name in mapping and result[0]:
            index,tools=mapping[name]; write_mock_tool_receipts(args[index],tools)
        return result
    monkeypatch.setattr(o,"_tool",mocked_tool_with_receipts)
    return o, parent, origin, source, tb, metric


def test_tool_only_doctor_retains_source_bound_prior_verification_without_resimulation(lineage):
    o,parent,origin,source,tb,metric = lineage
    before = VivadoMetrics.from_dict(metric.to_dict()); before.lut_used=20; before.timing_met=False; before.wns_ns=-0.1
    result = o._doctor_trial(source,before,SimpleNamespace(latency=0),tb,[],parent,
                            SimpleNamespace(action="tool_knobs"), verification_dir=origin)
    assert result
    manifest = json.loads((result[2] / "verification_provenance.json").read_text())
    assert manifest["mode"] == "source_identical_prior_verification"
    assert manifest["source_sha256"] == hashlib.sha256((result[2]/"m.v").read_bytes()).hexdigest()
    paths = {row["path"] for row in manifest["evidence"]}
    assert str((origin/"tool_exit_records.log").resolve()) in paths
    assert str((origin/"sim_log.txt").resolve()) in paths
    assert str(tb.resolve()) in paths
    assert "not rerun" in manifest["statement"]
    fsm.vivado.xsim_run.assert_not_called()


def test_tool_only_doctor_rejects_mismatched_prior_source(lineage):
    o,parent,origin,source,tb,metric = lineage
    (origin/"m.v").write_text("module wrong; endmodule")
    with pytest.raises(ValueError,match="identical prior source"):
        o._doctor_trial(source,metric,SimpleNamespace(latency=0),tb,[],parent,
                        SimpleNamespace(action="tool_knobs"), verification_dir=origin)
    fsm.vivado.run_synthesis.assert_not_called()


@pytest.mark.parametrize("known,accepted",[(False,True),(True,False)])
def test_doctor_unknown_annotation_is_not_invented_zero_cycle_contract(lineage,monkeypatch,known,accepted):
    o,parent,origin,source,tb,metric = lineage
    monkeypatch.setattr(o.doctor,"surgery",Mock(return_value="// @latency 2\n"+source))
    monkeypatch.setattr(fsm,"static_check",Mock(return_value=SimpleNamespace(passed=True)))
    before = VivadoMetrics.from_dict(metric.to_dict()); before.lut_used=20
    result = o._doctor_trial(source,before,SimpleNamespace(latency=0,latency_known=known),tb,[],parent,
                            SimpleNamespace(action="rtl_surgery",instruction="repair",detail="path"))
    assert bool(result) is accepted
    assert fsm.vivado.xsim_run.call_count == (1 if accepted else 0)


@pytest.mark.parametrize("change",["edit","delete"])
def test_loop_exposes_prior_receipts_and_done_rejects_their_tampering(lineage,monkeypatch,change):
    from autortl.roles import Evaluation
    o,parent,origin,source,tb,metric = lineage
    o.cfg.design_path=origin/"m.v"; o.cfg.testbench_path=tb
    o.cfg.max_iterations=o.cfg.best_of_n=1
    from tests.test_fsm_resume import write_mock_tool_receipts
    write_mock_tool_receipts(o.state.iter_dir(0))
    baseline=VivadoMetrics.from_dict(metric.to_dict()); baseline.lut_used=20
    candidate=VivadoMetrics.from_dict(metric.to_dict()); candidate.timing_met=False; candidate.wns_ns=-1
    repaired=VivadoMetrics.from_dict(metric.to_dict()); repaired.lut_used=8
    monkeypatch.setattr(o,"_full_flow",Mock(return_value=baseline))
    monkeypatch.setattr(o.planner,"plan",Mock(return_value="plan"))
    monkeypatch.setattr(o.generator,"generate",Mock(return_value=source))
    monkeypatch.setattr(o.evaluator,"evaluate",Mock(return_value=Evaluation("accepted","ACCEPT",1,0)))
    monkeypatch.setattr(fsm.vivado,"xvlog_check",Mock(return_value=(True,"",FailureKind.DESIGN)))
    fsm.vivado.full_metrics.side_effect=[candidate,repaired]
    monkeypatch.setattr(fsm,"diagnose",Mock(return_value=SimpleNamespace(action="tool_knobs",
                        wns_ns=-1,category=SimpleNamespace(value="logic"))))
    result=o.run()
    facts=json.loads((parent/"evaluation_facts.json").read_text())
    assert facts["verification_reuse"]["mode"]=="source_identical_prior_verification"
    assert fsm.vivado.xsim_run.call_count==1  # candidate only; physical Doctor reuses this verification
    receipt=origin/"tool_exit_records.log"
    assert str(receipt.resolve()) in o.state.load_fsm()["final_artifacts"]
    if change=="delete": receipt.unlink()
    else: receipt.write_text("changed receipt")
    with pytest.raises(ValueError,match="evidence"):
        fsm.Orchestrator(RunConfig.load(o.state.run_dir/"config.json"),o.state.run_dir).run()


@pytest.mark.parametrize("changed",["testbench","extra","missing_manifest"])
def test_physical_doctor_refuses_inputs_changed_since_actual_simulation(lineage,changed):
    o,parent,origin,source,tb,metric=lineage
    extra=origin/"companion.v"; extra.write_text("module companion; endmodule")
    manifest=origin/"verification_inputs.log"
    manifest.write_text(json.dumps(fsm._verification_inputs([origin/"m.v",extra],tb)))
    if changed=="testbench": tb.write_text("changed testbench")
    elif changed=="extra": extra.write_text("module changed; endmodule")
    else: manifest.unlink()
    with pytest.raises(fsm.VerificationEvidenceError,match="manifest|changed"):
        o._doctor_trial(source,metric,SimpleNamespace(latency=0),tb,[extra],parent,
                        SimpleNamespace(action="tool_knobs"),verification_dir=origin)
    fsm.vivado.run_synthesis.assert_not_called()



def test_non_ascii_doctor_source_reuse_preserves_utf8_bytes(lineage):
    o,parent,origin,source,tb,metric = lineage
    source = "// café Ω 中文\n" + source
    (origin / "m.v").write_text(source, encoding="utf-8")
    (origin / "verification_inputs.log").write_text(json.dumps(fsm._verification_inputs([origin / "m.v"], tb)), encoding="utf-8")
    before = VivadoMetrics.from_dict(metric.to_dict()); before.lut_used = 20
    result = o._doctor_trial(source,before,SimpleNamespace(latency=0),tb,[],parent,
                            SimpleNamespace(action="tool_knobs"),verification_dir=origin)
    assert result and (result[2]/"m.v").read_bytes() == (origin/"m.v").read_bytes()
    fsm.vivado.xsim_run.assert_not_called()
