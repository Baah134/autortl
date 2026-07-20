from autortl.state import RunState


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
