"""The simulated walkthrough runs the real Orchestrator with no model, Vivado or network."""
import json
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from autortl import fsm, roles

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import demo  # noqa: E402


def test_demo_runs_offline_and_labels_itself(tmp_path, capsys, monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("the demo must not reach a model, a process or the network")
    monkeypatch.setattr(roles, "ask", refuse)
    monkeypatch.setattr(subprocess, "run", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    originals = (fsm.vivado.xsim_run, fsm.vivado.run_synthesis, roles.ask, subprocess.Popen, socket.socket.connect)
    out = tmp_path / "demo"
    assert demo.main(["--output-dir", str(out)]) == 0
    text = capsys.readouterr().out
    assert text.startswith("SIMULATED WALKTHROUGH") and "measure nothing" in text
    for name in ("journal", "events.jsonl", "progress.md", "run_summary.json", "mux4_best.v"):
        assert (out / name).exists() and str(out / name) in text
    summary = json.loads((out / "run_summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "done" and summary["best_iteration"] == 1
    assert (out / "mux4_best.v").read_text(encoding="utf-8") == demo.CANDIDATE
    # The stand-ins are removed again afterwards.
    assert originals == (fsm.vivado.xsim_run, fsm.vivado.run_synthesis, roles.ask, subprocess.Popen,
                         socket.socket.connect)


def test_demo_refuses_a_used_folder(tmp_path):
    (tmp_path / "old.txt").write_text("earlier run")
    with pytest.raises(SystemExit, match="new or empty"):
        demo.run_demo(tmp_path)
