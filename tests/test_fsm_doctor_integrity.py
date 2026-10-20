"""Doctor experiments must preserve previously verified artifacts."""
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from autortl import fsm
from autortl.config import RunConfig
from autortl.report_parser import VivadoMetrics
from autortl.roles import Evaluation
from autortl.triage import FailureKind


def metrics(luts=10, timing=False):
    return VivadoMetrics(sim_passed=True, lut_used=luts, lut_total=100,
                         ff_used=5, ff_total=200, wns_ns=1 if timing else -1,
                         whs_ns=0.1, timing_met=timing)


@pytest.fixture
def trial(tmp_path, monkeypatch):
    o = fsm.Orchestrator(RunConfig(mode="optimize", top_module="m"), tmp_path / "run")
    parent = o.state.iter_dir(1)
    original = parent / "cand_standard"
    original.mkdir()
    source = "module m(input clk, output y); assign y=0; endmodule"
    (original / "m.v").write_text(source)
    (original / "timing.rpt").write_text("original timing report")
    tb = tmp_path / "tb.v"
    tb.write_text("// independent mocked testbench")
    monkeypatch.setattr(o.doctor, "surgery", Mock(return_value=source.replace("y=0", "y=1")))
    monkeypatch.setattr(fsm, "static_check", Mock(return_value=SimpleNamespace(passed=True)))
    monkeypatch.setattr(fsm.vivado, "xsim_run", Mock(return_value=(True, "", FailureKind.DESIGN)))
    monkeypatch.setattr(fsm.vivado, "run_synthesis", Mock(return_value=(True, "", FailureKind.DESIGN)))
    monkeypatch.setattr(fsm.vivado, "full_metrics", Mock(return_value=metrics(8, True)))
    monkeypatch.setattr(fsm.vivado, "vivado_seconds", Mock(return_value=2))
    from tests.test_fsm_resume import write_mock_tool_receipts
    actual_tool = o._tool
    def mocked_tool_with_receipts(name, *args, **kwargs):
        result = actual_tool(name, *args, **kwargs)
        mapping = {"xvlog_check": (2, ("xvlog",)), "xsim_run": (4, ("xvlog", "xelab", "xsim")),
                   "run_synthesis": (3, ("vivado",))}
        if name in mapping and result[0]:
            index, tools = mapping[name]
            write_mock_tool_receipts(args[index], tools)
        return result
    monkeypatch.setattr(o, "_tool", mocked_tool_with_receipts)
    return o, parent, original, source, tb


def call_trial(trial, action="rtl_surgery", tb=True):
    o, parent, _, source, testbench = trial
    diag = SimpleNamespace(action=action, instruction="repair timing", detail="paths")
    return o._doctor_trial(source, metrics(), SimpleNamespace(latency=0),
                           testbench if tb else None, [], parent, diag)


def assert_original_unchanged(trial):
    _, _, original, source, _ = trial
    assert (original / "m.v").read_text() == source
    assert (original / "timing.rpt").read_text() == "original timing report"


@pytest.mark.parametrize("stage", ["static", "latency", "sim", "synth", "metrics", "worse", "missing_tb"])
def test_failed_surgery_never_overwrites_verified_candidate(trial, stage):
    o, *_ = trial
    if stage == "static":
        fsm.static_check.return_value = SimpleNamespace(passed=False)
    elif stage == "latency":
        o.doctor.surgery.return_value = "// @latency 3\n" + o.doctor.surgery.return_value
    elif stage == "sim":
        fsm.vivado.xsim_run.return_value = (False, "license unavailable", FailureKind.INFRA)
    elif stage == "synth":
        fsm.vivado.run_synthesis.return_value = (False, "timed out after 3s", FailureKind.INFRA)
    elif stage == "metrics":
        fsm.vivado.full_metrics.return_value.whs_ns = -999
    elif stage == "worse":
        fsm.vivado.full_metrics.return_value = metrics(15, False)
    assert call_trial(trial, tb=stage != "missing_tb") is None
    assert_original_unchanged(trial)


@pytest.mark.parametrize("action", ["tool_knobs", "rtl_surgery"])
def test_success_adopts_matched_source_metrics_and_isolated_directory(trial, action):
    o, parent, _, source, _ = trial
    result = call_trial(trial, action)
    assert result is not None
    actual_source, actual_metrics, evidence_dir = result
    assert evidence_dir.parent == parent
    assert evidence_dir.name.startswith("doctor_")
    assert (evidence_dir / "m.v").read_text() == actual_source
    assert actual_source == (source if action == "tool_knobs" else o.doctor.surgery.return_value)
    assert actual_metrics.lut_used == 8
    assert actual_metrics.sim_passed
    assert fsm.vivado.run_synthesis.call_args.args[3] == evidence_dir
    assert o.budget.vivado_seconds == (2 if action == "tool_knobs" else 4)
    assert fsm.vivado.xsim_run.call_count == (0 if action == "tool_knobs" else 1)
    assert_original_unchanged(trial)


