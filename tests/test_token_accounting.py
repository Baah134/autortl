"""Per-run token accounting from the usage the model CLI reports."""
import json
import sys
from unittest.mock import Mock

import pytest

from autortl.budget import Budget
from llm import client


def test_usage_accumulates_and_persists(tmp_path):
    b = Budget(10, 10, 10, tmp_path / "budget.json")
    b.charge_tokens({"input_tokens": 100, "cached_input_tokens": 60, "output_tokens": 7})
    b.charge_tokens({"input_tokens": 50, "output_tokens": 3, "bogus": 9})
    saved = json.loads((tmp_path / "budget.json").read_text())
    assert saved["tokens"] == {"input_tokens": 150, "cached_input_tokens": 60, "output_tokens": 10}
    assert Budget(10, 10, 10, tmp_path / "budget.json").tokens == saved["tokens"]


def test_missing_or_malformed_usage_adds_nothing(tmp_path):
    b = Budget(10, 10, 10, tmp_path / "budget.json")
    for usage in (None, "lots", {"input_tokens": -5}, {"input_tokens": 1.5}):
        b.charge_tokens(usage)
    assert b.tokens == {"input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0}


def test_budgets_saved_before_token_accounting_still_load(tmp_path):
    (tmp_path / "budget.json").write_text('{"llm_calls": 2, "vivado_seconds": 3.0, "elapsed": 4.0}')
    assert Budget(10, 10, 10, tmp_path / "budget.json").tokens["input_tokens"] == 0


def test_client_charges_reported_usage(tmp_path, monkeypatch):
    monkeypatch.setattr(client, "_STATS_PATH", tmp_path / "stats.jsonl")
    monkeypatch.setattr(client, "_load_routing", lambda: {"roles": {}, "defaults": {"max_retries_per_backend": 1, "timeout_s": 60}})
    backend = Mock()
    backend.ask.return_value = ("text", {"usage": {"input_tokens": 1000, "output_tokens": 20}})
    monkeypatch.setattr(client, "_BACKENDS", {"codex": backend})
    b = Budget(5, 10, 10, tmp_path / "budget.json")
    assert client.ask("planner", "p", budget=b) == "text"
    assert (b.llm_calls, b.tokens["input_tokens"], b.tokens["output_tokens"]) == (1, 1000, 20)


def test_calls_without_usage_are_counted_not_read_as_zero_use(tmp_path):
    # command_endpoint_tokens_reported_as_zero: a command endpoint reports no usage.
    b = Budget(10, 10, 10, tmp_path / "budget.json")
    assert b.tokens_complete
    for usage in (None, "lots", {}, {"input_tokens": -5}, {"input_tokens": 1.5}, {"input_tokens": True}):
        b.charge_tokens(usage)
    b.charge_tokens({"input_tokens": 0, "output_tokens": 0})  # a reported zero is a report
    b.charge_tokens({"input_tokens": 9})
    saved = json.loads((tmp_path / "budget.json").read_text())
    assert saved["calls_without_token_usage"] == 6 and saved["tokens"]["input_tokens"] == 9
    resumed = Budget(10, 10, 10, tmp_path / "budget.json")
    assert resumed.calls_without_token_usage == 6 and not resumed.tokens_complete


def test_budgets_saved_before_the_unreported_count_load_as_complete(tmp_path):
    (tmp_path / "budget.json").write_text('{"llm_calls": 2, "vivado_seconds": 3.0, "elapsed": 4.0, '
                                          '"tokens": {"input_tokens": 7}}')
    assert Budget(10, 10, 10, tmp_path / "budget.json").calls_without_token_usage == 0


@pytest.mark.parametrize("bad", ["-1", "1.5", '"3"', "true", "null"])
def test_a_malformed_unreported_count_is_refused(tmp_path, bad):
    (tmp_path / "budget.json").write_text('{"llm_calls": 2, "vivado_seconds": 3.0, "elapsed": 4.0, '
                                          '"calls_without_token_usage": ' + bad + '}')
    with pytest.raises(ValueError, match="without token usage"):
        Budget(10, 10, 10, tmp_path / "budget.json")


def test_a_command_endpoint_call_marks_the_tokens_incomplete(tmp_path, monkeypatch):
    script = tmp_path / "ai.py"
    script.write_text("import sys; sys.stdin.read(); print('answer')", encoding="utf-8")
    endpoints_file = tmp_path / "endpoints.yaml"
    endpoints_file.write_text(json.dumps({"endpoints": {"mine": {"kind": "command",
                                                                 "argv": [sys.executable, str(script)]}}}),
                              encoding="utf-8")
    monkeypatch.setenv("AUTORTL_ENDPOINTS", str(endpoints_file))
    monkeypatch.setattr(client, "_STATS_PATH", tmp_path / "stats.jsonl")
    b = Budget(5, 10, 10, tmp_path / "budget.json")
    assert client.ask("planner", "p", budget=b, model="mine.default") == "answer"
    saved = json.loads((tmp_path / "budget.json").read_text())
    assert saved["llm_calls"] == 1 and saved["calls_without_token_usage"] == 1
    assert saved["tokens"] == {"input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0}
