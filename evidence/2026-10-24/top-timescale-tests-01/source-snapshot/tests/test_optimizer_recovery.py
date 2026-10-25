"""Bound candidate design repairs and prioritize verified timing recovery."""
import json
from unittest.mock import Mock
import pytest
from autortl import fsm
from autortl.bestofn import Candidate
from autortl.config import RunConfig
from autortl.report_parser import VivadoMetrics
from autortl.roles import Evaluation
from autortl.triage import FailureKind
from tests.test_fsm_resume import SOURCE, WINNER, configuration, install_models, install_tools, write_mock_tool_receipts


def setup_candidate(tmp_path, monkeypatch, fixes=1):
    o = fsm.Orchestrator(RunConfig(mode="optimize", top_module="m", max_fix_attempts=fixes), tmp_path / "run")
    tb = tmp_path / "m_tb.v"; tb.write_text("// frozen temporal test")
    parent = o.state.iter_dir(1)
    candidate = Candidate(SOURCE, "standard")
    repair = Mock(return_value=WINNER)
    monkeypatch.setattr(o.generator, "fix", repair)
    return o, candidate, o._infer_contract(SOURCE, "m"), tb, parent, repair


def test_compile_repair_restarts_all_gates_and_retains_each_source(tmp_path, monkeypatch):
    o, c, contract, tb, parent, repair = setup_candidate(tmp_path, monkeypatch)
    calls = []
    def tool(name, *args, **kwargs):
        work = args[2] if name == "xvlog_check" else args[4]
        calls.append((name, work))
        if name == "xvlog_check" and work.name == "cand_standard":
            (work / "xvlog.log").write_text("WARNING: [VRFC 10-3609] overwriting previous definition")
            return False, "WARNING: [VRFC 10-3609] overwriting previous definition", FailureKind.DESIGN
        return True, "", FailureKind.DESIGN
    monkeypatch.setattr(o, "_tool", tool)
    errors = []
    o._verify_optimization_candidate(c, contract, tb, [], parent, errors)
    assert c.alive and c.ladder_rungs_passed == 4
    assert [name for name, _ in calls] == ["xvlog_check", "xvlog_check", "xsim_run"]
    assert calls[0][1].name == "cand_standard" and calls[1][1].name == "repair_001"
    assert c.artifact_dir == calls[-1][1]
    assert (parent / "cand_standard/m.v").read_text() == SOURCE
    assert (c.artifact_dir / "m.v").read_text() == WINNER
    assert "overwriting" in (parent / "cand_standard/xvlog.log").read_text()
    assert "frozen companion" in repair.call_args.args[1]
    assert repair.call_args.args[3] == tb.read_text()
    assert len(errors) == 1 and repair.call_count == 1


@pytest.mark.parametrize("kind", [FailureKind.INFRA, FailureKind.UNKNOWN])
@pytest.mark.parametrize("stage", ["xvlog_check", "xsim_run"])
def test_infrastructure_never_consumes_design_repair(tmp_path, monkeypatch, kind, stage):
    o, c, contract, tb, parent, repair = setup_candidate(tmp_path, monkeypatch)
    def tool(name, *args, **kwargs):
        return (False, "license unavailable", kind) if name == stage else (True, "", FailureKind.DESIGN)
    monkeypatch.setattr(o, "_tool", tool)
    errors = []
    o._verify_optimization_candidate(c, contract, tb, [], parent, errors)
    assert c.alive and c.ladder_rungs_passed < 4 and c.verilog == SOURCE
    assert c.fail_reason.startswith("unverified:") and errors == []
    repair.assert_not_called()
    assert o.state.read_designs() == []


def test_shared_compile_and_simulation_repair_bound(tmp_path, monkeypatch):
    o, c, contract, tb, parent, repair = setup_candidate(tmp_path, monkeypatch, fixes=2)
    calls = []
    def tool(name, *args, **kwargs):
        work = args[2] if name == "xvlog_check" else args[4]
        calls.append((name, work.name))
        if work.name == "cand_standard" or name == "xsim_run":
            return False, "TEST FAILED controlled design failure", FailureKind.DESIGN
        return True, "", FailureKind.DESIGN
    monkeypatch.setattr(o, "_tool", tool)
    errors = []
    o._verify_optimization_candidate(c, contract, tb, [], parent, errors)
    assert not c.alive and c.ladder_rungs_passed < 4
    assert repair.call_count == 2 and len(errors) == 3
    assert repair.call_args_list[0].args[4] == []
    assert repair.call_args_list[1].args[4] == ["TEST FAILED controlled design failure"]
    assert [work for name, work in calls if name == "xvlog_check"] == ["cand_standard", "repair_001", "repair_002"]


