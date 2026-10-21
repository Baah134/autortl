"""Controlled trial evidence and exact no-op suppression; no vendor processes."""
import hashlib
import json
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from autortl import fsm
from autortl.config import RunConfig
from autortl.report_parser import VivadoMetrics
from autortl.roles import Evaluation
from tests.test_doctor_fsm import lineage
from tests.test_fsm_resume import configuration, install_models, install_tools, WINNER, write_mock_tool_receipts


def surgery():
    return SimpleNamespace(action="rtl_surgery", instruction="shorten the existing path",
                           detail="retained path", wns_ns=-.9,
                           category=SimpleNamespace(value="logic_depth"))


def default_script(o, origin, extra=()):
    return fsm.vivado.SYNTH_TCL.format(
        promotions=fsm.vivado.promotion_tcl(o.taxonomy.promotions()),
        part=o.cfg.target_part,
        sources=" ".join(f'"{fsm.vivado._tcl_path(p)}"' for p in [origin / "m.v", *extra]),
        workdir=fsm.vivado._tcl_path(origin), period=f"{o.cfg.target_period_ns:.3f}",
        top=o.cfg.top_module, extra_synth="", phys_opt="")


def test_exact_noop_with_proven_flow_skips_all_tools_and_has_no_trial_metrics(lineage, monkeypatch):
    o,parent,origin,source,tb,metric = lineage
    monkeypatch.setattr(o.doctor, "surgery", Mock(return_value=source))
    script=origin/"synth.tcl"; script.write_text(default_script(o,origin),encoding="utf-8")
    write_mock_tool_receipts(origin,("vivado",))
    assert o._doctor_trial(source,metric,o._infer_contract(source,"m"),tb,[],parent,
                           surgery(),verification_dir=origin) is None
    record=o._last_doctor_trial
    assert record["status"]=="NOT_ADOPTED" and record["reason"]=="no_source_change"
    assert record["tools_ran"] is False and "measured_metrics" not in record
    assert record["input_source"]["sha256"]==hashlib.sha256((origin/"m.v").read_bytes()).hexdigest()
    assert record["input_source"]["path"]==str((origin/"m.v").resolve())
    assert record["input_source"]["truncated"] is False
    assert "assign y=0" in fsm._doctor_advice(record)
    assert record["prior_flow_script"]["sha256"]==hashlib.sha256(script.read_bytes()).hexdigest()
    assert not (parent/"doctor_rtl_surgery_trial").exists()
    fsm.vivado.xsim_run.assert_not_called(); fsm.vivado.run_synthesis.assert_not_called()


@pytest.mark.parametrize("flow",["missing","physical_options","unknown_script","changed_part","changed_dependencies",
                                 "unexecuted_script","changed_promotions","changed_source_bytes"])
def test_identical_source_without_identical_flow_proof_still_runs(lineage,monkeypatch,flow):
    o,parent,origin,source,tb,metric=lineage
    monkeypatch.setattr(o.doctor,"surgery",Mock(return_value=source))
    text=default_script(o,origin)
    if flow!="unexecuted_script":write_mock_tool_receipts(origin,("vivado",))
    if flow=="physical_options":text=text.replace("\nroute_design", "\nphys_opt_design\nroute_design")
    if flow=="unknown_script":text="unknown flow\n"
    if flow!="missing":(origin/"synth.tcl").write_text(text,encoding="utf-8")
    if flow=="changed_part":o.cfg.target_part="xc7a100tcsg324-1"
    if flow=="changed_promotions":monkeypatch.setattr(o.taxonomy,"promotions",lambda:{"Synth 1-1":"ERROR"})
    if flow=="changed_source_bytes":(origin/"m.v").write_text("// changed source\n"+source)
    extra=[]
    if flow=="changed_dependencies":
        companion=origin/"other.v"; companion.write_text("module other; endmodule")
        extra=[companion]
    o._doctor_trial(source,metric,o._infer_contract(source,"m"),tb,extra,parent,
                    surgery(),verification_dir=origin)
    fsm.vivado.xsim_run.assert_called_once(); fsm.vivado.run_synthesis.assert_called_once()
    assert o._last_doctor_trial["tools_ran"] is True


