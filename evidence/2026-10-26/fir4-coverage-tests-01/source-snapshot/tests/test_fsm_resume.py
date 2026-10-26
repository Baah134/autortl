"""Fault injection through the real journal, state and budget implementations."""
import json
from pathlib import Path
from unittest.mock import Mock
import pytest
from autortl import fsm
from autortl.config import RunConfig
from autortl.report_parser import VivadoMetrics
from autortl.roles import Evaluation
from autortl.triage import FailureKind

SOURCE = "module m(input clk,input rst,output y); assign y=0; endmodule"
WINNER = SOURCE.replace("y=0", "y=1")


def configuration(tmp_path):
    source, tb = tmp_path / "seed.v", tmp_path / "m_tb.v"
    source.write_text(SOURCE)
    tb.write_text("// controlled simulator fixture")
    return RunConfig(mode="optimize", top_module="m", design_path=source,
                     testbench_path=tb, max_iterations=1, best_of_n=1)


def write_mock_tool_receipts(work, tools=("xvlog", "xelab", "xsim", "vivado")):
    """Synthetic unit-test process records, never evidence of actual tool execution."""
    import hashlib
    work = Path(work); work.mkdir(parents=True, exist_ok=True)
    records = work / "tool_exit_records.log"
    with records.open("a", encoding="utf-8") as stream:
        for tool in tools:
            log = work / f"mock_{tool}.log"
            log.write_text("controlled unit-test output " + tool, encoding="utf-8")
            stream.write(json.dumps({"schema_version":1,"tool":tool,"executable":"unit-test-mock/"+tool,
                "cwd":str(work.resolve()),"pid":123,"status":"exited","returncode":0,
                "driver_returncode":0,"elapsed_seconds":0,"output_log_path":str(log.resolve()),
                "output_log_sha256":hashlib.sha256(log.read_bytes()).hexdigest()}) + "\n")


def install_tools(monkeypatch, *, fail_compile=False, fail_sim=False):
    calls = []
    def compile(files, cfg, work, **kwargs):
        calls.append(("compile", str(work)))
        if fail_compile: raise KeyboardInterrupt("in-flight compile interruption")
        write_mock_tool_receipts(work, ("xvlog",))
        return True, "", FailureKind.DESIGN
    def simulate(files, tb, top, cfg, work, **kwargs):
        calls.append(("simulation", str(work)))
        if fail_sim and "cand_" in str(work):
            return False, "license unavailable", FailureKind.INFRA
        (work / "sim_log.txt").write_text("TEST PASSED\n")
        write_mock_tool_receipts(work, ("xvlog", "xelab", "xsim"))
        return True, "", FailureKind.DESIGN
    def synth(files, top, cfg, work, **kwargs):
        calls.append(("synthesis", str(work)))
        (work / "utilization.rpt").write_text("controlled report")
        write_mock_tool_receipts(work, ("vivado",))
        return True, "", FailureKind.DESIGN
    def metrics(work):
        return VivadoMetrics(sim_passed=True, lut_used=20 if "iter_000" in str(work) else 10,
                             lut_total=20800, ff_used=8, ff_total=41600,
                             wns_ns=1, whs_ns=0.1, timing_met=True)
    monkeypatch.setattr(fsm.vivado, "xvlog_check", compile)
    monkeypatch.setattr(fsm.vivado, "xsim_run", simulate)
    monkeypatch.setattr(fsm.vivado, "run_synthesis", synth)
    monkeypatch.setattr(fsm.vivado, "full_metrics", metrics)
    monkeypatch.setattr(fsm.vivado, "vivado_seconds", lambda: 0)
    return calls


def install_models(o, forbidden=False):
    results = {("planner", "propose_contract"): "contract",
               ("planner", "plan"): "## Instruction for generator\nImprove area",
               ("evaluator", "review_contract"): "ACCEPT",
               ("generator", "generate"): WINNER,
               ("evaluator", "evaluate"): Evaluation("ACCEPT", "ACCEPT", 1, 0)}
    mocks = {}
    for (role, name), value in results.items():
        def call(*args, _value=value, **kwargs):
            if forbidden: raise AssertionError("Completed model stage was called again")
            o.budget.charge_llm()
            return _value
        model = Mock(side_effect=call)
        setattr(getattr(o, role), name, model)
        mocks[(role, name)] = model
    return mocks


def test_resume_preserves_completed_models_tools_winner_and_budget(tmp_path, monkeypatch):
    cfg = configuration(tmp_path)
    run = tmp_path / "run"
    o = fsm.Orchestrator(cfg, run)
    install_models(o)
    install_tools(monkeypatch, fail_compile=True)
    with pytest.raises(KeyboardInterrupt): o.run()
    saved_calls = o.budget.llm_calls
    assert saved_calls == 2
    # External files may change; the saved, verified snapshot is authoritative.
    (tmp_path / "seed.v").write_text("changed external source")
    resumed = fsm.Orchestrator(RunConfig.load(run / "config.json"), run)
    models = install_models(resumed)
    calls = install_tools(monkeypatch)
    summary = resumed.run()
    assert summary["best_iteration"] == 1
    assert (run / "m_best.v").read_text() == WINNER
    assert resumed.budget.llm_calls == saved_calls + 1
    assert models[("generator", "generate")].call_count == 0
    assert not any("iter_000" in work for _, work in calls)
    assert [entry["iteration"] for entry in resumed.state.read_designs()] == [0, 1]
    assert resumed.state.load_fsm()["phase"] == "DONE"


