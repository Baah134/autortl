"""The tier0 gate runner keeps campaign14's source selection, budgets and command."""
import json
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import tier0_gate as gate  # noqa: E402


def test_identity_selection(tmp_path):
    for rel in ("autortl/a.py", "autortl/sub/b.v", "tests/t.py", "data/x.yaml", ".claude/skills/s.md",
                "curriculum/c.json", "llm/l.sv", "scripts/s.py", "run.py"):
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rel)
    for rel in ("autortl/__pycache__/a.cpython-312.pyc", "autortl/__pycache__/a.py", "autortl/notes.txt",
                "tools/gate.py", "evidence/e.json", "hardware/h.v"):
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rel)
    found = gate.identities(tmp_path)
    assert sorted(found) == sorted(["autortl/a.py", "autortl/sub/b.v", "tests/t.py", "data/x.yaml",
                                    ".claude/skills/s.md", "curriculum/c.json", "llm/l.sv", "scripts/s.py", "run.py"])
    assert found["run.py"] == gate.sha(tmp_path / "run.py")


def test_this_runner_is_outside_the_identity():
    # Writing or editing the gate must not change what it freezes.
    assert "tools" not in gate.SELECTION


def test_bench_command_matches_campaign14(tmp_path, monkeypatch):
    # campaign14's budgets; no --target-freq-mhz (gate_frequency_overrides_entry_meta):
    # both tier0 entries already ran at 100 MHz (meta 100.0, else the default).
    monkeypatch.delenv("AUTORTL_VIVADO_BIN", raising=False)
    out = tmp_path / "run"
    command = gate.bench_command("PY", out)
    assert command == ["PY", "run.py", "bench", "--tier", "0", "--iterations", "1", "--best-of-n", "1",
                       "--max-llm-calls", "16", "--max-vivado-minutes", "20", "--max-wall-minutes", "30",
                       "--max-infra-retries", "1", "--target-part", "xc7a35tcpg236-1",
                       "--output-dir", str(out),
                       "--vivado", "C:/AMDDesignTools/2025.2/Vivado/bin/vivado.bat",
                       "--xvlog", "C:/AMDDesignTools/2025.2/Vivado/bin/xvlog.bat",
                       "--xelab", "C:/AMDDesignTools/2025.2/Vivado/bin/xelab.bat",
                       "--xsim", "C:/AMDDesignTools/2025.2/Vivado/bin/xsim.bat"]


def test_bench_command_takes_the_vivado_folder_from_the_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTORTL_VIVADO_BIN", r"D:\Xilinx\Vivado\bin")
    command = gate.bench_command("PY", tmp_path / "run")
    assert command[-8:] == ["--vivado", "D:/Xilinx/Vivado/bin/vivado.bat", "--xvlog", "D:/Xilinx/Vivado/bin/xvlog.bat",
                            "--xelab", "D:/Xilinx/Vivado/bin/xelab.bat", "--xsim", "D:/Xilinx/Vivado/bin/xsim.bat"]


def test_the_vivado_bin_option_overrides_the_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTORTL_VIVADO_BIN", "D:/ignored")
    command = gate.bench_command("PY", tmp_path / "run", vivado="E:/Vivado/bin/")
    assert command[-8:] == ["--vivado", "E:/Vivado/bin/vivado.bat", "--xvlog", "E:/Vivado/bin/xvlog.bat",
                            "--xelab", "E:/Vivado/bin/xelab.bat", "--xsim", "E:/Vivado/bin/xsim.bat"]


def test_main_passes_the_vivado_bin_option_to_the_bench(tmp_path, monkeypatch):
    # Stop main right after it builds the command, before any process starts.
    seen = []
    def stop(python, out, tier=0, model=None, jobs=1, vivado=None):
        seen.append(vivado)
        raise SystemExit("stopped")
    monkeypatch.setattr(gate, "ROOT", tmp_path)
    monkeypatch.setattr(gate, "identities", lambda root=None: {})
    monkeypatch.setattr(gate, "bench_command", stop)
    monkeypatch.setattr(gate.subprocess, "run", lambda *a, **k: type("R", (), {"returncode": 0, "stdout": "1 passed"})())
    monkeypatch.syspath_prepend(str(gate.Path(gate.__file__).resolve().parents[1]))
    import curriculum.runner
    monkeypatch.setattr(curriculum.runner, "_history", lambda: [])
    (tmp_path / "logs").mkdir()
    with pytest.raises(SystemExit, match="stopped"):
        gate.main(["--name", "gate-02", "--vivado-bin", "E:/Vivado/bin"])
    assert seen == ["E:/Vivado/bin"]


