"""Oracles that agree with the behavior text but not the examples send a planner spec back.

Taxonomy: oracle_example_dispute_ends_build (explore-tier3-05 uart_fifo_build, uart_tx).
Only a planner-written spec is repaired; a supplied JSON spec is law. Lint repairs and
disputes share one max_fix_attempts counter. Infra never counts as a dispute.
"""
import json
from unittest.mock import Mock

import pytest

from autortl import fsm
from autortl.config import RunConfig
from autortl.golden import GoldenTimeoutError, only_example_mismatches, validate_examples
from autortl.spec import DesignSpec
from llm.client import ModelCallError
from tests.test_fsm_build import create
from tests.test_golden_reset_protocol import COUNTER
from tests.test_spec_repair import GOOD, prose, same_name_as_module

ORACLE = COUNTER.replace('"count": 99', '"count": 0')
MISMATCH = "example 1: expected count=7, golden model gave 1"


def disputed():
    """GOOD with an example the behavior text cannot produce (one enabled step gives 1)."""
    spec = json.loads(GOOD)
    spec["modules"][0]["examples"][1]["expected"]["count"] = 7
    return json.dumps(spec)


def generated_oracle_build(tmp_path, monkeypatch, planner_outputs, oracle=ORACLE):
    o, synthesis = create(tmp_path, monkeypatch)
    prose(tmp_path, o)
    o.cfg.testbench_path = None
    planner = Mock(side_effect=planner_outputs)
    monkeypatch.setattr(o.planner, "make_spec", planner)
    golden = Mock(side_effect=oracle) if isinstance(oracle, list) else Mock(return_value=oracle)
    monkeypatch.setattr(o.generator, "golden_model", golden)
    return o, planner, golden, synthesis


def checkpoint(o):
    return json.loads((o.state.run_dir / "state.json").read_text(encoding="utf-8"))


def resumed(o, monkeypatch, **mocks):
    """A fresh orchestrator on the same run directory with the same role mocks."""
    new = fsm.Orchestrator(RunConfig.load(o.state.run_dir / "config.json"), o.state.run_dir)
    for role in ("planner", "generator", "evaluator"):
        for name, value in vars(getattr(o, role)).items():
            if isinstance(value, Mock):
                monkeypatch.setattr(getattr(new, role), name, value)
    for dotted, value in mocks.items():
        role, name = dotted.split("__")
        monkeypatch.setattr(getattr(new, role), name, value)
    return new


def test_only_example_mismatches_classifies_qualification_lines():
    module = DesignSpec.from_json(GOOD).modules[0]
    assert only_example_mismatches([MISMATCH], module)
    assert not only_example_mismatches([], module)
    assert not only_example_mismatches([MISMATCH, "golden worker failed"], module)
    module.examples[0].expected = {}
    assert validate_examples(module)
    assert not only_example_mismatches([MISMATCH], module)


def test_disputed_planner_spec_is_replanned_and_the_new_spec_builds(tmp_path, monkeypatch):
    o, planner, golden, synthesis = generated_oracle_build(tmp_path, monkeypatch, [disputed(), GOOD])
    result = o.run()
    assert result["status"] == "done"
    assert planner.call_count == 2 and golden.call_count == 3
    feedback = planner.call_args_list[1].kwargs["feedback"]
    assert feedback.startswith("Repair attempt 1.\nmodule counter8_core: " + fsm.SPEC_DISPUTE_INSTRUCTION)
    assert MISMATCH in feedback and feedback.count(MISMATCH) == 1  # both attempts, listed once
    assert "Your previous design_spec was:\n" + disputed() in feedback
    assert len(feedback) < 8000
    run = o.state.run_dir
    assert json.loads((run / "design_spec.json").read_text(encoding="utf-8")) == json.loads(GOOD)
    first = [json.loads((run / f"modules/counter8_core/golden_attempt_{i}.log").read_text()) for i in (1, 2)]
    assert all(log["example_mismatch_only"] and MISMATCH in log["diagnostic"] for log in first)
    assert json.loads((run / "modules_rev1/counter8_core/golden_attempt_1.log").read_text())["status"] == "oracle_qualified"
    assert (run / "modules_rev1/counter8_core/counter8_core.v").is_file()
    assert not (run / "modules/counter8_core/counter8_core.v").exists()
    state = checkpoint(o)
    assert state["spec_repairs"] == 1
    assert [d["outcome"] for d in state["spec_disputes"]] == ["replanned"]
    assert state["spec_disputes"][0]["attempts"] == [[MISMATCH], [MISMATCH]]
    assert [r["revision"] for r in state["spec_revisions"]] == [0, 1]
    assert json.loads((run / "spec_disputes/rev0.json").read_text())["module"] == "counter8_core"
    assert (run / "spec_revisions/rev0.json").read_text(encoding="utf-8") == disputed()
    assert synthesis.call_count == 1


