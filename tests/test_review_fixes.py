"""Regression tests for the independent review of the October 29 harness changes."""
import json
from unittest.mock import Mock

import pytest

from autortl.budget import Budget
from autortl.config import RunConfig
from autortl.state import CheckpointLockedError
from curriculum import runner
from llm import client
from tests.test_curriculum import curriculum, records, successful_metrics  # noqa: F401


def test_token_lock_propagates_without_discarding_the_response(tmp_path, monkeypatch):
    # token_save_lock_misattributed
    monkeypatch.setattr(client, "_STATS_PATH", tmp_path / "stats.jsonl")
    monkeypatch.setattr(client, "_load_routing", lambda: {"roles": {}, "defaults": {"max_retries_per_backend": 2, "timeout_s": 60}})
    backend = Mock()
    backend.ask.return_value = ("text", {"usage": {"input_tokens": 5}})
    monkeypatch.setattr(client, "_BACKENDS", {"codex": backend})
    budget = Budget(5, 10, 10)
    budget.charge_tokens = Mock(side_effect=CheckpointLockedError("budget.json held open"))
    with pytest.raises(CheckpointLockedError):
        client.ask("planner", "p", budget=budget)
    assert backend.ask.call_count == 1 and budget.llm_calls == 1  # no retry, no second charge


def test_the_winner_digest_comes_from_the_summary_top(curriculum):  # noqa: F811
    # parallel_build_winner_digest_lost: a worker process keeps its top_module rewrite to itself
    _, orch, output = curriculum
    construct = orch.side_effect

    def build(cfg, run_dir):
        instance = construct(cfg, run_dir)
        (run_dir / "renamed_top_best.v").write_text("module renamed_top; endmodule")
        instance.run.side_effect = lambda: {"status": "done", "best_metrics": successful_metrics(),
                                            "top_module": "renamed_top"}
        return instance

    orch.side_effect = build
    runner.run_tier(0, output_root=output)
    assert all(r["winner_sha256"] for r in records()[-1]["results"])


def test_an_escaped_checkpoint_lock_is_infrastructure(curriculum):  # noqa: F811
    # infra_outcomes_missing_failure_kind
    _, orch, output = curriculum
    construct = orch.side_effect

    def build(cfg, run_dir):
        instance = construct(cfg, run_dir)
        if run_dir.name == "c":
            instance.run.side_effect = CheckpointLockedError("events.jsonl held open")
        return instance

    orch.side_effect = build
    assert runner.run_tier(0, output_root=output) == 3
    assert not runner.RESULTS.exists()


def test_build_blocked_and_integration_failures_carry_their_kind():
    from pathlib import Path
    source = (Path(__file__).resolve().parents[1] / "autortl" / "fsm.py").read_text(encoding="utf-8")
    assert '"failure_kind": kind.value, "error": err}' in source.replace("\n                    ", " ")
    assert '{"status": "integration_failed", "failure_kind": kind.value, "error": err}' in source


def test_default_is_not_a_pinned_model():
    with pytest.raises(ValueError, match="unpinned"):
        RunConfig(mode="optimize", model="default").validate()


def test_null_saved_tokens_is_a_clean_error(tmp_path):
    (tmp_path / "budget.json").write_text('{"llm_calls": 1, "vivado_seconds": 0, "elapsed": 0, "tokens": null}')
    with pytest.raises(ValueError, match="token"):
        Budget(5, 5, 5, tmp_path / "budget.json")


def test_doctor_does_not_mistake_not_logged_in(monkeypatch, tmp_path):
    from autortl import doctor
    monkeypatch.setattr(doctor.shutil, "which", lambda name: "/bin/codex" if name == "codex" else None)
    monkeypatch.delenv("AUTORTL_CODEX_BIN", raising=False)
    monkeypatch.setattr(doctor, "_probe", lambda cmd, timeout=60: (0, "codex 1") if cmd[-1] == "--version" else (0, "Not logged in"))
    assert {c.name: c.status for c in doctor.model_check()}["codex login"] == "MISSING"
