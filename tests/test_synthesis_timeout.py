"""Synthesis timeout is a run setting a heavy entry can raise.

Taxonomy: fixed_synthesis_timeout_blocks_heavy_designs (explore-tier6-05: the AES-128
baseline passed its testbench, then synthesis passed the fixed 900 s twice).
"""
import json
import sys
from pathlib import Path

import pytest
import yaml

from autortl.config import RunConfig

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import explore  # noqa: E402


def test_default_keeps_the_old_fifteen_minutes_and_old_configs_load():
    assert RunConfig(mode="optimize").synthesis_timeout_minutes == 15.0
    saved = RunConfig(mode="optimize").to_dict()
    saved.pop("synthesis_timeout_minutes")  # a config.json written before the setting existed
    assert RunConfig.from_dict(json.loads(json.dumps(saved))).synthesis_timeout_minutes == 15.0


@pytest.mark.parametrize("value", [0, 0.5, 241, float("nan"), "45"])
def test_out_of_range_timeouts_are_refused(value):
    with pytest.raises(ValueError, match="synthesis_timeout_minutes"):
        RunConfig(mode="optimize", synthesis_timeout_minutes=value).validate()


def test_run_py_flag_reaches_the_config(monkeypatch):
    import run
    seen = {}
    class Stop(Exception):
        pass
    def fake_orchestrator(cfg, run_dir=None):
        seen["cfg"] = cfg
        raise Stop
    monkeypatch.setattr(run, "Orchestrator", fake_orchestrator)
    with pytest.raises(Stop):
        run.main(["optimize", "--design", "d.v", "--tb", "t.v", "--top", "m",
                  "--synthesis-timeout-minutes", "45"])
    assert seen["cfg"].synthesis_timeout_minutes == 45.0


def test_explore_passes_the_entry_timeout_and_budgets():
    entry = ROOT / "curriculum/tier6/aes128_core_build"
    cmd = explore.entry_command("PY", entry, Path("out"))
    assert cmd[cmd.index("--synthesis-timeout-minutes") + 1] == "45"
    assert cmd[cmd.index("--max-vivado-minutes") + 1] == "150"
    assert cmd[cmd.index("--max-wall-minutes") + 1] == "240"
    assert cmd[cmd.index("--max-llm-calls") + 1] == str(explore.BUDGETS["model_calls"])  # not raised


def test_entries_without_the_setting_keep_the_defaults():
    cmd = explore.entry_command("PY", ROOT / "curriculum/tier6/cordic_build", Path("out"))
    assert "--synthesis-timeout-minutes" not in cmd
    assert cmd[cmd.index("--max-vivado-minutes") + 1] == str(explore.BUDGETS["tool_minutes"])


def test_runner_validates_and_records_the_entry_timeout(tmp_path):
    from curriculum import runner
    meta = yaml.safe_load((ROOT / "curriculum/tier6/aes128_core_build/meta.yaml").read_text(encoding="utf-8"))
    assert meta["synthesis_timeout_minutes"] == 45
    bad = tmp_path / "bad_entry"
    bad.mkdir()
    (bad / "meta.yaml").write_text("mode: build\nspec: s.json\nsynthesis_timeout_minutes: 0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="synthesis_timeout_minutes"):
        runner._metadata(bad)
