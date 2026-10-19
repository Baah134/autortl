"""Baseline failures and search restarts cannot fabricate a winning artifact."""
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from autortl import fsm
from autortl.config import RunConfig
from autortl.report_parser import VivadoMetrics
from autortl.roles import Evaluation
from autortl.triage import FailureKind


def good(luts=20):
    return VivadoMetrics(sim_passed=True, lut_used=luts, lut_total=20800,
                         ff_used=10, ff_total=41600, wns_ns=1, whs_ns=0.1,
                         timing_met=True)


@pytest.fixture
def harness(tmp_path, monkeypatch):
    design = tmp_path / "m.v"
    design.write_text("module m(input clk, input rst, output y); assign y=0; endmodule")
    tb = tmp_path / "m_tb.v"
    tb.write_text("// mocked simulation")
    cfg = RunConfig(mode="optimize", top_module="m", design_path=design,
                    testbench_path=tb, max_iterations=0, max_fix_attempts=2)
    o = fsm.Orchestrator(cfg, tmp_path / "run")
    # Every external model/tool path is mocked; accidental calls fail the test.
    for role in ("planner", "generator", "evaluator", "doctor"):
        obj = getattr(o, role)
        for name in dir(obj):
            if not name.startswith("_") and callable(getattr(obj, name)):
                monkeypatch.setattr(obj, name, Mock(side_effect=AssertionError("unexpected model call")))
    for name in ("xsim_run", "xvlog_check", "run_synthesis", "full_metrics"):
        monkeypatch.setattr(fsm.vivado, name, Mock(side_effect=AssertionError("unexpected tool call")))
    monkeypatch.setattr(fsm.vivado, "vivado_seconds", Mock(return_value=0))
    return o


def assert_no_winner(o, result):
    assert result["best_iteration"] is None
    assert "best_metrics" not in result
    assert o.state.read_designs() == []
    assert not (o.state.run_dir / "m_best.v").exists()
    assert json.loads((o.state.run_dir / "run_summary.json").read_text()) == result
    o.planner.propose_contract.assert_not_called()


@pytest.mark.parametrize("missing", [None, "absent.v"])
def test_missing_testbench_blocks_before_tool_or_model(harness, missing):
    o = harness
    o.cfg.testbench_path = missing
    result = o.run()
    assert result["status"] == "baseline_blocked"
    assert_no_winner(o, result)
    fsm.vivado.xsim_run.assert_not_called()
    o.generator.fix.assert_not_called()


@pytest.mark.parametrize("stage", ["sim", "synth"])
@pytest.mark.parametrize("kind", [FailureKind.INFRA, FailureKind.UNKNOWN])
def test_tool_failure_kind_overrides_design_looking_message(harness, stage, kind):
    o = harness
    # Exact tool classification must win over the word FAIL in a diagnostic.
    fsm.vivado.xsim_run.side_effect = None
    fsm.vivado.xsim_run.return_value = ((False, "FAIL tool unavailable", kind)
                                      if stage == "sim" else (True, "", FailureKind.DESIGN))
    fsm.vivado.run_synthesis.side_effect = None
    fsm.vivado.run_synthesis.return_value = (False, "FAIL tool unavailable", kind)
    result = o.run()
    assert result["status"] == "baseline_blocked"
    assert result["failure_kind"] == kind.value
    assert_no_winner(o, result)
    o.generator.fix.assert_not_called()


def test_failed_design_baseline_exhausts_fixes_without_promotion(harness):
    o = harness
    fsm.vivado.xsim_run.side_effect = None
    fsm.vivado.xsim_run.return_value = (False, "TEST FAILED", FailureKind.DESIGN)
    o.generator.fix.side_effect = None
    o.generator.fix.return_value = o.cfg.design_path.read_text()
    result = o.run()
    assert result["status"] == "baseline_failed"
    assert o.generator.fix.call_count == 2
    assert_no_winner(o, result)
    fsm.vivado.run_synthesis.assert_not_called()


def test_repair_stops_immediately_on_infrastructure_failure(harness):
    o = harness
    fsm.vivado.xsim_run.side_effect = [
        (False, "TEST FAILED", FailureKind.DESIGN),
    ] + [(False, "license unavailable", FailureKind.INFRA)] * (o.cfg.max_infra_retries + 1)
    o.generator.fix.side_effect = None
    o.generator.fix.return_value = o.cfg.design_path.read_text()
    result = o.run()
    assert result["status"] == "baseline_blocked"
    assert o.generator.fix.call_count == 1
    assert_no_winner(o, result)


@pytest.mark.parametrize("field,value", [
    ("lut_total", 0), ("wns_ns", -999), ("whs_ns", -999),
    ("wns_ns", float("nan")), ("whs_ns", float("inf")),
])
def test_invalid_baseline_metrics_stop_before_negotiation(harness, monkeypatch, field, value):
    metrics = good()
    setattr(metrics, field, value)
    monkeypatch.setattr(harness, "_full_flow", Mock(return_value=metrics))
    result = harness.run()
    assert result["status"] == "baseline_blocked"
    assert_no_winner(harness, result)
    harness.generator.fix.assert_not_called()


