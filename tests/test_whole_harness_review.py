"""Regression tests for the whole-harness review (Oct 29)."""
from pathlib import Path

import pytest

from autortl.verilog_interface import integer
from curriculum import runner
from tests.test_curriculum import curriculum, records, successful_metrics  # noqa: F401

FSM = (Path(__file__).resolve().parents[1] / "autortl" / "fsm.py").read_text(encoding="utf-8")


def test_ladder_infra_returns_carry_their_kind():
    # ladder_infra_blocked_missing_failure_kind
    assert FSM.count('{"status": "infra_blocked", "failure_kind": FailureKind.INFRA.value, "iteration": it,') == 3
    assert '{"status": "infra_blocked", "iteration": it,' not in FSM


@pytest.mark.parametrize("status", ["infra_blocked", "model_blocked"])
def test_blocked_statuses_never_enter_history(curriculum, status):  # noqa: F811
    _, orch, output = curriculum
    construct = orch.side_effect

    def build(cfg, run_dir):
        instance = construct(cfg, run_dir)
        if run_dir.name == "b":
            instance.run.side_effect = lambda: {"status": status, "error": "quota"}
        return instance

    orch.side_effect = build
    assert runner.run_tier(0, output_root=output) == 3
    assert not runner.RESULTS.exists()


@pytest.mark.parametrize("expression", ["-" * 20000 + "7", "(" * 400 + "1" + ")" * 400, "1+" * 3000 + "1"])
def test_overflowing_width_expressions_are_ordinary_errors(expression):
    # model_text_overflows_supervisor_parser
    with pytest.raises(ValueError):
        integer(expression, {})


def test_latency_check_no_longer_skips_a_missing_annotation():
    # latency_annotation_deletion_skips_check
    assert "latency is not None and latency != " not in FSM


def test_doctor_surgery_runs_the_companion_gate():
    # doctor_surgery_skips_companion_gate
    surgery = FSM[FSM.index('source = self._model("doctor", "surgery"'):]
    assert surgery.index("companions.violation(") < surgery.index('work = parent / f"doctor_')


def test_baseline_repair_runs_the_companion_gate():
    # baseline_repair_skips_companion_check (Codex review of 749d6d1)
    fix_loop = FSM[FSM.index("def _fix_loop"):]
    fix_loop = fix_loop[:fix_loop.index("\n    def ")]
    assert "companions.violation(repaired" in fix_loop
