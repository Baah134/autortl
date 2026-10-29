"""Per-run token accounting from the usage the model CLI reports."""
import json
from unittest.mock import Mock

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