def allow_negotiation(o):
    o.planner.propose_contract.side_effect = None
    o.planner.propose_contract.return_value = "contract"
    o.evaluator.review_contract.side_effect = None
    o.evaluator.review_contract.return_value = "ACCEPT"


def test_repaired_baseline_exports_matching_source_and_metrics(harness):
    o = harness
    repaired = o.cfg.design_path.read_text().replace("y=0", "y=1")
    o.generator.fix.side_effect = None
    o.generator.fix.return_value = repaired
    fsm.vivado.xsim_run.side_effect = [
        (False, "TEST FAILED", FailureKind.DESIGN), (True, "", FailureKind.DESIGN)]
    fsm.vivado.run_synthesis.side_effect = None
    fsm.vivado.run_synthesis.return_value = (True, "", FailureKind.DESIGN)
    fsm.vivado.full_metrics.side_effect = None
    fsm.vivado.full_metrics.return_value = good(12)
    allow_negotiation(o)
    result = o.run()
    assert result["status"] == "done"
    assert result["best_iteration"] == 0
    assert result["best_metrics"]["lut_used"] == 12
    assert (o.state.run_dir / "m_best.v").read_text() == repaired
    assert o.state.read_designs()[0]["is_best"] is True


def test_full_flow_requires_testbench_even_when_called_directly(harness):
    o = harness
    result = o._full_flow([o.cfg.design_path], None, "m", o.state.run_dir)
    assert result.sim_passed is False
    assert o._flow_failure_kind(result) == FailureKind.UNKNOWN
    fsm.vivado.run_synthesis.assert_not_called()


def test_full_flow_keeps_explicit_simulation_verdict(harness):
    o = harness
    for name in ("xsim_run", "run_synthesis"):
        getattr(fsm.vivado, name).side_effect = None
        getattr(fsm.vivado, name).return_value = (True, "", FailureKind.DESIGN)
    metrics = good()
    metrics.sim_error = "Simulation log not found"
    fsm.vivado.full_metrics.side_effect = None
    fsm.vivado.full_metrics.return_value = metrics
    result = o._full_flow([o.cfg.design_path], o.cfg.testbench_path,
                          "m", o.state.run_dir)
    assert result.sim_passed is True
    assert result.sim_error == ""


def test_synthesis_design_failure_is_repaired_before_baseline_promotion(harness):
    o = harness
    repaired = o.cfg.design_path.read_text().replace("y=0", "y=1")
    o.generator.fix.side_effect = None
    o.generator.fix.return_value = repaired
    fsm.vivado.xsim_run.side_effect = None
    fsm.vivado.xsim_run.return_value = (True, "", FailureKind.DESIGN)
    fsm.vivado.run_synthesis.side_effect = [
        (False, "[Synth 8-123] unsupported construct", FailureKind.DESIGN),
        (True, "", FailureKind.DESIGN),
    ]
    fsm.vivado.full_metrics.side_effect = None
    fsm.vivado.full_metrics.return_value = good(12)
    allow_negotiation(o)
    result = o.run()
    assert result["status"] == "done"
    assert o.generator.fix.call_count == 1
    assert (o.state.run_dir / "m_best.v").read_text() == repaired


def test_restart_preserves_winner_and_changes_only_generation_seed(harness, monkeypatch):
    o = harness
    o.cfg.max_iterations = 3
    o.cfg.best_of_n = 1
    o.cfg.stall_restart_threshold = 1
    original = o.cfg.design_path.read_text()
    winner = original.replace("y=0", "y=1")
    other = original.replace("y=0", "y=2")
    monkeypatch.setattr(o, "_full_flow", Mock(return_value=good(20)))
    monkeypatch.setattr(fsm, "static_check", Mock(return_value=SimpleNamespace(passed=True)))
    monkeypatch.setattr(o.metrics_cache, "get", Mock(return_value=None))
    allow_negotiation(o)
    o.planner.plan.side_effect = None
    o.planner.plan.return_value = "plan"
    o.planner.restart_plan.side_effect = None
    o.planner.restart_plan.return_value = "new plan"
    o.generator.generate.side_effect = [winner, other, other]
    o.evaluator.evaluate.side_effect = [
        Evaluation("accepted", "ACCEPT", 1, 0),
        Evaluation("restart", "RESTART", 1, 0),
        Evaluation("reject", "REJECT", 1, 0),
    ]
    for name in ("xsim_run", "xvlog_check", "run_synthesis"):
        getattr(fsm.vivado, name).side_effect = None
        getattr(fsm.vivado, name).return_value = (True, "", FailureKind.DESIGN)
    fsm.vivado.full_metrics.side_effect = [good(10), good(15), good(15)]
    result = o.run()
    assert result["best_iteration"] == 1
    assert result["best_metrics"]["lut_used"] == 10
    assert (o.state.run_dir / "m_best.v").read_text() == winner
    seeds = [call.args[1] for call in o.generator.generate.call_args_list]
    assert seeds == [original, winner, original]
    o.planner.restart_plan.assert_called_once()
