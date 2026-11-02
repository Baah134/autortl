"""An entry's own meta.yaml frequency and budgets win over the bench's tier-wide values.

Taxonomy: gate_frequency_overrides_entry_meta (the gate's --target-freq-mhz 100 would
have run fir8 and fir16_sym_build, meta 150.0, at 100 MHz) and
entry_budgets_ignored_by_bench (meta budgets reached only tools/explore.py).
"""
import math
from pathlib import Path

import pytest
import yaml

from curriculum import runner
from tests.test_curriculum import curriculum, records  # noqa: F401  (fixture)

ROOT = Path(__file__).resolve().parents[1]


def _set_meta(root, name, **extra):
    path = root / "tier0" / name / "meta.yaml"
    meta = yaml.safe_load(path.read_text())
    meta.update(extra)
    path.write_text(yaml.safe_dump(meta))


def _configs(orch):
    return {call.kwargs["run_dir"].name: call.args[0] for call in orch.call_args_list}


def test_meta_frequency_and_budgets_win_over_bench_values_and_enter_the_cohort(curriculum, capsys):
    root, orch, output = curriculum
    _set_meta(root, "a", target_freq_mhz=150.0, budgets={"model_calls": 50, "tool_minutes": 150, "wall_minutes": 240})
    _set_meta(root, "b", budgets={"model_calls": 5})  # lowering is allowed too
    assert runner.run_tier(0, output_root=output, target_freq_mhz=100.0, max_llm_calls=30,
                           max_vivado_minutes=40.0, max_wall_minutes=60.0, max_iterations=1) == 0
    cfgs = _configs(orch)
    assert (cfgs["a"].target_freq_mhz, cfgs["a"].max_llm_calls, cfgs["a"].max_vivado_minutes,
            cfgs["a"].max_wall_minutes) == (150.0, 50, 150.0, 240.0)
    assert (cfgs["b"].target_freq_mhz, cfgs["b"].max_llm_calls, cfgs["b"].max_vivado_minutes,
            cfgs["b"].max_wall_minutes) == (100.0, 5, 40.0, 60.0)
    for name in ("c", "d", "e"):  # entries that declare nothing take the bench values
        assert (cfgs[name].target_freq_mhz, cfgs[name].max_llm_calls) == (100.0, 30)
    assert all(cfg.max_iterations == 1 for cfg in cfgs.values())  # iterations still follow the bench
    record = {r["entry"]: r for r in records()[-1]["results"]}
    assert record["a"]["config"]["target_freq_mhz"] == 150.0
    assert record["a"]["config"]["max_vivado_minutes"] == 150.0 and record["a"]["config"]["max_llm_calls"] == 50
    assert record["b"]["config"]["max_llm_calls"] == 5
    out = capsys.readouterr().out
    assert "a: meta.yaml sets target_freq_mhz = 150.0" in out and "b: meta.yaml sets max_llm_calls = 5" in out


def test_entry_settings_change_the_cohort(curriculum):
    root, _, output = curriculum
    assert runner.run_tier(0, output_root=output) == 0
    before = records()[-1]["cohort"]
    _set_meta(root, "a", budgets={"wall_minutes": 300})
    assert runner.run_tier(0, output_root=output) == 0
    assert records()[-1]["cohort"] != before


def test_without_a_bench_frequency_an_entry_runs_at_its_meta_frequency_else_100(curriculum):
    root, orch, output = curriculum
    _set_meta(root, "a", target_freq_mhz=150)
    assert runner.run_tier(0, output_root=output) == 0
    cfgs = _configs(orch)
    assert cfgs["a"].target_freq_mhz == 150.0 and type(cfgs["a"].target_freq_mhz) is float
    assert cfgs["b"].target_freq_mhz == 100.0


def test_meta_synthesis_timeout_reaches_the_bench_config(curriculum):
    # run.py bench has no --synthesis-timeout-minutes and OVERRIDES does not take it,
    # so nothing on the bench path can replace an entry's own value.
    root, orch, output = curriculum
    _set_meta(root, "a", synthesis_timeout_minutes=45)
    assert "synthesis_timeout_minutes" not in runner.OVERRIDES
    with pytest.raises(ValueError, match="Unsupported curriculum overrides"):
        runner.run_tier(0, output_root=output, synthesis_timeout_minutes=15.0)
    assert runner.run_tier(0, output_root=output, max_vivado_minutes=40.0) == 0
    cfgs = _configs(orch)
    assert cfgs["a"].synthesis_timeout_minutes == 45 and cfgs["b"].synthesis_timeout_minutes == 15.0


def test_run_py_bench_sends_no_default_frequency_or_timeout(monkeypatch, tmp_path):
    import run
    seen = {}
    monkeypatch.setattr(runner, "run_tier", lambda tier, **kw: seen.update(kw) or 0)
    assert run.main(["bench", "--tier", "2", "--output-dir", str(tmp_path)]) == 0
    assert seen == {"output_root": tmp_path.resolve()}
    with pytest.raises(SystemExit):
        run.main(["bench", "--tier", "2", "--synthesis-timeout-minutes", "45"])


def _entry(tmp_path, text):
    entry = tmp_path / "e"
    entry.mkdir(exist_ok=True)
    (entry / "s.json").write_text("{}")
    (entry / "meta.yaml").write_text("mode: build\nspec: s.json\n" + text)
    return entry


@pytest.mark.parametrize("text,match", [
    ("budgets: {}\n", "budgets may set only"),
    ("budgets: [1]\n", "budgets may set only"),
    ("budgets:\n  best_of_n: 2\n", "budgets may set only"),
    ("budgets:\n  model_calls: 0\n", "budgets.model_calls must be a positive integer"),
    ("budgets:\n  model_calls: 2.5\n", "budgets.model_calls must be a positive integer"),
    ("budgets:\n  model_calls: true\n", "budgets.model_calls must be a positive integer"),
    ("budgets:\n  tool_minutes: -1\n", "budgets.tool_minutes must be a positive number"),
    ("budgets:\n  wall_minutes: .nan\n", "budgets.wall_minutes must be a positive number"),
    ("budgets:\n  wall_minutes: '60'\n", "budgets.wall_minutes must be a positive number"),
    ("explore_budgets:\n  tool_minutes: 90\n", "renamed budgets"),
    ("target_freq_mhz: 0\n", "target_freq_mhz must be a positive number"),
    ("target_freq_mhz: .inf\n", "target_freq_mhz must be a positive number"),
    ("target_freq_mhz: '150'\n", "target_freq_mhz must be a positive number"),
])
def test_metadata_rejects_invalid_budgets_and_frequency(tmp_path, text, match):
    with pytest.raises(ValueError, match=match):
        runner._metadata(_entry(tmp_path, text))


def test_metadata_accepts_valid_budgets(tmp_path):
    meta = runner._metadata(_entry(tmp_path, "budgets:\n  model_calls: 40\n  tool_minutes: 90.5\n"))
    assert runner.entry_settings(meta) == {"max_llm_calls": 40, "max_vivado_minutes": 90.5}


def test_every_real_entry_validates_and_heavy_entries_declare_budgets():
    for meta_path in sorted((ROOT / "curriculum").glob("tier*/*/meta.yaml")):
        meta = runner._metadata(meta_path.parent)
        settings = runner.entry_settings(meta)
        assert all(isinstance(v, (int, float)) and math.isfinite(v) and v > 0 for v in settings.values())
    aes = runner.entry_settings(runner._metadata(ROOT / "curriculum/tier6/aes128_core_build"))
    assert aes["max_vivado_minutes"] == 150.0 and aes["max_wall_minutes"] == 240.0