def test_supplied_json_spec_with_disputed_examples_fails_without_planner(tmp_path, monkeypatch):
    o, _ = create(tmp_path, monkeypatch)  # make_spec raises if called
    supplied = tmp_path / "spec.json"
    supplied.write_text(disputed(), encoding="utf-8")
    o.cfg.spec_path = supplied
    o.cfg.testbench_path = None
    golden = Mock(return_value=ORACLE)
    monkeypatch.setattr(o.generator, "golden_model", golden)
    result = o.run()
    assert result["status"] == "module_failed" and result["module"] == "counter8_core"
    assert set(result) == {"status", "module", "error"}
    assert MISMATCH in result["error"]
    assert golden.call_count == fsm.ORACLE_ATTEMPTS  # a supplied spec cannot be replanned
    state = checkpoint(o)
    assert "spec_disputes" not in state and "spec_revisions" not in state
    assert not (o.state.run_dir / "modules_rev1").exists()


SANDBOX = 'def init(): return {}\ndef step(s,i): return s,{"count":i["missing"]}'


@pytest.mark.parametrize("oracles", [
    ["def init(:", "def init(:", "def init(:"],  # validation error, three times
    [SANDBOX, SANDBOX, SANDBOX],                # worker error while running the examples
    [ORACLE, SANDBOX, "def init(:"],            # a mismatch then other errors
    [SANDBOX, ORACLE, "def init(:"],            # a mismatch between other errors
])
def test_non_mismatch_oracle_failure_is_not_a_dispute(tmp_path, monkeypatch, oracles):
    o, planner, golden, synthesis = generated_oracle_build(tmp_path, monkeypatch, [disputed(), GOOD], oracles)
    result = o.run()
    assert result["status"] == "module_failed" and "spec_dispute" not in result
    assert planner.call_count == 1 and golden.call_count == fsm.ORACLE_ATTEMPTS
    assert "spec_disputes" not in checkpoint(o)
    synthesis.assert_not_called()


def test_lint_repairs_and_disputes_share_one_counter(tmp_path, monkeypatch):
    # max_fix_attempts is 1: the lint repair spends it, so the dispute cannot replan.
    o, planner, golden, synthesis = generated_oracle_build(
        tmp_path, monkeypatch, [same_name_as_module(disputed()), disputed(), GOOD])
    result = o.run()
    assert result["status"] == "module_failed"
    assert result["spec_dispute"]["outcome"] == "repairs_exhausted"
    assert result["spec_dispute"]["spec_repair"] is None
    assert planner.call_count == 2 and golden.call_count == 2
    state = checkpoint(o)
    assert state["spec_repairs"] == 1
    assert [d["outcome"] for d in state["spec_disputes"]] == ["repairs_exhausted"]
    synthesis.assert_not_called()


def test_shared_counter_bounds_lint_repairs_after_a_dispute(tmp_path, monkeypatch):
    o, planner, golden, synthesis = generated_oracle_build(
        tmp_path, monkeypatch, [disputed(), same_name_as_module(GOOD), same_name_as_module(GOOD), GOOD])
    o.cfg.max_fix_attempts = 2
    result = o.run()
    assert result["status"] == "spec_lint_failed"
    assert planner.call_count == 3  # the initial spec, one dispute repair, one lint repair
    assert "Repair attempt 2." in planner.call_args_list[2].kwargs["feedback"]
    assert checkpoint(o)["spec_repairs"] == 2
    synthesis.assert_not_called()


def test_dispute_then_lint_repair_within_the_bound_builds(tmp_path, monkeypatch):
    o, planner, golden, _ = generated_oracle_build(
        tmp_path, monkeypatch, [disputed(), same_name_as_module(GOOD), GOOD])
    o.cfg.max_fix_attempts = 2
    assert o.run()["status"] == "done"
    assert planner.call_count == 3 and golden.call_count == 3


def test_oracle_timeout_is_infra_and_never_a_dispute(tmp_path, monkeypatch):
    o, planner, golden, synthesis = generated_oracle_build(tmp_path, monkeypatch, [disputed(), GOOD])
    real = fsm.qualify_against_examples
    calls = []
    def qualify(gm, module):
        calls.append(module.name)
        if len(calls) == 2:
            raise GoldenTimeoutError("golden worker timed out")
        return real(gm, module)
    monkeypatch.setattr(fsm, "qualify_against_examples", qualify)
    result = o.run()
    assert result["status"] == "build_blocked" and result["failure_kind"] == "infra"
    assert planner.call_count == 1 and golden.call_count == 2
    assert "spec_disputes" not in checkpoint(o) and "spec_repairs" not in checkpoint(o)
    synthesis.assert_not_called()


