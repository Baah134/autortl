import importlib.util
import json
from pathlib import Path
from unittest.mock import Mock
import pytest
from autortl.report_parser import VivadoMetrics
from autortl.triage import FailureKind


@pytest.mark.parametrize("stage", ["simulation", "qualification", "implementation", "success"])
def test_counter_cli_evidence_and_fail_closed(tmp_path, monkeypatch, stage):
    path = Path(__file__).resolve().parents[1] / "scripts/check_counter_cli.py"
    spec = importlib.util.spec_from_file_location("counter_cli", path)
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    out = tmp_path / "evidence"
    monkeypatch.setattr("sys.argv", [str(path), "--bin-dir", str(tmp_path), "--output", str(out)])
    sim = Mock(return_value=(stage != "simulation", "", FailureKind.DESIGN))
    qual = Mock(return_value=(stage != "qualification", "verdict"))
    impl = Mock(return_value=(stage != "implementation", "", FailureKind.DESIGN))
    monkeypatch.setattr(cli, "xsim_run", sim)
    monkeypatch.setattr(cli, "qualify", qual)
    monkeypatch.setattr(cli, "run_synthesis", impl)
    monkeypatch.setattr(cli, "full_metrics", Mock(return_value=VivadoMetrics(
        sim_error="Simulation log not found", lut_total=20800, ff_total=41600,
        wns_ns=5.491, whs_ns=0.276)))
    assert cli.main() == (0 if stage == "success" else 1)
    result = json.loads((out / "result.json").read_text())
    assert result["passed"] is (stage == "success")
    assert len(result["source_sha256"]["counter.v"]) == 64
    if stage == "simulation":
        qual.assert_not_called()
    if stage in ("simulation", "qualification"):
        impl.assert_not_called()
    if stage == "success":
        assert result["metrics"]["sim_passed"]
        assert result["metrics"]["sim_error"] == ""
