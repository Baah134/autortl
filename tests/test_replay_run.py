"""tools/replay_run.py: a recorded run replays offline and rebuilds the same files."""
import hashlib
import json
from pathlib import Path

import pytest

from autortl import fsm, state
from tests.helpers import load_module
from tests.test_fsm_resume import WINNER, configuration, install_models, install_tools

ROOT = Path(__file__).resolve().parents[1]
replay_run = load_module(ROOT / "tools" / "replay_run.py", "replay_run_under_test")


def record(tmp_path, monkeypatch, name="recorded_run_directory"):
    """A complete optimize run with controlled tools and models, as the harness journals it."""
    run = tmp_path / name
    o = fsm.Orchestrator(configuration(tmp_path), run)
    install_models(o)
    install_tools(monkeypatch)
    assert o.run()["status"] == "done"
    return run


def tree_digest(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(Path(root).rglob("*")) if p.is_file()}


def journal_entry(run, identity):
    return run / "journal" / hashlib.sha256(identity.encode()).hexdigest()


def test_unchanged_harness_replays_a_recorded_run_with_no_model_or_tool_call(tmp_path, monkeypatch):
    run = record(tmp_path, monkeypatch)
    before = tree_digest(run)
    report = replay_run.run_replay(run, tmp_path / "out")
    assert report["ok"], report
    assert report["status"] == "done" and report["refused_calls"] == []
    assert report["different"] == report["missing"] == report["extra"] == []
    assert {"m_best.v", "run_summary.json", "state.json", "designs.jsonl"} <= set(report["identical"])
    assert report["runtime_changed"] is False
    assert "events.jsonl" in report["live_only"]
    replayed = Path(report["replay_dir"])
    assert len(str(replayed)) == len(str(run.resolve()))
    assert (replayed / "m_best.v").read_text() == WINNER
    assert tree_digest(run) == before, "the recorded run must stay untouched"


def test_a_behaviour_change_in_the_harness_is_reported_as_a_difference(tmp_path, monkeypatch):
    run = record(tmp_path, monkeypatch)
    original = state.RunState.append_design

    def changed(self, entry):
        original(self, {**entry, "changed_by_refactor": True})
    monkeypatch.setattr(state.RunState, "append_design", changed)
    report = replay_run.run_replay(run, tmp_path / "out")
    assert not report["ok"]
    assert "designs.jsonl" in report["different"]
    assert "changed_by_refactor" in report["excerpts"]["designs.jsonl"]


def test_a_call_the_journal_does_not_hold_is_refused_and_fails_the_replay(tmp_path, monkeypatch):
    run = record(tmp_path, monkeypatch)
    entries = [p for p in (run / "journal").glob("*/completed.json")
               if json.loads(p.read_text())["stage"].endswith(":model:generator.generate:0")]
    assert entries
    for entry in entries:
        entry.unlink()
    report = replay_run.run_replay(run, tmp_path / "out")
    assert not report["ok"]
    assert report["refused_calls"] == ["autortl.roles.ask"]
    assert report["status"] == "replay_miss"


def test_a_journal_that_fails_its_own_hash_check_is_refused(tmp_path, monkeypatch):
    run = record(tmp_path, monkeypatch)
    artifact = next(p for p in (run / "journal").rglob("artifacts/*") if p.is_file())
    artifact.write_bytes(artifact.read_bytes() + b" sanitized")
    with pytest.raises(replay_run.ReplayError, match="hash check"):
        replay_run.run_replay(run, tmp_path / "out")


def test_main_exit_codes(tmp_path, monkeypatch, capsys):
    run = record(tmp_path, monkeypatch)
    assert replay_run.main(["--run", str(run), "--out", str(tmp_path / "out")]) == 0
    out = capsys.readouterr().out  # the harness prints its own DONE line first
    assert json.loads(out[out.index("\n{") + 1:])["ok"] is True
    assert replay_run.main(["--run", str(tmp_path), "--out", str(tmp_path / "out")]) == 2


def test_refuses_an_out_directory_too_long_for_a_same_length_path(tmp_path, monkeypatch):
    run = record(tmp_path, monkeypatch, name="r")
    with pytest.raises(replay_run.ReplayError, match="too long"):
        replay_run.prepare(run, tmp_path / "a_much_longer_parent_directory")


def test_never_deletes_a_directory_that_is_not_an_earlier_replay(tmp_path, monkeypatch):
    run = record(tmp_path, monkeypatch)
    target = replay_run.replay_dir(run, tmp_path / "out")
    target.mkdir(parents=True)
    (target / "keep.txt").write_text("not a replay")
    with pytest.raises(replay_run.ReplayError, match="not an earlier replay"):
        replay_run.prepare(run, tmp_path / "out")
    assert (target / "keep.txt").exists()


def test_refuses_a_moved_copy_whose_config_names_another_directory(tmp_path, monkeypatch):
    run = record(tmp_path, monkeypatch)
    moved = tmp_path / "moved_copy_of_the_recorded_run"
    import shutil
    shutil.copytree(run, moved)
    with pytest.raises(replay_run.ReplayError, match="moved copy"):
        replay_run.prepare(moved, tmp_path / "out")


def test_relocation_rebinds_every_digest_of_a_rewritten_file_to_a_fixed_point():
    old, new = "C:\\runs\\a", "D:\\other\\b"
    log = b"cwd C:\\runs\\a\\iter_000"
    receipt = json.dumps({"output_log_sha256": hashlib.sha256(log).hexdigest(),
                          "cwd": old}).encode()
    completion = json.dumps({"artifacts": {"r": hashlib.sha256(receipt).hexdigest()}}).encode()
    out = replay_run.relocate_all({"log": log, "receipt": receipt, "completion": completion},
                                  replay_run.path_forms(old, new))
    assert out["log"] == b"cwd D:\\other\\b\\iter_000"
    assert json.loads(out["receipt"]) == {"output_log_sha256": hashlib.sha256(out["log"]).hexdigest(),
                                          "cwd": new}
    assert json.loads(out["completion"])["artifacts"]["r"] == hashlib.sha256(out["receipt"]).hexdigest()


def test_relocation_rewrites_all_three_path_spellings():
    forms = replay_run.path_forms("C:\\r\\a", "C:\\s\\b")
    text = b'C:\\r\\a\\x "C:\\\\r\\\\a\\\\y" C:/r/a/z'
    assert replay_run.relocate(text, forms) == b'C:\\s\\b\\x "C:\\\\s\\\\b\\\\y" C:/s/b/z'


@pytest.mark.parametrize("recorded, replayed, equal", [
    ("ld/run_one/x.rpt tail", "ew/run_two/x.rpt tail", True),     # cut at the start of a preview
    ("head of C:/old/ru", "head of C:/new/ru", True),               # cut at the end of a preview
    ("C:/old/run_one/x LUT=17", "C:/new/run_two/x LUT=18", False),  # a real change stays a change
    ("C:/old/run_one/x", "C:/new/run_two/xx", False),               # lengths differ
])
def test_preview_cuts_through_the_run_path_are_equivalent_and_nothing_else(recorded, replayed, equal):
    forms = replay_run.path_forms("C:/old/run_one", "C:/new/run_two")
    assert replay_run._edge_equal(recorded, replayed, forms) is equal
