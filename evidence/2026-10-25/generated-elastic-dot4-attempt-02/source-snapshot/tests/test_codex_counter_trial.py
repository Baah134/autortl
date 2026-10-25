import importlib.util
import json
from pathlib import Path
from unittest.mock import Mock
import pytest
from autortl.report_parser import VivadoMetrics
from autortl.triage import FailureKind


@pytest.mark.parametrize("failure", ["none", "simulation", "mutant_infra", "async_mutant_pass", "implementation", "timing"])
def test_supervised_codex_trial_preserves_stage_gates(tmp_path, monkeypatch, failure):
    path = Path(__file__).resolve().parents[1] / "scripts/check_codex_counter.py"
    spec = importlib.util.spec_from_file_location("codex_trial", path)
    trial = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(trial)
    out = tmp_path / "trial"
    monkeypatch.setattr("sys.argv", [str(path), "--bin-dir", str(tmp_path), "--output", str(out)])
    source = "module counter8(input clk,rst,enable,output reg [7:0] count); always @(posedge clk) if(rst) count<=0; else if(enable) count<=count+1; endmodule"
    ask = Mock(return_value=source)
    monkeypatch.setattr(trial.client, "ask", ask)
    sim = Mock(side_effect=[
        (failure != "simulation", "TEST FAILED" if failure == "simulation" else "", FailureKind.DESIGN),
        (False, "license unavailable" if failure == "mutant_infra" else "Testbench failures:\nFAIL mismatch",
         FailureKind.INFRA if failure == "mutant_infra" else FailureKind.DESIGN),
        (failure == "async_mutant_pass", "Testbench failures:\nFAIL reset", FailureKind.DESIGN)])
    monkeypatch.setattr(trial.vivado, "xsim_run", sim)
    impl = Mock(return_value=(failure != "implementation", "", FailureKind.DESIGN))
    monkeypatch.setattr(trial.vivado, "run_synthesis", impl)
    monkeypatch.setattr(trial.vivado, "full_metrics", Mock(return_value=VivadoMetrics(
        lut_used=8, lut_total=20800, ff_used=8, ff_total=41600, wns_ns=1, whs_ns=0.1,
        timing_met=failure != "timing")))
    assert trial.main() == (0 if failure == "none" else 1)
    result = json.loads((out / "result.json").read_text())
    assert result["passed"] is (failure == "none")
    assert len(result["source_sha256"]) == 64
    ask.assert_called_once()
    if failure in ("simulation", "mutant_infra", "async_mutant_pass"):
        impl.assert_not_called()
