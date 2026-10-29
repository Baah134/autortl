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


def _load_cli():
    path = Path(__file__).resolve().parents[1] / "scripts/check_counter_cli.py"
    spec = importlib.util.spec_from_file_location("counter_cli", path)
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    return cli, path


def test_counter_cli_prefers_bat_and_falls_back_to_bare_tool_names(tmp_path):
    cli, _ = _load_cli()
    assert cli.tool_path(tmp_path, "xsim") == str(tmp_path.resolve() / "xsim.bat")
    (tmp_path / "xsim").write_text("")
    assert cli.tool_path(tmp_path, "xsim") == str(tmp_path.resolve() / "xsim")
    (tmp_path / "xsim.bat").write_text("")
    assert cli.tool_path(tmp_path, "xsim") == str(tmp_path.resolve() / "xsim.bat")


def test_counter_cli_bin_dir_defaults_to_the_environment(tmp_path, monkeypatch):
    cli, path = _load_cli()
    monkeypatch.setenv("AUTORTL_VIVADO_BIN", str(tmp_path))
    monkeypatch.setattr("sys.argv", [str(path), "--output", str(tmp_path / "evidence")])
    seen = []
    def stop(files, tb, top, cfg, work, **kwargs):
        seen.append(cfg.xsim_bin)
        return False, "stopped", FailureKind.DESIGN
    monkeypatch.setattr(cli, "xsim_run", stop)
    assert cli.main() == 1
    assert seen == [str(tmp_path.resolve() / "xsim.bat")]


def test_counter_cli_requires_a_bin_dir_without_the_environment(tmp_path, monkeypatch):
    cli, path = _load_cli()
    monkeypatch.delenv("AUTORTL_VIVADO_BIN", raising=False)
    monkeypatch.setattr("sys.argv", [str(path), "--output", str(tmp_path / "evidence")])
    with pytest.raises(SystemExit):
        cli.main()
