import json
from pathlib import Path
from unittest.mock import Mock
import pytest
from autortl import fsm
from autortl.config import RunConfig
from autortl.report_parser import VivadoMetrics
from autortl.roles import Evaluation
from autortl.triage import FailureKind
from tests.test_fsm_resume import write_mock_tool_receipts

ROOT = Path(__file__).resolve().parents[1]
RTL = "module counter8_core(input clk,input rst,input enable,output reg [7:0] count); always @(posedge clk) if(rst) count<=0; else if(enable) count<=count+1'b1; endmodule"


def create(tmp_path, monkeypatch, mutant_kind=FailureKind.DESIGN):
    fixture = ROOT / "curriculum/tier1/counter8_build"
    cfg = RunConfig(mode="build", spec_path=fixture / "design_spec.json",
                    testbench_path=fixture / "counter8_tb.v", max_iterations=1,
                    best_of_n=1, max_fix_attempts=1)
    o = fsm.Orchestrator(cfg, tmp_path / "run")
    monkeypatch.setattr(o.generator, "generate", Mock(return_value=RTL))
    monkeypatch.setattr(o.generator, "golden_model", Mock(side_effect=AssertionError("trusted TB must not invoke generated oracle")))
    monkeypatch.setattr(o.planner, "make_spec", Mock(side_effect=AssertionError("typed JSON must not be replanned")))
    monkeypatch.setattr(o.planner, "propose_contract", Mock(return_value="contract"))
    monkeypatch.setattr(o.planner, "plan", Mock(return_value="plan"))
    monkeypatch.setattr(o.evaluator, "review_contract", Mock(return_value="ACCEPT"))
    monkeypatch.setattr(o.evaluator, "evaluate", Mock(return_value=Evaluation("REJECT", "REJECT", 1, 0)))
    def compile(files, config, work, **kwargs):
        write_mock_tool_receipts(work, ("xvlog",))
        return True, "", FailureKind.DESIGN
    monkeypatch.setattr(fsm.vivado, "xvlog_check", Mock(side_effect=compile))
    def sim(files, tb, top, config, work, **kwargs):
        if "mutant" in work.parts:
            return False, "Testbench failures:\nFAIL wrong count" if mutant_kind == FailureKind.DESIGN else "license unavailable", mutant_kind
        write_mock_tool_receipts(work, ("xvlog", "xelab", "xsim"))
        return True, "", FailureKind.DESIGN
    monkeypatch.setattr(fsm.vivado, "xsim_run", sim)
    def synthesize(files, top, config, work, **kwargs):
        write_mock_tool_receipts(work, ("vivado",))
        return True, "", FailureKind.DESIGN
    synth = Mock(side_effect=synthesize)
    monkeypatch.setattr(fsm.vivado, "run_synthesis", synth)
    monkeypatch.setattr(fsm.vivado, "full_metrics", Mock(return_value=VivadoMetrics(
        sim_passed=True, lut_used=6, lut_total=20800, ff_used=8, ff_total=41600,
        wns_ns=7, whs_ns=0.2, timing_met=True)))
    monkeypatch.setattr(fsm.vivado, "vivado_seconds", lambda: 0)
    return o, synth


def test_typed_build_generates_qualifies_integrates_and_done_resumes(tmp_path, monkeypatch):
    o, synthesis = create(tmp_path, monkeypatch)
    result = o.run()
    assert result["status"] == "done"
    assert result["top_module"] == "counter8"
    assert "counter8_core u_counter8_core" in (o.state.run_dir / "counter8_best.v").read_text()
    assert synthesis.call_count == 1  # Invalid optimization candidate never reaches implementation.
    resumed = fsm.Orchestrator(RunConfig.load(o.state.run_dir / "config.json"), o.state.run_dir)
    monkeypatch.setattr(resumed.generator, "generate", Mock(side_effect=AssertionError("duplicate generation")))
    assert resumed.run() == result


@pytest.mark.parametrize("kind", [FailureKind.INFRA, FailureKind.UNKNOWN])
def test_qualification_tool_failure_cannot_promote_build(tmp_path, monkeypatch, kind):
    o, synthesis = create(tmp_path, monkeypatch, kind)
    result = o.run()
    assert result["status"] != "done"
    synthesis.assert_not_called()
    assert not (o.state.run_dir / "counter8_best.v").exists()


def test_multi_module_build_requires_independent_top_testbench(tmp_path, monkeypatch):
    o, synthesis = create(tmp_path, monkeypatch)
    data = json.loads(o.cfg.spec_path.read_text())
    second = json.loads(json.dumps(data["modules"][0]))
    second["name"] = "other"
    second["ports"] = [p for p in second["ports"] if p["direction"] == "input"]
    data["modules"].append(second)
    path = tmp_path / "spec.json"; path.write_text(json.dumps(data))
    o.cfg.spec_path = path
    o.cfg.testbench_path = None
    monkeypatch.setattr(o, "_build_module", Mock(return_value=RTL))
    result = o.run()
    assert result["status"] == "build_blocked"
    synthesis.assert_not_called()
