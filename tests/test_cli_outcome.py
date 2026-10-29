"""Completed experiment output must expose physical feasibility explicitly."""
import json
from unittest.mock import Mock
import pytest
import run


@pytest.mark.parametrize("closed,kind", [(False,None),(True,"timing_recovery"),(True,"objective")])
def test_cli_prints_timing_closure_separately_from_completed_status(tmp_path, monkeypatch, capsys, closed, kind):
    summary={"status":"done","best_iteration":1 if closed else 0,"timing_closed":closed,"improvement_kind":kind,"run_dir":str(tmp_path)}
    monkeypatch.setattr(run,"Orchestrator",Mock(return_value=Mock(run=Mock(return_value=summary))))
    assert run.main(["build","--spec",str(tmp_path/"spec.json"),"--output-dir",str(tmp_path/"trial")])==0
    assert json.loads(capsys.readouterr().out)==summary


def test_locked_checkpoint_is_an_infrastructure_stop_not_a_traceback(tmp_path, monkeypatch, capsys):
    # taxonomy: checkpoint_replace_denied. The last checkpoint is intact, so the run resumes.
    from autortl.state import CheckpointLockedError
    locked = CheckpointLockedError(13, "checkpoint events.jsonl stayed locked; run `run.py resume`", "events.jsonl")
    orchestrator = Mock(run=Mock(side_effect=locked))
    orchestrator.state.run_dir = tmp_path / "trial"
    monkeypatch.setattr(run, "Orchestrator", Mock(return_value=orchestrator))
    assert run.main(["build", "--spec", str(tmp_path / "spec.json"), "--output-dir", str(tmp_path / "trial")]) == 3
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "infra_blocked" and "resume" in out["error"] and out["run_dir"] == str(tmp_path / "trial")