def test_an_earlier_attempt_is_never_overwritten(tmp_path, monkeypatch):
    monkeypatch.setattr(gate, "ROOT", tmp_path)
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "gate-01-prelaunch.json").write_text("{}")
    with pytest.raises(SystemExit, match="never overwritten"):
        gate.main(["--name", "gate-01"])


def test_tier1_command_leaves_iterations_to_each_entry(tmp_path):
    out = tmp_path / "run"
    command = gate.bench_command("PY", out, tier=1)
    assert command[:5] == ["PY", "run.py", "bench", "--tier", "1"]
    assert "--iterations" not in command
    flags = dict(zip(command[5:19:2], command[6:20:2]))
    assert flags == {"--best-of-n": "1", "--max-llm-calls": "30", "--max-vivado-minutes": "40",
                     "--max-wall-minutes": "60", "--max-infra-retries": "1", "--target-part": "xc7a35tcpg236-1",
                     "--output-dir": str(out)}
    assert command[19] == "--vivado"


def test_tier0_command_is_unchanged_by_the_tier_option(tmp_path):
    assert gate.bench_command("PY", tmp_path, tier=0) == gate.bench_command("PY", tmp_path)


def test_a_held_higher_tier_blocks_the_gate(tmp_path, monkeypatch):
    import curriculum.runner as runner
    monkeypatch.setattr(gate, "ROOT", tmp_path)
    (tmp_path / "logs").mkdir()
    current = gate.sha(runner.__file__)
    monkeypatch.setattr(runner, "_history", lambda: [{"tier": 2, "held": True, "full_tier": True,
                                                      "runtime_identity": {"governance_sha256": current}}])
    with pytest.raises(SystemExit, match="higher held tier"):
        gate.main(["--name", "gate-02", "--tier", "1"])


def test_a_hold_under_old_governance_does_not_block():
    # held_under_old_governance_blocks: sign-off pass 2 changed runner.py, so pass 1's
    # tier 1 hold belongs to another cohort.
    old = {"tier": 1, "held": True, "full_tier": True, "runtime_identity": {"governance_sha256": "old"}}
    assert gate.held_higher_tiers([old], 0, "new") == []
    assert gate.held_higher_tiers([old], 0, "old") == [1]
    assert gate.held_higher_tiers([old], 0) == [1]  # no governance given: as before


def test_a_hold_on_other_implementation_files_does_not_block(tmp_path):
    # held_under_old_runtime_blocks: a taxonomy edit changed the runtime after pass 3's tier 1 hold.
    run = tmp_path / "campaign" / "entry"
    run.mkdir(parents=True)
    (run / "runtime.json").write_text(json.dumps({"implementation": {"data/taxonomy.yaml": "old"}}), encoding="utf-8")
    held = {"tier": 1, "held": True, "full_tier": True, "runtime_identity": {"governance_sha256": "g"},
            "results": [{"evidence_dir": str(run)}]}
    assert gate.held_higher_tiers([held], 0, "g", {"data/taxonomy.yaml": "new"}) == []
    assert gate.held_higher_tiers([held], 0, "g", {"data/taxonomy.yaml": "old"}) == [1]
    unreadable = dict(held, results=[{"evidence_dir": str(tmp_path / "gone")}])
    assert gate.held_higher_tiers([unreadable], 0, "g", {"data/taxonomy.yaml": "new"}) == [1]  # still blocks


def test_implementation_hashes_cover_the_files_a_run_freezes():
    hashes = gate.implementation_hashes()
    assert "autortl/fsm.py" in hashes and "data/taxonomy.yaml" in hashes and "llm/client.py" in hashes
    assert not any(name.startswith(("tools/", "curriculum/")) for name in hashes)


