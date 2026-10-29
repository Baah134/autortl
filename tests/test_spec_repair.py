"""A planner-written spec that fails structural lint is repaired, boundedly.

Taxonomy: spec_lint_failure_skips_planner_repair. Supplied JSON specs are law
and are never replanned.
"""
import json
from pathlib import Path
from unittest.mock import Mock

from autortl import prompts
from tests.test_fsm_build import ROOT, create

GOOD = (ROOT / "curriculum/tier1/counter8_build/design_spec.json").read_text(encoding="utf-8")


def same_name_as_module(text):
    spec = json.loads(text)
    spec["top_name"] = spec["modules"][0]["name"]
    return json.dumps(spec)


def prose(tmp_path, o):
    path = tmp_path / "request.md"
    path.write_text("Build an 8-bit counter named counter8.", encoding="utf-8")
    o.cfg.spec_path = path


def test_lint_errors_go_back_to_the_planner_and_the_repair_is_used(tmp_path, monkeypatch):
    o, _ = create(tmp_path, monkeypatch)
    prose(tmp_path, o)
    planner = Mock(side_effect=["Here is the spec:\n" + same_name_as_module(GOOD), GOOD])
    monkeypatch.setattr(o.planner, "make_spec", planner)
    result = o.run()
    assert result["status"] == "done"
    assert planner.call_count == 2
    feedback = planner.call_args_list[1].kwargs["feedback"]
    assert "Repair attempt 1" in feedback and "top module must differ from child module names" in feedback
    assert json.loads((o.state.run_dir / "design_spec.json").read_text(encoding="utf-8"))["top_name"] == "counter8"


def test_unloadable_planner_json_is_repaired_too(tmp_path, monkeypatch):
    o, _ = create(tmp_path, monkeypatch)
    prose(tmp_path, o)
    planner = Mock(side_effect=['{"top_name": "counter8", "modules": [}', GOOD])
    monkeypatch.setattr(o.planner, "make_spec", planner)
    assert o.run()["status"] == "done"
    assert "spec JSON does not load" in planner.call_args_list[1].kwargs["feedback"]


def test_repair_is_bounded_by_max_fix_attempts(tmp_path, monkeypatch):
    o, synthesis = create(tmp_path, monkeypatch)
    prose(tmp_path, o)
    planner = Mock(return_value=same_name_as_module(GOOD))
    monkeypatch.setattr(o.planner, "make_spec", planner)
    result = o.run()
    assert result["status"] == "spec_lint_failed"
    assert result["errors"] == ["top module must differ from child module names"]
    assert planner.call_count == 1 + o.cfg.max_fix_attempts
    synthesis.assert_not_called()


def test_supplied_json_spec_is_law_and_never_replanned(tmp_path, monkeypatch):
    o, _ = create(tmp_path, monkeypatch)
    supplied = tmp_path / "spec.json"
    supplied.write_text(same_name_as_module(GOOD), encoding="utf-8")
    o.cfg.spec_path = supplied
    # create() already makes make_spec raise if it is called.
    result = o.run()
    assert result["status"] == "spec_lint_failed"


def test_spec_prompt_states_the_naming_rule():
    assert "differs from every module name" in prompts.SPEC_PROMPT
    assert '"foo_top"' in prompts.SPEC_PROMPT.format(intent="x", target_part="p", target_freq_mhz=1,
                                                     objective="minimize_luts")


def test_a_spec_that_crashes_the_loader_is_repaired_and_the_planner_sees_it(tmp_path, monkeypatch):
    o, _ = create(tmp_path, monkeypatch)
    prose(tmp_path, o)
    broken = '{"top_name": "counter8", "modules": ["a"]}'  # spec.py calls .pop on a str: AttributeError
    planner = Mock(side_effect=[broken, GOOD])
    monkeypatch.setattr(o.planner, "make_spec", planner)
    assert o.run()["status"] == "done"
    feedback = planner.call_args_list[1].kwargs["feedback"]
    assert "spec JSON does not load" in feedback and broken in feedback
