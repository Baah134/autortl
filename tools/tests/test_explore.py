"""tools/explore.py builds per-entry run.py commands and never touches the history."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import explore  # noqa: E402

ROOT = HERE.parents[1]


def test_build_entry_command_carries_spec_tb_top_and_meta_iterations(tmp_path):
    cmd = explore.entry_command("PY", ROOT / "curriculum/tier2/sync_fifo_build", tmp_path / "o", model="m1")
    assert cmd[:3] == ["PY", "run.py", "build"]
    assert "--spec" in cmd and "--tb" in cmd and cmd[cmd.index("--top") + 1] == "sync_fifo"
    assert cmd[cmd.index("--iterations") + 1] == "2" and cmd[-2:] == ["--model", "m1"]
    assert "bench" not in cmd


def test_optimize_entry_command_uses_design_tb_and_top(tmp_path):
    cmd = explore.entry_command("PY", ROOT / "curriculum/tier2/fir8", tmp_path / "o")
    assert cmd[:3] == ["PY", "run.py", "optimize"]
    assert cmd[cmd.index("--top") + 1] == "fir8" and "--design" in cmd


def test_generate_golden_is_passed_when_meta_asks(tmp_path):
    cmd = explore.entry_command("PY", ROOT / "curriculum/tier4/crc16_stream_build", tmp_path / "o")
    assert "--generate-golden" in cmd


def test_an_existing_exploration_is_never_overwritten(tmp_path, monkeypatch):
    import pytest
    monkeypatch.setattr(explore, "ROOT", tmp_path)
    (tmp_path / "logs" / "x").mkdir(parents=True)
    with pytest.raises(SystemExit, match="never overwritten"):
        explore.main(["--tier", "2", "--name", "x"])