def test_a_pinned_model_is_passed_to_the_bench(tmp_path):
    command = gate.bench_command("PY", tmp_path, tier=0, model="gpt-6-luna")
    assert command[-2:] == ["--model", "gpt-6-luna"]
    assert command[:-2] == gate.bench_command("PY", tmp_path)


def test_jobs_are_passed_only_when_parallel(tmp_path):
    assert "--jobs" not in gate.bench_command("PY", tmp_path, tier=1)
    assert gate.bench_command("PY", tmp_path, tier=1, jobs=4)[-2:] == ["--jobs", "4"]


@pytest.mark.parametrize("jobs", ["0", "-2", "two"])
def test_jobs_below_one_is_a_usage_error_before_anything_runs(tmp_path, monkeypatch, capsys, jobs):
    # gate_jobs_zero_silently_serial: previously --jobs 0 quietly ran one entry at a time.
    monkeypatch.setattr(gate, "ROOT", tmp_path)
    with pytest.raises(SystemExit) as exit_info:
        gate.main(["--name", "gate-03", "--jobs", jobs])
    assert exit_info.value.code == 2 and "--jobs" in capsys.readouterr().err
    assert not (tmp_path / "logs").exists()


def test_agent_worktrees_are_not_part_of_the_identity(tmp_path):
    for rel in ("run.py", ".claude/skills/s/SKILL.md", ".claude/worktrees/agent-1/autortl/fsm.py"):
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rel)
    assert sorted(gate.identities(tmp_path)) == [".claude/skills/s/SKILL.md", "run.py"]


def test_a_failing_doctor_stops_the_gate_before_any_freeze(tmp_path, monkeypatch):
    monkeypatch.setattr(gate, "ROOT", tmp_path)
    from curriculum import runner
    monkeypatch.setattr(runner, "_history", lambda: [])  # independent of the real curriculum history
    (tmp_path / "logs").mkdir()
    calls = []
    def run(cmd, **kwargs):
        calls.append(cmd)
        return type("R", (), {"returncode": 1, "stdout": "MISSING codex"})()
    monkeypatch.setattr(gate.subprocess, "run", run)
    with pytest.raises(SystemExit, match="environment not ready"):
        gate.main(["--name", "gate-03"])
    assert calls and "doctor" in calls[0]
    assert not (tmp_path / "logs" / "gate-03-source-freeze.json").exists()


def test_tier0_and_tier1_budgets_are_unchanged():
    # Their existing cohorts were measured with exactly these per-entry budgets.
    assert gate.TIER_BUDGETS[0] is gate.BUDGETS
    assert gate.TIER_BUDGETS[0] == {"iterations": 1, "best_of_n": 1, "model_calls": 16, "tool_minutes": 20,
                                    "wall_minutes": 30, "infra_retries": 1}
    assert gate.TIER_BUDGETS[1] == {"iterations": None, "best_of_n": 1, "model_calls": 30, "tool_minutes": 40,
                                    "wall_minutes": 60, "infra_retries": 1}


def test_tiers_two_to_six_take_the_tier1_budgets():
    # gate_limited_to_tiers_zero_and_one
    assert sorted(gate.TIER_BUDGETS) == [0, 1, 2, 3, 4, 5, 6]
    for tier in range(2, 7):
        assert gate.TIER_BUDGETS[tier] == gate.TIER_BUDGETS[1]
        assert gate.TIER_BUDGETS[tier] is not gate.TIER_BUDGETS[1]


@pytest.mark.parametrize("tier", [2, 3, 4, 5, 6])
def test_tiers_two_to_six_bench_command_passes_no_global_frequency(tmp_path, monkeypatch, tier):
    # gate_frequency_overrides_entry_meta: fir8 and fir16_sym_build run at their meta 150 MHz.
    monkeypatch.delenv("AUTORTL_VIVADO_BIN", raising=False)
    out = tmp_path / "run"
    command = gate.bench_command("PY", out, tier=tier)
    assert command[:5] == ["PY", "run.py", "bench", "--tier", str(tier)]
    assert "--target-freq-mhz" not in command and "--target_freq_mhz" not in command
    assert "--iterations" not in command  # each entry's meta.yaml
    assert command[5:] == gate.bench_command("PY", out, tier=1)[5:]