@pytest.mark.parametrize("stage", ["xvlog_check", "xsim_run"])
def test_zero_repair_budget_is_honored(tmp_path, monkeypatch, stage):
    o, c, contract, tb, parent, repair = setup_candidate(tmp_path, monkeypatch, fixes=0)
    monkeypatch.setattr(o, "_tool", lambda name, *args, **kwargs: (False, "FAIL broken RTL", FailureKind.DESIGN) if name == stage else (True, "", FailureKind.DESIGN))
    o._verify_optimization_candidate(c, contract, tb, [], parent, [])
    assert not c.alive and c.ladder_rungs_passed < 4
    repair.assert_not_called()


def test_repair_cannot_change_public_interface(tmp_path, monkeypatch):
    o, c, contract, tb, parent, repair = setup_candidate(tmp_path, monkeypatch)
    repair.return_value = "module m(output [7:0] other); assign other=0; endmodule"
    tool = Mock(return_value=(False, "FAIL compile", FailureKind.DESIGN))
    monkeypatch.setattr(o, "_tool", tool)
    o._verify_optimization_candidate(c, contract, tb, [], parent, [])
    assert not c.alive and c.ladder_rungs_passed == 0
    assert tool.call_count == 1 and repair.call_count == 1
    assert (parent / "cand_standard/repair_001/m.v").read_text() == repair.return_value


def test_full_loop_promotes_higher_area_timing_recovery_and_done_replays(tmp_path, monkeypatch):
    cfg = configuration(tmp_path)
    o = fsm.Orchestrator(cfg, tmp_path / "run")
    install_models(o); install_tools(monkeypatch)
    def metrics(work):
        base = "iter_000" in work.parts
        return VivadoMetrics(sim_passed=True, lut_used=13 if base else 20, lut_total=100,
            ff_used=6 if base else 30, ff_total=200, wns_ns=-.931 if base else .2,
            whs_ns=.091 if base else .1, timing_met=not base)
    monkeypatch.setattr(fsm.vivado, "full_metrics", metrics)
    result = o.run()
    assert result["best_iteration"] == 1 and result["timing_closed"] is True
    assert result["improvement_kind"] == "timing_recovery" and result["best_metrics"]["lut_used"] == 20
    facts = json.loads((o.state.run_dir / "iter_001/evaluation_facts.json").read_text())
    assert facts["improvement_kind"] == "timing_recovery" and facts["measured_improvement"] is True
    assert facts["candidate_timing_feasible"] and not facts["previous_best_timing_feasible"]
    assert o.state.read_designs()[-1]["improvement_kind"] == "timing_recovery"
    resumed = fsm.Orchestrator(RunConfig.load(o.state.run_dir / "config.json"), o.state.run_dir)
    install_models(resumed, forbidden=True)
    assert resumed.run() == result


def test_compile_repair_journal_replay_does_not_repeat_model_fix(tmp_path, monkeypatch):
    cfg = configuration(tmp_path); cfg.max_fix_attempts = 1
    o = fsm.Orchestrator(cfg, tmp_path / "run")
    install_models(o); install_tools(monkeypatch)
    repair = Mock(return_value=WINNER); monkeypatch.setattr(o.generator, "fix", repair)
    original = fsm.vivado.xvlog_check
    def compile(files, config, work, **kwargs):
        if work.name == "cand_standard":
            return False, "WARNING: [VRFC 10-3609] overwriting previous definition", FailureKind.DESIGN
        if work.name == "repair_001":
            raise KeyboardInterrupt("interrupted repaired compile")
        return original(files, config, work, **kwargs)
    monkeypatch.setattr(fsm.vivado, "xvlog_check", compile)
    with pytest.raises(KeyboardInterrupt): o.run()
    assert repair.call_count == 1
    resumed = fsm.Orchestrator(RunConfig.load(o.state.run_dir / "config.json"), o.state.run_dir)
    install_models(resumed); install_tools(monkeypatch)
    duplicate = Mock(side_effect=AssertionError("journaled fix must not repeat"))
    monkeypatch.setattr(resumed.generator, "fix", duplicate)
    result = resumed.run()
    assert result["best_iteration"] == 1
    assert result["best_artifact_dir"].endswith("repair_001")
    duplicate.assert_not_called()
    assert (o.state.run_dir / "iter_001/cand_standard/m.v").is_file()
    assert (o.state.run_dir / "iter_001/cand_standard/repair_001/m.v").is_file()



