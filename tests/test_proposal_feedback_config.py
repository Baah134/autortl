"""Frozen experimental proposal-context configuration and CLI boundaries."""
from unittest.mock import Mock

import pytest

from autortl.config import RunConfig
import run


@pytest.mark.parametrize("mode", ["build", "optimize"])
def test_new_runs_disable_proposal_feedback(mode):
    config = RunConfig(mode=mode)
    assert config.proposal_feedback is False
    assert config.to_dict()["proposal_feedback"] is False


@pytest.mark.parametrize("mode", ["build", "optimize"])
def test_api_explicitly_enables_proposal_feedback(mode):
    config = RunConfig(mode=mode, proposal_feedback=True)
    config.validate()
    assert config.proposal_feedback is True
    assert config.to_dict()["proposal_feedback"] is True


@pytest.mark.parametrize("enabled", [False, True])
def test_proposal_feedback_roundtrip(enabled, tmp_path):
    config = RunConfig(mode="build", proposal_feedback=enabled, work_dir=tmp_path)
    path = tmp_path / "config.json"
    config.save(path)
    loaded = RunConfig.load(path)
    assert loaded.proposal_feedback is enabled
    assert loaded.to_dict() == config.to_dict()


def test_old_saved_run_preserves_disabled_feedback():
    data = RunConfig(mode="build").to_dict()
    del data["proposal_feedback"]
    assert RunConfig.from_dict(data).proposal_feedback is False
    del data["generate_golden"]
    assert RunConfig.from_dict(data).proposal_feedback is False
    assert RunConfig.from_dict(data).generate_golden is False
    del data["target_part"]
    with pytest.raises(ValueError, match="target_part"):
        RunConfig.from_dict(data)


@pytest.mark.parametrize("value", [None, 0, 1, "true", "false", [], {}])
@pytest.mark.parametrize("saved", [False, True])
def test_proposal_feedback_requires_strict_boolean(value, saved):
    with pytest.raises(ValueError, match="proposal_feedback must be boolean"):
        if saved:
            data = RunConfig(mode="build").to_dict()
            data["proposal_feedback"] = value
            RunConfig.from_dict(data)
        else:
            RunConfig(mode="build", proposal_feedback=value).validate()


@pytest.mark.parametrize("command", [
    ["build", "--spec", "s.json"],
    ["optimize", "--design", "m.v", "--top", "m"],
])
@pytest.mark.parametrize("extra,enabled", [
    ([], False),
    (["--proposal-feedback"], True),
    (["--no-proposal-feedback"], False),
])
def test_new_run_cli_feedback_choice(monkeypatch, command, extra, enabled):
    orchestrator = Mock()
    orchestrator.return_value.run.return_value = {"status": "done"}
    monkeypatch.setattr(run, "Orchestrator", orchestrator)
    assert run.main([*command, *extra]) == 0
    assert orchestrator.call_args.args[0].proposal_feedback is enabled


@pytest.mark.parametrize("extra,expected", [
    ([], {}),
    (["--proposal-feedback"], {"proposal_feedback": True}),
    (["--no-proposal-feedback"], {"proposal_feedback": False}),
])
def test_bench_only_forwards_explicit_feedback_choice(monkeypatch, extra, expected):
    from curriculum import runner
    bench = Mock(return_value=0)
    monkeypatch.setattr(runner, "run_tier", bench)
    assert run.main(["bench", "--tier", "0", *extra]) == 0
    bench.assert_called_once_with(0, **expected)


@pytest.mark.parametrize("command", ["build", "optimize", "bench"])
def test_feedback_help_labels_experiment_and_retained_audit(capsys, command):
    with pytest.raises(SystemExit) as exc:
        run.main([command, "--help"])
    assert exc.value.code == 0
    help_text = " ".join(capsys.readouterr().out.split())
    assert "--proposal-feedback" in help_text
    assert "--no-proposal-feedback" in help_text
    assert "experimental prior-proposal context" in help_text
    assert "default: off" in help_text
    assert "bounded proposal journal audit is always retained" in help_text


@pytest.mark.parametrize("enabled", [False, True])
def test_resume_retains_frozen_feedback_choice(monkeypatch, tmp_path, enabled):
    config = RunConfig(mode="build", work_dir=tmp_path, proposal_feedback=enabled)
    config.save(tmp_path / "config.json")
    orchestrator = Mock()
    orchestrator.return_value.run.return_value = {"status": "done"}
    monkeypatch.setattr(run, "Orchestrator", orchestrator)
    assert run.main(["resume", "--run", str(tmp_path)]) == 0
    assert orchestrator.call_args.args[0].proposal_feedback is enabled
    orchestrator.reset_mock()
    for flag in ("--proposal-feedback", "--no-proposal-feedback"):
        with pytest.raises(SystemExit) as exc:
            run.main(["resume", "--run", str(tmp_path), flag])
        assert exc.value.code == 2
        orchestrator.assert_not_called()


def test_resume_old_config_keeps_feedback_disabled(monkeypatch, tmp_path):
    import json
    data = RunConfig(mode="build", work_dir=tmp_path).to_dict()
    del data["proposal_feedback"]
    (tmp_path / "config.json").write_text(json.dumps(data), encoding="utf-8")
    orchestrator = Mock()
    orchestrator.return_value.run.return_value = {"status": "done"}
    monkeypatch.setattr(run, "Orchestrator", orchestrator)
    assert run.main(["resume", "--run", str(tmp_path)]) == 0
    assert orchestrator.call_args.args[0].proposal_feedback is False
