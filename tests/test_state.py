from autortl.state import RunState
from autortl import state
import pytest


def test_instruction_extraction(tmp_path):
    s = RunState(tmp_path)
    s.write_plan("# PLAN\n## Hypothesis\nblah\n"
                 "## Instruction for generator\nNarrow the comparators to 10 bits.\n")
    assert "Narrow the comparators" in s.extract_instruction()


def test_designs_roundtrip(tmp_path):
    s = RunState(tmp_path)
    s.append_design({"iteration": 1, "is_best": True, "lut_used": 48})
    s.append_design({"iteration": 2, "is_best": False, "lut_used": 60})
    d = s.read_designs()
    assert len(d) == 2 and d[0]["lut_used"] == 48


def test_fsm_resume_roundtrip(tmp_path):
    s = RunState(tmp_path)
    s.save_fsm({"phase": "GENERATING", "iteration": 4})
    assert s.load_fsm()["iteration"] == 4


def test_progress_tail(tmp_path):
    s = RunState(tmp_path)
    for i in range(5):
        s.append_progress(i, f"strategy {i}", "ACCEPT")
    tail = s.read_progress(tail_lines=4)
    assert "strategy 4" in tail


def test_atomic_failure_preserves_previous_checkpoint(monkeypatch, tmp_path):
    s = RunState(tmp_path)
    s.save_fsm({"phase": "old"})
    def fail(*args):
        raise OSError("interrupted replace")
    monkeypatch.setattr(state.os, "replace", fail)
    with pytest.raises(OSError):
        s.save_fsm({"phase": "new"})
    assert s.load_fsm() == {"phase": "old"}
    assert not list(tmp_path.glob("*.tmp"))


def test_design_history_idempotence_and_conflict(tmp_path):
    s = RunState(tmp_path)
    entry = {"iteration": 1, "metric": 20}
    s.append_design(entry)
    RunState(tmp_path).append_design(entry)
    assert s.read_designs() == [entry]
    with pytest.raises(ValueError, match="conflicting"):
        s.append_design({"iteration": 1, "metric": 30})
    assert s.read_designs() == [entry]


def test_progress_idempotent_by_iteration_outcome_or_id(tmp_path):
    s = RunState(tmp_path)
    s.append_progress(1, "first", "PASS")
    s.append_progress(1, "replayed", "PASS")
    s.append_progress(1, "second", "FAIL")
    s.append_progress(1, "explicit", "PASS", event_id="separate")
    assert s.read_progress().count("## [") == 3
    assert "replayed" not in s.read_progress()


def test_structured_events_immutable_and_idempotent(tmp_path):
    s = RunState(tmp_path)
    s.append_event({"stage": "sim", "outcome": "pass"}, event_id="sim-1")
    s.append_event({"stage": "sim", "outcome": "pass"}, event_id="sim-1")
    with pytest.raises(ValueError, match="conflicting"):
        s.append_event({"stage": "sim", "outcome": "fail"}, event_id="sim-1")
    assert len(s.read_events()) == 1


def test_corrupt_checkpoint_does_not_silently_reset(tmp_path):
    s = RunState(tmp_path)
    s.fsm_path.write_text('{"phase":')
    with pytest.raises(ValueError):
        s.load_fsm()
