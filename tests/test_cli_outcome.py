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