def test_changed_surgery_is_not_noop_and_retains_measured_rejected_trial(lineage,monkeypatch):
    o,parent,origin,source,tb,metric=lineage
    changed=source.replace("y=0","y=1")
    monkeypatch.setattr(o.doctor,"surgery",Mock(return_value=changed))
    (origin/"synth.tcl").write_text(default_script(o,origin),encoding="utf-8")
    write_mock_tool_receipts(origin,("vivado",))
    trial=VivadoMetrics.from_dict(metric.to_dict()); trial.wns_ns=-.525; trial.timing_met=False
    fsm.vivado.full_metrics.return_value=trial
    report_text="controlled raw timing report"
    def synth(*args,**kwargs):
        (args[3]/"timing_routed.rpt").write_text(report_text)
        return True,"",fsm.FailureKind.DESIGN
    fsm.vivado.run_synthesis.side_effect=synth
    assert o._doctor_trial(source,metric,o._infer_contract(source,"m"),tb,[],parent,
                           surgery(),verification_dir=origin) is None
    record=o._last_doctor_trial
    assert record["reason"]=="timing_not_closed" and record["status"]=="NOT_ADOPTED"
    assert record["measured_metrics"]["wns_ns"]==-.525 and metric.wns_ns==1
    assert record["trial_source"]["sha256"]==hashlib.sha256((parent/"doctor_rtl_surgery_trial/m.v").read_bytes()).hexdigest()
    assert record["reports"][0]["sha256"]==hashlib.sha256(report_text.encode()).hexdigest()


def test_intentional_tool_knobs_with_same_source_still_run(lineage):
    o,parent,origin,source,tb,metric=lineage
    (origin/"synth.tcl").write_text(default_script(o,origin),encoding="utf-8")
    o._doctor_trial(source,metric,o._infer_contract(source,"m"),tb,[],parent,
                    SimpleNamespace(action="tool_knobs"),verification_dir=origin)
    fsm.vivado.run_synthesis.assert_called_once()
    assert fsm.vivado.run_synthesis.call_args.kwargs["phys_opt"] is True
    fsm.vivado.xsim_run.assert_not_called()
    assert o._last_doctor_trial["tools_ran"] is True


def test_noop_feedback_replays_without_another_model_or_tool_call(lineage,monkeypatch):
    o,parent,origin,source,tb,metric=lineage
    o._journal_enabled=True
    (origin/"synth.tcl").write_text(default_script(o,origin),encoding="utf-8")
    write_mock_tool_receipts(origin,("vivado",))
    model=Mock(return_value=source); monkeypatch.setattr(o.doctor,"surgery",model)
    o._doctor_trial(source,metric,o._infer_contract(source,"m"),tb,[],parent,surgery(),verification_dir=origin)
    expected=dict(o._last_doctor_trial)
    resumed=fsm.Orchestrator(o.cfg,o.state.run_dir); resumed._journal_enabled=True
    forbidden=Mock(side_effect=AssertionError("completed model must replay"))
    monkeypatch.setattr(resumed.doctor,"surgery",forbidden)
    resumed._doctor_trial(source,metric,resumed._infer_contract(source,"m"),tb,[],parent,surgery(),verification_dir=origin)
    assert resumed._last_doctor_trial==expected
    forbidden.assert_not_called(); model.assert_called_once()
    fsm.vivado.xsim_run.assert_not_called(); fsm.vivado.run_synthesis.assert_not_called()


