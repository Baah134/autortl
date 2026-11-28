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


def test_out_of_context_implementation_is_passed_when_meta_asks(tmp_path):
    # chip_top_flow_for_soc_block: the AXI4-Lite slave is an SoC block.
    cmd = explore.entry_command("PY", ROOT / "curriculum/tier5/axil_regs_build", tmp_path / "o")
    assert cmd[cmd.index("--implementation") + 1] == "out_of_context"
    chip_top = explore.entry_command("PY", ROOT / "curriculum/tier2/sync_fifo_build", tmp_path / "o")
    assert "--implementation" not in chip_top  # run.py's default is chip_top


def test_an_existing_exploration_is_never_overwritten(tmp_path, monkeypatch):
    import pytest
    monkeypatch.setattr(explore, "ROOT", tmp_path)
    (tmp_path / "logs" / "x").mkdir(parents=True)
    with pytest.raises(SystemExit, match="never overwritten"):
        explore.main(["--tier", "2", "--name", "x"])


def test_a_failing_doctor_stops_the_exploration_before_any_entry(tmp_path, monkeypatch):
    import subprocess
    import pytest
    calls = []
    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 1, stdout="codex: missing", stderr="")
    monkeypatch.setattr(explore.subprocess, "run", fake_run)
    monkeypatch.setattr(explore, "ROOT", tmp_path)
    (tmp_path / "curriculum" / "tier9" / "e1").mkdir(parents=True)
    (tmp_path / "curriculum" / "tier9" / "e1" / "meta.yaml").write_text("mode: build\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="exploration was not started"):
        explore.main(["--tier", "9", "--name", "x", "--python", "PY"])
    assert len(calls) == 1 and calls[0][1:3] == ["run.py", "doctor"]
    assert not (tmp_path / "logs" / "x").exists()


def _entry(tmp_path, extra):
    entry = tmp_path / "e1"
    entry.mkdir()
    (entry / "spec.json").write_text("{}", encoding="utf-8")
    (entry / "meta.yaml").write_text("mode: build\nspec: spec.json\ntarget_freq_mhz: 150.0\n" + extra, encoding="utf-8")
    return entry


def test_entry_budgets_raise_or_lower_that_entry_only(tmp_path):
    # entry_budgets_ignored_by_bench: the key is `budgets`, as in a bench.
    cmd = explore.entry_command("PY", _entry(tmp_path, "budgets:\n  model_calls: 12\n  wall_minutes: 90\n"),
                                tmp_path / "o")
    assert cmd[cmd.index("--max-llm-calls") + 1] == "12"
    assert cmd[cmd.index("--max-wall-minutes") + 1] == "90"
    assert cmd[cmd.index("--max-vivado-minutes") + 1] == str(explore.BUDGETS["tool_minutes"])
    assert cmd[cmd.index("--target-freq-mhz") + 1] == "150.0"
    plain = explore.entry_command("PY", ROOT / "curriculum/tier2/sync_fifo_build", tmp_path / "o")
    assert plain[plain.index("--max-llm-calls") + 1] == str(explore.BUDGETS["model_calls"])


def test_the_old_explore_budgets_key_and_bad_budgets_are_refused(tmp_path):
    import pytest
    with pytest.raises(ValueError, match="renamed budgets"):
        explore.entry_command("PY", _entry(tmp_path, "explore_budgets:\n  tool_minutes: 90\n"), tmp_path / "o")
    other = tmp_path / "other"
    other.mkdir()
    with pytest.raises(ValueError, match="budgets may set only"):
        explore.entry_command("PY", _entry(other, "budgets:\n  best_of_n: 4\n"), tmp_path / "o")


def test_no_curriculum_entry_uses_the_old_key():
    for meta in (ROOT / "curriculum").glob("tier*/*/meta.yaml"):
        assert "explore_budgets" not in meta.read_text(encoding="utf-8"), meta


def test_jobs_zero_is_a_usage_error(tmp_path, monkeypatch, capsys):
    # backend_configuration_rough_edges, gate_jobs_zero_silently_serial
    import pytest
    monkeypatch.setattr(explore, "ROOT", tmp_path)
    with pytest.raises(SystemExit) as exit_info:
        explore.main(["--tier", "2", "--name", "y", "--jobs", "0"])
    assert exit_info.value.code == 2 and "--jobs" in capsys.readouterr().err
    assert not (tmp_path / "logs").exists()