def test_model_unavailable_during_oracle_is_infra_and_never_a_dispute(tmp_path, monkeypatch):
    unavailable = ModelCallError("generator", "CODEX_UNAVAILABLE")
    o, planner, golden, synthesis = generated_oracle_build(
        tmp_path, monkeypatch, [disputed(), GOOD], [ORACLE, unavailable])
    result = o.run()
    assert result["status"] == "model_blocked" and result["error_code"] == "CODEX_UNAVAILABLE"
    assert planner.call_count == 1
    assert "spec_disputes" not in checkpoint(o)
    synthesis.assert_not_called()


def test_resume_after_blocked_dispute_repair_replays_and_replans_once(tmp_path, monkeypatch):
    unavailable = ModelCallError("planner", "CODEX_UNAVAILABLE")
    o, planner, golden, _ = generated_oracle_build(tmp_path, monkeypatch, [disputed(), unavailable])
    assert o.run()["status"] == "model_blocked"
    assert checkpoint(o)["spec_repairs"] == 1
    planner2, golden2 = Mock(return_value=GOOD), Mock(return_value=ORACLE)
    again = resumed(o, monkeypatch, planner__make_spec=planner2, generator__golden_model=golden2)
    result = again.run()
    assert result["status"] == "done"
    assert planner2.call_count == 1 and golden2.call_count == 1  # earlier calls replay from the journal
    assert fsm.SPEC_DISPUTE_INSTRUCTION in planner2.call_args.kwargs["feedback"]
    state = checkpoint(again)
    assert state["spec_repairs"] == 1 and len(state["spec_disputes"]) == 1
    assert [r["revision"] for r in state["spec_revisions"]] == [0, 1]


def test_resume_after_replan_uses_the_replanned_spec(tmp_path, monkeypatch):
    o, planner, golden, _ = generated_oracle_build(tmp_path, monkeypatch, [disputed(), GOOD])
    monkeypatch.setattr(o.generator, "generate", Mock(side_effect=ModelCallError("generator", "CODEX_UNAVAILABLE")))
    assert o.run()["status"] == "model_blocked"
    assert json.loads((o.state.run_dir / "design_spec.json").read_text()) == json.loads(GOOD)
    from tests.test_fsm_build import RTL
    again = resumed(o, monkeypatch, planner__make_spec=Mock(side_effect=AssertionError("replayed, not replanned")),
                    generator__generate=Mock(return_value=RTL))
    result = again.run()
    assert result["status"] == "done"
    assert json.loads((again.state.run_dir / "design_spec.json").read_text()) == json.loads(GOOD)
    assert golden.call_count == 3  # nothing re-asked on resume
    assert checkpoint(again)["spec_repairs"] == 1


def test_resume_refuses_to_build_a_superseded_spec_revision(tmp_path, monkeypatch):
    # If a replayed oracle stopped disputing, the build would fall back to the
    # pre-dispute spec; the checkpoint records revision 1, so that is refused.
    o, planner, golden, _ = generated_oracle_build(tmp_path, monkeypatch, [disputed(), GOOD])
    monkeypatch.setattr(o.generator, "generate", Mock(side_effect=ModelCallError("generator", "CODEX_UNAVAILABLE")))
    assert o.run()["status"] == "model_blocked"
    monkeypatch.setattr(fsm, "qualify_against_examples", Mock(return_value=[]))
    from tests.test_fsm_build import RTL
    again = resumed(o, monkeypatch, generator__generate=Mock(return_value=RTL))
    result = again.run()
    assert result["status"] == "infra_blocked"
    assert "revision 0" in result["error"] and "revision 1" in result["error"]


def test_resume_refuses_a_spec_revision_that_differs_from_the_checkpoint(tmp_path, monkeypatch):
    o, planner, golden, _ = generated_oracle_build(tmp_path, monkeypatch, [disputed(), GOOD])
    monkeypatch.setattr(o.generator, "generate", Mock(side_effect=ModelCallError("generator", "CODEX_UNAVAILABLE")))
    assert o.run()["status"] == "model_blocked"
    state = checkpoint(o)
    state["spec_revisions"][1]["spec_sha256"] = "0" * 64
    (o.state.run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
    from tests.test_fsm_build import RTL
    again = resumed(o, monkeypatch, generator__generate=Mock(return_value=RTL))
    result = again.run()
    assert result["status"] == "infra_blocked"
    assert "spec revision 1" in result["error"]