def test_done_resume_is_idempotent_and_tampered_winner_rejected(tmp_path, monkeypatch):
    o = fsm.Orchestrator(configuration(tmp_path), tmp_path / "run")
    install_models(o)
    install_tools(monkeypatch)
    summary = o.run()
    run = o.state.run_dir
    resumed = fsm.Orchestrator(RunConfig.load(run / "config.json"), run)
    install_models(resumed, forbidden=True)
    monkeypatch.setattr(fsm.vivado, "xsim_run", Mock(side_effect=AssertionError("duplicate tool run")))
    assert resumed.run() == summary
    (run / "m_best.v").write_text(SOURCE)
    with pytest.raises(ValueError, match="winner artifact"):
        resumed.run()


@pytest.mark.parametrize("target", ["summary", "report"])
def test_done_resume_rejects_changed_result_evidence(tmp_path, monkeypatch, target):
    o = fsm.Orchestrator(configuration(tmp_path), tmp_path / "run")
    install_models(o)
    install_tools(monkeypatch)
    result = o.run()
    path = o.state.run_dir / "run_summary.json" if target == "summary" else Path(result["best_artifact_dir"]) / "utilization.rpt"
    path.write_text("altered evidence")
    with pytest.raises(ValueError, match="evidence"):
        fsm.Orchestrator(RunConfig.load(o.state.run_dir / "config.json"), o.state.run_dir).run()


@pytest.mark.parametrize("change", ["input", "config", "implementation", "journal"])
def test_resume_rejects_changed_checkpoint_context(tmp_path, monkeypatch, change):
    o = fsm.Orchestrator(configuration(tmp_path), tmp_path / "run")
    install_models(o)
    install_tools(monkeypatch, fail_compile=True)
    with pytest.raises(KeyboardInterrupt): o.run()
    cfg = RunConfig.load(o.state.run_dir / "config.json")
    if change == "input": cfg.design_path.write_text("corrupted frozen input")
    elif change == "config": cfg.target_freq_mhz = 200
    elif change == "implementation":
        path = o.state.run_dir / "runtime.json"
        data = json.loads(path.read_text()); data["python"] = "different interpreter"
        path.write_text(json.dumps(data))
    else:
        evidence = next((o.state.run_dir / "journal").glob("*/artifacts/*.v"))
        evidence.write_text("corrupted stage evidence")
    resumed = fsm.Orchestrator(cfg, o.state.run_dir)
    install_models(resumed, forbidden=True)
    install_tools(monkeypatch)
    with pytest.raises(ValueError): resumed.run()


def test_infra_blocked_round_does_not_record_design_rejection(tmp_path, monkeypatch):
    o = fsm.Orchestrator(configuration(tmp_path), tmp_path / "run")
    install_models(o)
    install_tools(monkeypatch, fail_sim=True)
    summary = o.run()
    assert summary["status"] == "infra_blocked"
    assert [entry["iteration"] for entry in o.state.read_designs()] == [0]
    assert "REJECT" not in o.state.read_progress()
    # The failed tool stage was not committed; a later resume can retry it.
    resumed = fsm.Orchestrator(RunConfig.load(o.state.run_dir / "config.json"), o.state.run_dir)
    models = install_models(resumed)
    install_tools(monkeypatch)
    assert resumed.run()["best_iteration"] == 1
    assert models[("generator", "generate")].call_count == 0


@pytest.mark.parametrize("change", ["edit", "delete"])
def test_done_retains_tool_exit_receipts_even_when_not_a_report(tmp_path, monkeypatch, change):
    o = fsm.Orchestrator(configuration(tmp_path), tmp_path / "run")
    install_models(o)
    install_tools(monkeypatch)
    original_synth = fsm.vivado.run_synthesis
    def synth(files, top, cfg, work, **kwargs):
        return original_synth(files, top, cfg, work, **kwargs)
    monkeypatch.setattr(fsm.vivado, "run_synthesis", synth)
    result = o.run()
    path = Path(result["best_artifact_dir"]) / "tool_exit_records.log"
    assert str(path.resolve()) in o.state.load_fsm()["final_artifacts"]
    if change == "delete": path.unlink()
    else: path.write_text("modified receipt")
    with pytest.raises(ValueError, match="evidence"):
        fsm.Orchestrator(RunConfig.load(o.state.run_dir / "config.json"), o.state.run_dir).run()