@pytest.mark.parametrize("action", ["tool_knobs", "rtl_surgery"])
def test_timing_recovery_at_equal_objective_can_be_adopted(trial, action):
    fsm.vivado.full_metrics.return_value = metrics(10, True)
    assert call_trial(trial, action) is not None


def test_invalid_tool_knob_metrics_do_not_replace_original(trial):
    fsm.vivado.full_metrics.return_value.lut_total = 0
    assert call_trial(trial, "tool_knobs") is None
    assert_original_unchanged(trial)


def prepare_loop(trial, monkeypatch):
    o, _, original, source, tb = trial
    o.cfg.design_path = original / "m.v"
    o.cfg.testbench_path = tb
    o.cfg.max_iterations = o.cfg.best_of_n = 1
    monkeypatch.setattr(o, "_full_flow", Mock(return_value=metrics(20, True)))
    monkeypatch.setattr(o.planner, "propose_contract", Mock(return_value="contract"))
    monkeypatch.setattr(o.planner, "plan", Mock(return_value="plan"))
    monkeypatch.setattr(o.evaluator, "review_contract", Mock(return_value="ACCEPT"))
    monkeypatch.setattr(o.evaluator, "evaluate", Mock(return_value=Evaluation("accepted", "ACCEPT", 1, 0)))
    monkeypatch.setattr(o.generator, "generate", Mock(return_value=source.replace("y=0", "y=1")))
    monkeypatch.setattr(fsm.vivado, "xvlog_check", Mock(return_value=(True, "", FailureKind.DESIGN)))
    from tests.test_fsm_resume import write_mock_tool_receipts
    write_mock_tool_receipts(o.state.iter_dir(0))
    return o


@pytest.mark.parametrize("change", ["sentinel", "malformed", "unverified", "synth_error", "unknown_field"])
def test_invalid_cache_falls_back_to_fresh_validated_synthesis(trial, monkeypatch, change):
    o = prepare_loop(trial, monkeypatch)
    cached = metrics(1, True).to_dict()
    if change == "sentinel":
        cached["whs_ns"] = -999
    elif change == "malformed":
        cached["lut_used"] = "not a number"
    elif change == "unverified":
        cached["sim_passed"] = False
    elif change == "synth_error":
        cached["synth_error"] = "failed implementation"
    else:
        cached["unexpected"] = "unsupported schema"
    monkeypatch.setattr(o.metrics_cache, "get_entry", Mock(return_value={
        "metrics": cached, "artifact_dir": str(o.state.run_dir / "cached_evidence")}))
    result = o.run()
    assert result["best_metrics"]["lut_used"] == 8
    fsm.vivado.run_synthesis.assert_called_once()


def test_valid_cache_remains_eligible_after_gate(trial, monkeypatch):
    o = prepare_loop(trial, monkeypatch)
    evidence = o.state.run_dir / "cached_evidence"
    evidence.mkdir()
    from tests.test_fsm_resume import write_mock_tool_receipts
    write_mock_tool_receipts(evidence)
    monkeypatch.setattr(o.metrics_cache, "get_entry", Mock(return_value={
        "metrics": metrics(9, True).to_dict(), "artifact_dir": str(evidence)}))
    result = o.run()
    assert result["best_metrics"]["lut_used"] == 9
    fsm.vivado.run_synthesis.assert_not_called()


def test_loop_promotes_matching_doctor_artifact_and_evaluates_trial_metrics(trial, monkeypatch):
    o = prepare_loop(trial, monkeypatch)
    monkeypatch.setattr(o.metrics_cache, "get", Mock(return_value=None))
    fsm.vivado.full_metrics.side_effect = [metrics(10, False), metrics(8, True)]
    monkeypatch.setattr(fsm, "diagnose", Mock(return_value=SimpleNamespace(
        action="rtl_surgery", instruction="repair", detail="path", wns_ns=-1,
        category=SimpleNamespace(value="rtl"))))
    fixed = trial[3].replace("y=0", "y=2")
    o.doctor.surgery.return_value = fixed
    result = o.run()
    assert result["best_metrics"]["lut_used"] == 8
    assert "doctor_rtl_surgery_" in result["best_artifact_dir"]
    assert (o.state.run_dir / "m_best.v").read_text() == fixed
    assert (o.state.iter_dir(1) / "cand_standard" / "m.v").read_text() != fixed
    assert o.evaluator.evaluate.call_args.args[3].lut_used == 8
    recorded = o.state.read_designs()[-1]
    assert recorded["artifact_dir"] == result["best_artifact_dir"]
    assert recorded["code_hash"] == result["best_code_hash"]


def test_hold_trial_requests_physical_fix_without_retiming_or_rtl_surgery(trial):
    from autortl.timing_doctor import TimingCategory
    o, parent, _, source, tb = trial
    diagnosis = SimpleNamespace(action="tool_knobs", category=TimingCategory.HOLD)
    assert o._doctor_trial(source, metrics(), SimpleNamespace(latency=0), tb, [], parent, diagnosis)
    options = fsm.vivado.run_synthesis.call_args.kwargs
    assert options["hold_fix"] is True and options["retiming"] is False
    o.doctor.surgery.assert_not_called()
    assert_original_unchanged(trial)