def test_explore_defaults_are_the_gate_budgets_for_tiers_one_to_six():
    import explore
    for tier in range(1, 7):
        budgets = dict(gate.TIER_BUDGETS[tier])
        assert budgets.pop("iterations") is None
        assert budgets == explore.BUDGETS


@pytest.mark.parametrize("tier", [2, 6])
def test_main_accepts_the_higher_tiers(tmp_path, monkeypatch, tier):
    seen = []
    def stop(python, out, tier=0, model=None, jobs=1, vivado=None):
        seen.append(tier)
        raise SystemExit("stopped")
    monkeypatch.setattr(gate, "ROOT", tmp_path)
    monkeypatch.setattr(gate, "identities", lambda root=None: {})
    monkeypatch.setattr(gate, "bench_command", stop)
    monkeypatch.setattr(gate.subprocess, "run", lambda *a, **k: type("R", (), {"returncode": 0, "stdout": "1 passed"})())
    monkeypatch.syspath_prepend(str(gate.Path(gate.__file__).resolve().parents[1]))
    import curriculum.runner
    monkeypatch.setattr(curriculum.runner, "_history", lambda: [])
    (tmp_path / "logs").mkdir()
    with pytest.raises(SystemExit, match="stopped"):
        gate.main(["--name", "gate-04", "--tier", str(tier)])
    assert seen == [tier]


def test_tier7_is_a_usage_error(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(gate, "ROOT", tmp_path)
    with pytest.raises(SystemExit) as exit_info:
        gate.main(["--name", "gate-05", "--tier", "7"])
    assert exit_info.value.code == 2 and "--tier" in capsys.readouterr().err


def record(tier, held, full_tier=True):
    return {"tier": tier, "held": held, "full_tier": full_tier}


def test_bottom_up_sign_off_pass_is_never_blocked():
    # Tiers 0 to k-1 are held when tier k is gated, and tier k may be gated again.
    history = []
    for tier in range(7):
        for streak in (1, 2, 3):
            assert gate.held_higher_tiers(history, tier) == []
            history.append(record(tier, streak == 3))
    for tier in range(6):
        assert gate.held_higher_tiers(history, tier) == list(range(tier + 1, 7))


def test_held_is_the_latest_full_tier_state():
    # stale_held_record_blocks_lower_gates: held, then re-gated on a changed harness.
    history = [record(3, True), record(3, False)]
    assert gate.held_higher_tiers(history, 0) == []
    # A subset run never releases a held tier.
    assert gate.held_higher_tiers([record(3, True), record(3, False, full_tier=False)], 0) == [3]
    # Lower or equal tiers never block.
    assert gate.held_higher_tiers([record(0, True), record(2, True)], 2) == []


def test_entry_settings_name_each_entry_s_own_frequency_and_budgets():
    tier2 = gate.entry_settings(2)
    assert tier2["fir8"] == {"target_freq_mhz": 150.0, "max_vivado_minutes": 70.0, "max_wall_minutes": 110.0}
    assert tier2["sync_fifo_build"] == {"target_freq_mhz": 100.0}
    assert gate.entry_settings(5)["fir16_sym_build"] == {"target_freq_mhz": 150.0, "max_vivado_minutes": 100.0,
                                                         "max_wall_minutes": 160.0}
    tier6 = gate.entry_settings(6)
    assert tier6["aes128_core_build"] == {"target_freq_mhz": 100.0, "max_vivado_minutes": 150.0,
                                          "max_wall_minutes": 240.0}
    assert tier6["rv32i_core_build"] == {"target_freq_mhz": 100.0, "max_vivado_minutes": 180.0,
                                         "max_wall_minutes": 300.0}
    assert tier6["cordic_build"] == {"target_freq_mhz": 100.0}
    # Tier 0 and tier 1 declare nothing but 100 MHz, so dropping the gate's
    # --target-freq-mhz 100 leaves their effective configuration unchanged.
    for tier in (0, 1):
        for settings in gate.entry_settings(tier).values():
            assert settings in ({}, {"target_freq_mhz": 100.0})
