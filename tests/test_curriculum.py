import json
from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml

from curriculum import runner
from autortl.config import RunConfig
from autortl.spec import DesignSpec


def successful_metrics():
    return {"sim_passed": True, "sim_error": "", "synth_error": "",
            "timing_met": True, "wns_ns": 1.0, "whs_ns": 0.1,
            "lut_used": 5, "lut_total": 100, "ff_used": 5, "ff_total": 100}


@pytest.fixture
def curriculum(monkeypatch, tmp_path):
    root = tmp_path / "curriculum"
    for name in ("a", "b", "c", "d", "e"):
        entry = root / "tier0" / name
        entry.mkdir(parents=True)
        (entry / "m.v").write_text("module m; endmodule")
        (entry / "tb.v").write_text("module tb; endmodule")
        (entry / "meta.yaml").write_text(yaml.safe_dump({"mode": "optimize", "top": "m",
            "design": "m.v", "tb": "tb.v", "pass_criteria": {"timing_met": True}}))
    monkeypatch.setattr(runner, "ROOT", root)
    monkeypatch.setattr(runner, "RESULTS", root / "results.jsonl")
    orch = Mock()
    orch.return_value.run.side_effect = lambda: {"status": "done", "best_metrics": successful_metrics()}
    monkeypatch.setattr(runner, "Orchestrator", orch)
    return root, orch, tmp_path / "outputs"


def records():
    return [json.loads(line) for line in runner.RESULTS.read_text().splitlines()]


def test_three_consecutive_matching_full_runs_hold(curriculum):
    _, orch, output = curriculum
    for expected in (1, 2, 3):
        assert runner.run_tier(0, output_root=output) == 0
        record = records()[-1]
        assert record["consecutive_qualifying_runs"] == expected
        assert record["held"] == (expected == 3)
    assert orch.call_count == 15
    assert len({r["cohort"] for r in records()}) == 1
    assert len({r["evidence_dir"] for r in records()}) == 3


def test_subset_never_promotes_even_when_selecting_every_entry(curriculum):
    _, _, output = curriculum
    for _ in range(3):
        runner.run_tier(0, output_root=output, entries=list("abcde"))
    assert not records()[-1]["held"] and not records()[-1]["full_tier"]
    runner.run_tier(0, output_root=output)
    assert records()[-1]["consecutive_qualifying_runs"] == 1


def test_subset_cannot_supply_protected_entries():
    history = [{"tier": 0, "cohort": "same", "full_tier": False, "held": True,
                "qualified": True, "results": [{"entry": "a", "ok": True}]}]
    current = [{"entry": name, "ok": name != "a"} for name in "abcde"]
    governance = runner._govern(history, 0, "same", current, True)
    assert governance["qualified"] and not governance["held_before"]
    assert governance["held_regressions"] == []


def test_held_regression_blocks_even_at_eighty_percent(curriculum):
    _, orch, output = curriculum
    for _ in range(3):
        runner.run_tier(0, output_root=output)
    outcomes = iter([{"status": "failed"}] + [
        {"status": "done", "best_metrics": successful_metrics()} for _ in range(4)])
    orch.return_value.run.side_effect = lambda: next(outcomes)
    assert runner.run_tier(0, output_root=output) == 1
    assert records()[-1]["passed"] == 4
    assert records()[-1]["held_regressions"] == ["a"]
    assert records()[-1]["consecutive_qualifying_runs"] == 0


def test_changed_execution_cohort_resets_streak(curriculum):
    _, _, output = curriculum
    runner.run_tier(0, output_root=output, max_infra_retries=2)
    runner.run_tier(0, output_root=output, max_infra_retries=2)
    runner.run_tier(0, output_root=output, max_infra_retries=3)
    assert records()[-1]["consecutive_qualifying_runs"] == 1
    assert records()[-1]["cohort"] != records()[-2]["cohort"]


def test_source_change_resets_streak(curriculum):
    root, _, output = curriculum
    runner.run_tier(0, output_root=output)
    (root / "tier0/a/m.v").write_text("module m; wire x; endmodule")
    runner.run_tier(0, output_root=output)
    assert records()[-1]["consecutive_qualifying_runs"] == 1