@pytest.mark.parametrize("change",[None,"before_tamper","before_delete","after_tamper","after_delete"])
def test_rejected_trial_reaches_next_planner_without_replacing_candidate_metrics(tmp_path,monkeypatch,change):
    cfg=configuration(tmp_path); cfg.max_iterations=2
    o=fsm.Orchestrator(cfg,tmp_path/"run")
    install_models(o); install_tools(monkeypatch)
    report=o.state.run_dir/"iter_001/doctor_rtl_surgery_trial/timing_routed.rpt"
    synth=fsm.vivado.run_synthesis
    def synth_with_report(*args,**kwargs):
        result=synth(*args,**kwargs)
        (args[3]/"timing_routed.rpt").write_text("controlled timing report",encoding="utf-8")
        return result
    monkeypatch.setattr(fsm.vivado,"run_synthesis",synth_with_report)
    generated=0
    def generate(*args,**kwargs):
        nonlocal generated
        generated+=1
        if generated==2 and change and change.startswith("before_"):
            if change.endswith("delete"):report.unlink()
            else:report.write_text("modified trial report",encoding="utf-8")
        return WINNER
    monkeypatch.setattr(o.generator,"generate",Mock(side_effect=generate))
    monkeypatch.setattr(o.doctor,"surgery",Mock(return_value="// changed trial\n"+WINNER))
    def metrics(work):
        slack=-.931 if "iter_000" in work.parts else (-.525 if work.name=="doctor_rtl_surgery_trial" else -.905)
        return VivadoMetrics(sim_passed=True,lut_used=13,lut_total=100,ff_used=6,ff_total=200,
                             wns_ns=slack,whs_ns=.091,timing_met=False)
    monkeypatch.setattr(fsm.vivado,"full_metrics",metrics)
    monkeypatch.setattr(fsm,"diagnose",Mock(side_effect=[surgery(),SimpleNamespace(
        action="none",wns_ns=-.905,category=SimpleNamespace(value="unknown"))]))
    monkeypatch.setattr(fsm,"advisor_digest",lambda *args:"ordinary advice "*400)
    monkeypatch.setattr(o.evaluator,"evaluate",Mock(return_value=Evaluation("unclosed","REJECT",0,1)))
    result=o.run()
    facts=json.loads((o.state.run_dir/"iter_001/evaluation_facts.json").read_text(encoding="utf-8"))
    assert facts["candidate_metrics"]["wns_ns"]==-.905
    assert facts["previous_best_metrics"]["wns_ns"]==-.931
    assert facts["doctor_trial"]["status"]=="NOT_ADOPTED"
    assert facts["doctor_trial"]["measured_metrics"]["wns_ns"]==-.525
    advice=o.planner.plan.call_args_list[1].kwargs["advisor"]
    assert advice.startswith("Doctor trial evidence")
    assert "NOT_ADOPTED" in advice[:3000] and "-0.525" in advice[:3000]
    assert "// changed trial" in advice[:3000] and "assign y=1" in advice[:3000]
    assert result["best_iteration"]==0
    if change and change.startswith("before_"):
        assert result["status"]=="infra_blocked" and "Doctor trial evidence" in result["error"]
        assert not (o.state.run_dir/"m_best.v").exists()
    else:
        assert result["best_metrics"]["wns_ns"]==-.931
    second=json.loads((o.state.run_dir/"iter_002/evaluation_facts.json").read_text(encoding="utf-8"))
    assert "doctor_trial" not in second  # Never attach stale prior-trial evidence to a new candidate.
    if change and change.startswith("after_"):
        assert str(report.resolve()) in o.state.load_fsm()["final_artifacts"]
        if change.endswith("delete"):report.unlink()
        else:report.write_text("modified trial report",encoding="utf-8")
        resumed=fsm.Orchestrator(RunConfig.load(o.state.run_dir/"config.json"),o.state.run_dir)
        install_models(resumed,forbidden=True)
        with pytest.raises(ValueError,match="Completed report evidence"):
            resumed.run()


def test_advice_is_bounded_and_labels_truncation():
    text=fsm._doctor_advice({"status":"NOT_ADOPTED","reason":"timing_not_closed",
                            "reports":[{"path":"x"*9000}]})
    assert len(text)<3000 and "Preview truncated" in text and "NOT_ADOPTED" in text


@pytest.mark.parametrize("when",["before","after"])
@pytest.mark.parametrize("change",["tamper","delete"])
def test_resolved_build_spec_identity_is_not_reblessed_or_lost(tmp_path,monkeypatch,when,change):
    from tests.test_fsm_build import create, RTL
    o,_=create(tmp_path,monkeypatch)
    def modify():
        if change=="delete":o.state.spec_path.unlink()
        else:o.state.spec_path.write_bytes(o.state.spec_path.read_bytes()+b"\n ")
    calls=0
    def generate(*args,**kwargs):
        nonlocal calls
        calls+=1
        if calls==2 and when=="before":modify()
        return RTL
    monkeypatch.setattr(o.generator,"generate",Mock(side_effect=generate))
    result=o.run()
    if when=="before":
        assert result["status"]=="infra_blocked" and "build specification evidence" in result["error"]
        assert not (o.state.run_dir/"counter8_best.v").exists()
    else:
        assert result["status"]=="done"
        assert str(o.state.spec_path.resolve()) in o.state.load_fsm()["final_artifacts"]
        modify()
        resumed=fsm.Orchestrator(RunConfig.load(o.state.run_dir/"config.json"),o.state.run_dir)
        with pytest.raises(ValueError,match="Completed report evidence"):
            resumed.run()
