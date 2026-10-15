from unittest.mock import Mock
import pytest
from autortl import fsm
from autortl.config import RunConfig
from autortl.report_parser import VivadoMetrics
from autortl.triage import FailureKind
from autortl.spec import ModuleSpec


@pytest.mark.parametrize("stage", ["compile", "sim", "repair", "missing_tb"])
@pytest.mark.parametrize("kind", [FailureKind.INFRA, FailureKind.UNKNOWN])
def test_incomplete_candidate_never_synthesized_or_cached(tmp_path, monkeypatch, stage, kind):
    design = tmp_path / "m.v"
    design.write_text("module m(input clk, input rst, output y); assign y=0; endmodule")
    tb = tmp_path / "tb.v"
    tb.write_text("// simulator mocked")
    cfg = RunConfig(mode="optimize", top_module="m", design_path=design,
                    testbench_path=None if stage == "missing_tb" else tb,
                    max_iterations=1, best_of_n=1)
    o = fsm.Orchestrator(cfg, tmp_path / "run")
    baseline = VivadoMetrics(sim_passed=True, lut_used=20, lut_total=20800,
                             ff_total=41600, wns_ns=1, timing_met=True)
    monkeypatch.setattr(o, "_full_flow", Mock(return_value=baseline))
    monkeypatch.setattr(o.planner, "propose_contract", Mock(return_value="contract"))
    monkeypatch.setattr(o.evaluator, "review_contract", Mock(return_value="ACCEPT"))
    monkeypatch.setattr(o.planner, "plan", Mock(return_value="plan"))
    candidate = design.read_text().replace("y=0", "y=1")
    monkeypatch.setattr(o.generator, "generate", Mock(return_value=candidate))
    fix = Mock(return_value=candidate)
    monkeypatch.setattr(o.generator, "fix", fix)
    failed = (False, "tool unavailable", kind)
    monkeypatch.setattr(fsm.vivado, "xvlog_check", Mock(
        return_value=failed if stage == "compile" else (True, "", FailureKind.DESIGN)))
    sim = Mock(return_value=failed)
    if stage == "repair":
        sim.side_effect = [(False, "TEST FAILED", FailureKind.DESIGN), failed]
    monkeypatch.setattr(fsm.vivado, "xsim_run", sim)
    synth = Mock(side_effect=AssertionError("unverified candidate reached synthesis"))
    cache = Mock(side_effect=AssertionError("unverified candidate reached cache"))
    monkeypatch.setattr(fsm.vivado, "run_synthesis", synth)
    monkeypatch.setattr(o.metrics_cache, "get", cache)
    result = o.run()
    assert result["best_iteration"] == 0
    synth.assert_not_called()
    cache.assert_not_called()
    assert fix.call_count == (1 if stage == "repair" else 0)


@pytest.mark.parametrize("second_qualified", [False, True])
def test_regenerated_testbench_must_be_requalified(tmp_path, monkeypatch, second_qualified):
    o = fsm.Orchestrator(RunConfig(mode="build"), tmp_path / "run")
    module = ModuleSpec("m", "test", [])
    work = tmp_path / "module"
    work.mkdir()
    (work / "golden.py").write_text("# mocked golden model")
    tb = work / "m_tb.v"
    tb.write_text("// mocked testbench")
    monkeypatch.setattr(fsm, "GoldenModel", Mock())
    monkeypatch.setattr(fsm, "qualify_against_examples", Mock(return_value=[]))
    monkeypatch.setattr(fsm, "generate_tb", Mock(return_value=tb))
    monkeypatch.setattr(o, "_generate_verified", Mock(return_value="module m; endmodule"),
                        raising=False)
    qualification = Mock(side_effect=[(False, "missed bug"), (second_qualified, "retry")])
    monkeypatch.setattr(fsm, "qualify_tb", qualification)
    monkeypatch.setattr(fsm.vivado, "xsim_run", Mock(return_value=(True, "", FailureKind.DESIGN)))
    result = o._build_module(module, work)
    assert (result is not None) is second_qualified
    assert qualification.call_count == 2
