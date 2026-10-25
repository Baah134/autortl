from pathlib import Path
from unittest.mock import Mock
import pytest

from autortl.config import RunConfig
import run


def test_config_roundtrip_absolute_paths(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = RunConfig(mode="build", spec_path=Path("spec.json"), work_dir=Path("run"),
                    max_llm_calls=7, vivado_bin="custom-vivado")
    path = tmp_path / "config.json"
    cfg.save(path)
    loaded = RunConfig.load(path)
    assert loaded.spec_path == tmp_path / "spec.json"
    assert loaded.work_dir == tmp_path / "run"
    assert loaded.max_llm_calls == 7 and loaded.vivado_bin == "custom-vivado"
    assert loaded.to_dict() == cfg.to_dict()


@pytest.mark.parametrize("mutation", ["version", "missing", "relative", "unknown"])
def test_invalid_saved_config_rejected(mutation):
    data = RunConfig(mode="optimize").to_dict()
    if mutation == "version":
        data["schema_version"] = 999
    elif mutation == "missing":
        del data["target_part"]
    elif mutation == "relative":
        data["design_path"] = "relative.v"
    else:
        data["surprise"] = True
    with pytest.raises(ValueError):
        RunConfig.from_dict(data)


@pytest.fixture
def orchestrator(monkeypatch):
    cls = Mock()
    cls.return_value.run.return_value = {"status": "done"}
    monkeypatch.setattr(run, "Orchestrator", cls)
    return cls


def test_cli_resume_loads_saved_config_without_defaults(tmp_path, orchestrator):
    cfg = RunConfig(mode="build", spec_path=tmp_path / "spec.json", max_llm_calls=7,
                    target_freq_mhz=123, work_dir=tmp_path)
    cfg.save(tmp_path / "config.json")
    assert run.main(["resume", "--run", str(tmp_path)]) == 0
    restored = orchestrator.call_args.args[0]
    assert restored.to_dict() == cfg.to_dict()
    assert orchestrator.call_args.kwargs["run_dir"] == tmp_path


def test_cli_resume_missing_config_fails_before_run(tmp_path, orchestrator):
    with pytest.raises(SystemExit):
        run.main(["resume", "--run", str(tmp_path)])
    orchestrator.assert_not_called()


def test_cli_resume_rejects_override_flags(tmp_path, orchestrator):
    with pytest.raises(SystemExit):
        run.main(["resume", "--run", str(tmp_path), "--iterations", "99"])
    orchestrator.assert_not_called()


def test_cli_output_and_budget_options(tmp_path, orchestrator):
    result = run.main(["optimize", "--design", "d.v", "--top", "d",
                      "--output-dir", str(tmp_path), "--max-llm-calls", "9",
                      "--max-vivado-minutes", "12", "--max-wall-minutes", "15"])
    assert result == 0
    cfg = orchestrator.call_args.args[0]
    assert (cfg.max_llm_calls, cfg.max_vivado_minutes, cfg.max_wall_minutes) == (9, 12, 15)
    assert orchestrator.call_args.kwargs["run_dir"] == tmp_path


def test_stale_route_is_rejected(orchestrator):
    with pytest.raises(SystemExit):
        run.main(["build", "--spec", "s.json", "--route", "generator=claude_code.sonnet"])
    orchestrator.assert_not_called()


def test_cli_failure_returns_nonzero(orchestrator):
    orchestrator.return_value.run.return_value = {"status": "blocked"}
    assert run.main(["build", "--spec", "s.json"]) == 1


def test_bench_forwards_only_explicit_overrides(monkeypatch, tmp_path):
    from curriculum import runner
    bench = Mock(return_value=0)
    monkeypatch.setattr(runner, "run_tier", bench)
    assert run.main(["bench", "--tier", "0", "--entries", "counter",
                     "--output-dir", str(tmp_path), "--max-llm-calls", "3"]) == 0
    bench.assert_called_once_with(0, entries=["counter"], output_root=tmp_path, max_llm_calls=3)


def test_config_missing_infra_retry_field_fails_explicitly():
    data = RunConfig(mode="build").to_dict()
    del data["max_infra_retries"]
    with pytest.raises(ValueError, match="max_infra_retries"):
        RunConfig.from_dict(data)


@pytest.mark.parametrize("name,value", [
    ("max_wall_minutes", float("nan")), ("target_freq_mhz", float("inf")),
    ("max_llm_calls", True), ("max_infra_retries", -1), ("best_of_n", 0),
    ("max_fix_attempts", 1.5), ("parallel_candidates", "false"),
    ("objective", "unknown"), ("work_dir", None), ("vivado_bin", ""),
])
def test_saved_config_invalid_values_rejected(name, value):
    data = RunConfig(mode="build").to_dict()
    data[name] = value
    with pytest.raises(ValueError):
        RunConfig.from_dict(data)


def test_build_cli_integration_testbench_and_infra_retry(tmp_path, orchestrator):
    run.main(["build", "--spec", "s.json", "--tb", "tb.v", "--top", "top",
              "--work-dir", str(tmp_path), "--max-infra-retries", "4"])
    cfg = orchestrator.call_args.args[0]
    assert cfg.testbench_path == Path("tb.v") and cfg.top_module == "top"
    assert cfg.max_infra_retries == 4
    assert orchestrator.call_args.kwargs["run_dir"] == tmp_path


@pytest.mark.parametrize("flag,value", [("--max-wall-minutes", "nan"),
    ("--target-freq-mhz", "inf"), ("--max-infra-retries", "-1")])
def test_cli_invalid_numbers_fail_before_orchestration(flag, value, orchestrator):
    with pytest.raises(SystemExit):
        run.main(["build", "--spec", "s.json", flag, value])
    orchestrator.assert_not_called()


def test_config_atomic_save_failure_preserves_previous(monkeypatch, tmp_path):
    from autortl import state
    path = tmp_path / "config.json"
    config = RunConfig(mode="build", max_llm_calls=7)
    config.save(path)
    def fail(*args):
        raise OSError("interrupted")
    monkeypatch.setattr(state.os, "replace", fail)
    config.max_llm_calls = 99
    with pytest.raises(OSError):
        config.save(path)
    assert RunConfig.load(path).max_llm_calls == 7