@pytest.mark.parametrize("field,value", [
    ("sim_passed", False), ("sim_error", "failed"), ("synth_error", "failed"),
    ("timing_met", False), ("wns_ns", -1.0), ("whs_ns", -0.1),
    ("lut_total", 0), ("ff_total", 0), ("wns_ns", float("nan")),
    ("whs_ns", -999.0), ("lut_used", -1),
])
def test_mandatory_gates_cannot_be_skipped(field, value):
    metrics = successful_metrics()
    metrics[field] = value
    assert not runner._accepted({"status": "done", "best_metrics": metrics}, {})[0]


def test_declared_resource_limits_apply():
    summary = {"status": "done", "best_metrics": successful_metrics()}
    assert not runner._accepted(summary, {"max_luts": 4})[0]
    assert not runner._accepted(summary, {"max_ffs": 4})[0]
    assert runner._accepted(summary, {"max_luts": 5, "max_ffs": 5})[0]


@pytest.mark.parametrize("contents", ["[]", "mode: invalid", "mode: optimize", "[bad yaml"])
def test_malformed_metadata_fails_before_any_jobs(curriculum, contents):
    root, orch, output = curriculum
    (root / "tier0/e/meta.yaml").write_text(contents)
    with pytest.raises((ValueError, yaml.YAMLError)):
        runner.run_tier(0, output_root=output)
    orch.assert_not_called()


@pytest.mark.parametrize("contents", ['{"partial":', '[]', '{"tier":0}',
    '{"tier":0,"cohort":"x","qualified":true,"held":true,"full_tier":false,"results":[{"entry":"a","ok":true}]}'])
def test_malformed_history_fails_before_any_jobs(curriculum, contents):
    _, orch, output = curriculum
    runner.RESULTS.write_text(contents)
    with pytest.raises(ValueError, match="Malformed curriculum history"):
        runner.run_tier(0, output_root=output)
    orch.assert_not_called()


def test_unknown_criteria_cannot_silently_disappear(curriculum):
    root, orch, output = curriculum
    meta = root / "tier0/a/meta.yaml"
    data = yaml.safe_load(meta.read_text())
    data["pass_criteria"] = {"max_lut": 1}
    meta.write_text(yaml.safe_dump(data))
    with pytest.raises(ValueError, match="criteria"):
        runner.run_tier(0, output_root=output)
    orch.assert_not_called()


def test_atomic_results_failure_preserves_history(curriculum, monkeypatch):
    from autortl import state
    _, _, output = curriculum
    runner.run_tier(0, output_root=output)
    before = runner.RESULTS.read_bytes()
    replace = state.os.replace
    def fail_history(source, destination):
        if Path(destination) == runner.RESULTS:
            raise OSError("interrupted history write")
        return replace(source, destination)
    monkeypatch.setattr(state.os, "replace", fail_history)
    with pytest.raises(OSError):
        runner.run_tier(0, output_root=output)
    assert runner.RESULTS.read_bytes() == before


def test_checked_in_build_fixtures_have_valid_constructor_and_ports():
    actual = Path(__file__).resolve().parents[1] / "curriculum" / "tier1"
    found = {}
    for entry in actual.iterdir():
        if not (entry / "design_spec.json").exists():
            continue
        meta = runner._metadata(entry)
        spec = DesignSpec.load(entry / meta["spec"])
        config = RunConfig(mode=meta["mode"], top_module=meta["top"],
                           spec_path=entry / meta["spec"], testbench_path=entry / meta["tb"])
        config.validate()
        assert spec.top_name == config.top_module
        for module in spec.modules:
            assert module.validate() == []
        assert all(port.validate() == [] for port in spec.external_ports)
        found[spec.top_name] = {port.name: port.width for port in spec.external_ports}
    assert found["counter8"] == {"clk": 1, "rst": 1, "enable": 1, "count": 8}
    assert found["priority_encoder8"] == {"clk": 1, "rst": 1, "request": 8, "valid": 1, "index": 3}
