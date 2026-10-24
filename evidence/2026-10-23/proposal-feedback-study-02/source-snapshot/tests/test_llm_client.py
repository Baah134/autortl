import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from llm.client import extract_verilog, declared_latency
from llm import client
from llm.backends.codex_cli import CodexError
from autortl.budget import Budget
from unittest.mock import Mock
import json
import pytest


@pytest.fixture
def router(monkeypatch, tmp_path):
    monkeypatch.setattr(client, "_STATS_PATH", tmp_path / "stats.jsonl")
    monkeypatch.setattr(client, "_load_routing", lambda: {
        "roles": {"generator": {"chain": ["codex.default"]}},
        "defaults": {"max_retries_per_backend": 2, "timeout_s": 180}})
    backend = Mock()
    monkeypatch.setattr(client, "_BACKENDS", {"codex": backend})
    monkeypatch.setattr(client.time, "sleep", Mock())
    return backend


def test_missing_yaml_defaults_only_to_codex(monkeypatch):
    monkeypatch.setattr(client, "yaml", None)
    assert all(role["chain"] == ["codex.default"]
               for role in client._load_routing()["roles"].values())


def test_checked_in_routes_only_codex():
    assert all(role["chain"] == ["codex.default"]
               for role in client._load_routing()["roles"].values())


def test_success_records_usage_and_charges_attempt(router):
    meta = {"usage": {"input_tokens": 10}, "cost_usd": None}
    router.ask.return_value = ("RTL", meta)
    budget = Budget(2, 10, 10)
    assert client.ask("generator", "request", budget=budget) == "RTL"
    assert budget.llm_calls == 1
    record = json.loads(client._STATS_PATH.read_text())
    assert record["ok"] and record["metadata"] == meta


@pytest.mark.parametrize("code", ["CODEX_UNAVAILABLE", "CODEX_PROTOCOL"])
def test_failures_are_charged_and_not_retried(router, code):
    router.ask.side_effect = CodexError(code, "failed")
    budget = Budget(3, 10, 10)
    with pytest.raises(RuntimeError, match=code):
        client.ask("generator", "request", budget=budget)
    assert budget.llm_calls == 1 and router.ask.call_count == 1
    assert not json.loads(client._STATS_PATH.read_text())["ok"]


def test_timeout_retry_is_bounded_and_charged(router):
    router.ask.side_effect = [CodexError("CODEX_TIMEOUT", "timeout"), ("RTL", {})]
    budget = Budget(2, 10, 10)
    assert client.ask("generator", "request", budget=budget) == "RTL"
    assert budget.llm_calls == 2
    records = [json.loads(line) for line in client._STATS_PATH.read_text().splitlines()]
    assert [r["ok"] for r in records] == [False, True]


def test_budget_stops_retry_before_spawn(router):
    router.ask.side_effect = CodexError("CODEX_TIMEOUT", "timeout")
    budget = Budget(1, 10, 10)
    with pytest.raises(RuntimeError, match="LLM_BUDGET"):
        client.ask("generator", "request", budget=budget)
    assert router.ask.call_count == 1 and budget.llm_calls == 1


def test_exhausted_budget_never_spawns(router):
    budget = Budget(0, 10, 10)
    with pytest.raises(RuntimeError, match="LLM_BUDGET"):
        client.ask("generator", "request", budget=budget)
    router.ask.assert_not_called()


def test_remaining_wall_time_caps_worker_timeout(router):
    router.ask.return_value = ("RTL", {})
    budget = Budget(2, 10, 0.1)
    client.ask("generator", "request", budget=budget)
    assert 0 < router.ask.call_args.kwargs["timeout_s"] <= 6


def test_empty_response_is_failed_attempt(router):
    router.ask.return_value = ("  ", {"usage": None})
    with pytest.raises(RuntimeError, match="CODEX_PROTOCOL"):
        client.ask("generator", "request")
    assert not json.loads(client._STATS_PATH.read_text())["ok"]


def test_external_override_never_falls_back(router):
    with pytest.raises(RuntimeError, match="unsupported backend"):
        client.ask("generator", "request", route_override="claude_code.sonnet")
    router.ask.assert_not_called()


def test_unknown_role_defaults_to_codex(router):
    router.ask.return_value = ("RTL", {})
    assert client.ask("new-role", "request") == "RTL"
    assert router.ask.call_args.args[0] == "default"


def test_extract_prefers_module_block():
    resp = """Here is the tb context:
```text
load = 1; @(posedge clk);
```
And the fix:
```verilog
module counter (input clk); endmodule
```"""
    out = extract_verilog(resp)
    assert out.startswith("module counter")


def test_extract_skips_nonmodule_fence():
    resp = "```verilog\nload = 1;\n```\n```verilog\nmodule m; endmodule\n```"
    assert "module m" in extract_verilog(resp)


def test_extract_strips_think_tags():
    resp = "<think>module fake; endmodule</think>\n```verilog\nmodule real_m; endmodule\n```"
    assert "real_m" in extract_verilog(resp)


def test_raw_module_fallback():
    assert "endmodule" in extract_verilog("module bare; wire x; endmodule")


def test_declared_latency():
    assert declared_latency("// @latency 3\nmodule m; endmodule") == 3
    assert declared_latency("module m; endmodule") is None