@pytest.mark.parametrize("failure",["missing","malformed","latest_failed","log_tampered"])
def test_accepting_model_cannot_promote_unknown_or_failed_tool_exits(tmp_path,monkeypatch,failure):
    o=fsm.Orchestrator(configuration(tmp_path),tmp_path/"run")
    models=install_models(o); install_tools(monkeypatch)
    original=fsm.vivado.run_synthesis
    def synth(files,top,cfg,work,**kwargs):
        result=original(files,top,cfg,work,**kwargs)
        if "cand_" in str(work):
            path=work/"tool_exit_records.log"
            if failure=="missing": path.unlink()
            elif failure=="malformed": path.write_text("{broken")
            elif failure=="log_tampered": (work/"mock_xsim.log").write_text("modified")
            else:
                rows=path.read_text().splitlines(); record=json.loads(rows[-1])
                record.update(returncode=1,driver_returncode=1)
                path.write_text("\n".join(rows+[json.dumps(record)])+"\n")
        return result
    monkeypatch.setattr(fsm.vivado,"run_synthesis",synth)
    result=o.run()
    assert result["status"]=="infra_blocked" and result["best_iteration"]==0
    assert result["best_metrics"]["lut_used"]==20
    models[("evaluator","evaluate")].assert_not_called()
    assert [row["iteration"] for row in o.state.read_designs()]==[0]
    assert "REJECT" not in o.state.read_progress()
    facts=json.loads((o.state.iter_dir(1)/"evaluation_facts.json").read_text())
    assert facts["process_exit_gate"]["passed"] is False


@pytest.mark.parametrize("change",["edit","delete"])
def test_done_rejects_changed_receipt_output_logs(tmp_path,monkeypatch,change):
    o=fsm.Orchestrator(configuration(tmp_path),tmp_path/"run")
    install_models(o); install_tools(monkeypatch)
    result=o.run(); path=Path(result["best_artifact_dir"])/"mock_xsim.log"
    assert str(path.resolve()) in o.state.load_fsm()["final_artifacts"]
    if change=="delete": path.unlink()
    else: path.write_text("changed output")
    with pytest.raises(ValueError,match="evidence"):
        fsm.Orchestrator(RunConfig.load(o.state.run_dir/"config.json"),o.state.run_dir).run()


def test_baseline_missing_receipts_does_not_create_verified_history(tmp_path,monkeypatch):
    o=fsm.Orchestrator(configuration(tmp_path),tmp_path/"run")
    install_models(o); install_tools(monkeypatch)
    original=fsm.vivado.run_synthesis
    def synth(files,top,cfg,work,**kwargs):
        result=original(files,top,cfg,work,**kwargs)
        if "iter_000" in str(work): (work/"tool_exit_records.log").unlink()
        return result
    monkeypatch.setattr(fsm.vivado,"run_synthesis",synth)
    result=o.run()
    assert result["status"]=="baseline_blocked"
    assert o.state.read_designs()==[] and result["best_iteration"] is None


@pytest.mark.parametrize("changed",["testbench","extra","source"])
def test_completed_simulation_replay_never_restamps_changed_inputs(tmp_path,monkeypatch,changed):
    cfg=configuration(tmp_path); o=fsm.Orchestrator(cfg,tmp_path/"run")
    work=o.state.iter_dir(1); source=work/"m.v"; source.write_text(SOURCE)
    extra=tmp_path/"companion.v"; extra.write_text("module companion; endmodule")
    calls=[]
    def simulate(*args,**kwargs): calls.append(1); return True,"",FailureKind.DESIGN
    monkeypatch.setattr(fsm.vivado,"xsim_run",simulate)
    monkeypatch.setattr(fsm.vivado,"vivado_seconds",lambda:0)
    o._journal_enabled=True; o._scope="lineage_test"
    o._tool("xsim_run",[source,extra],cfg.testbench_path,"m_tb",cfg,work)
    manifest=work/"verification_inputs.log"; saved=manifest.read_bytes()
    assert any((o.state.run_dir/"journal").glob("*/artifacts/verification_inputs.log"))
    target={"testbench":cfg.testbench_path,"extra":extra,"source":source}[changed]
    target.write_text("changed verification input")
    o._counts={}
    with pytest.raises(fsm.VerificationEvidenceError,match="replay inputs"):
        o._tool("xsim_run",[source,extra],cfg.testbench_path,"m_tb",cfg,work)
    assert calls==[1] and manifest.read_bytes()==saved


def test_simulation_inputs_changed_during_execution_are_not_verified(tmp_path,monkeypatch):
    cfg=configuration(tmp_path); o=fsm.Orchestrator(cfg,tmp_path/"run")
    work=o.state.iter_dir(1); source=work/"m.v"; source.write_text(SOURCE)
    def simulate(*args,**kwargs):
        cfg.testbench_path.write_text("changed during execution")
        return True,"",FailureKind.DESIGN
    monkeypatch.setattr(fsm.vivado,"xsim_run",simulate)
    monkeypatch.setattr(fsm.vivado,"vivado_seconds",lambda:0)
    with pytest.raises(fsm.VerificationEvidenceError,match="changed during"):
        o._tool("xsim_run",[source],cfg.testbench_path,"m_tb",cfg,work)
    assert not (work/"verification_inputs.log").exists()