def test_repair_cannot_change_known_latency(tmp_path, monkeypatch):
    o, c, contract, tb, parent, repair = setup_candidate(tmp_path, monkeypatch)
    contract.latency_known = True; contract.latency = 1
    repair.return_value = "// @latency 2\n" + WINNER
    tool = Mock(return_value=(False, "FAIL compile", FailureKind.DESIGN))
    monkeypatch.setattr(o, "_tool", tool)
    o._verify_optimization_candidate(c, contract, tb, [], parent, [])
    assert not c.alive and "latency" in c.fail_reason
    assert tool.call_count == 1 and repair.call_count == 1


def test_completed_experiment_with_unclosed_baseline_is_explicit(tmp_path, monkeypatch):
    o = fsm.Orchestrator(configuration(tmp_path), tmp_path / "run")
    install_models(o); install_tools(monkeypatch)
    monkeypatch.setattr(o.generator, "generate", Mock(return_value="module invalid; endmodule"))
    monkeypatch.setattr(fsm.vivado, "full_metrics", lambda work: VivadoMetrics(
        sim_passed=True,lut_used=13,lut_total=100,ff_used=6,ff_total=200,
        wns_ns=-.931,whs_ns=.091,timing_met=False))
    result = o.run()
    assert result["status"] == "done" and result["best_iteration"] == 0
    assert result["timing_closed"] is False and result["improvement_kind"] is None
    o.evaluator.evaluate.assert_not_called()



def test_non_ascii_candidate_reaches_evaluation_and_promotion(tmp_path, monkeypatch):
    o = fsm.Orchestrator(configuration(tmp_path), tmp_path / "run")
    install_models(o); install_tools(monkeypatch)
    source = "// café Ω 中文\n" + WINNER
    monkeypatch.setattr(o.generator, "generate", Mock(return_value=source))
    result = o.run()
    assert result["best_iteration"] == 1 and result["timing_closed"] is True
    assert (o.state.run_dir / "m_best.v").read_text(encoding="utf-8") == source
    assert (o.state.run_dir / "iter_001/cand_standard/m.v").read_text(encoding="utf-8") == source



@pytest.mark.parametrize("change", ["tamper", "delete"])
def test_done_binds_generated_child_dependency(tmp_path, monkeypatch, change):
    from tests.test_fsm_build import create
    o, _ = create(tmp_path, monkeypatch)
    result = o.run(); assert result["status"] == "done"
    child = o.state.run_dir / "modules/counter8_core/counter8_core.v"
    if change == "delete": child.unlink()
    else: child.write_bytes(child.read_bytes() + b"\n// changed child identity\n")
    resumed = fsm.Orchestrator(RunConfig.load(o.state.run_dir / "config.json"), o.state.run_dir)
    forbidden = Mock(side_effect=AssertionError("DONE must not regenerate child"))
    monkeypatch.setattr(resumed.generator, "generate", forbidden)
    with pytest.raises(ValueError, match="Completed"):
        resumed.run()
    forbidden.assert_not_called()


def test_finalization_does_not_bless_changed_verified_child(tmp_path, monkeypatch):
    from tests.test_fsm_build import create, RTL
    o, _ = create(tmp_path, monkeypatch)
    count = 0
    def generate(*args, **kwargs):
        nonlocal count
        count += 1
        if count == 2:
            child = o.state.run_dir / "modules/counter8_core/counter8_core.v"
            child.write_bytes(child.read_bytes() + b"\n// changed after verified simulation\n")
        return RTL
    monkeypatch.setattr(o.generator, "generate", Mock(side_effect=generate))
    result = o.run()
    assert result["status"] == "infra_blocked" and result["failure_kind"] == "infra"
    assert "verification dependency" in result["error"]
    assert o.state.load_fsm()["phase"] == "INFRA_BLOCKED"
    assert not (o.state.run_dir / "counter8_best.v").exists()
