"""Bounded diagnostics never preserve arbitrary worker stdout or credentials."""
import json
from pathlib import Path
import subprocess
from unittest.mock import Mock

import pytest
from autortl.budget import Budget
from llm import client
from llm.backends import codex_cli as backend

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def worker(tmp_path, monkeypatch):
    monkeypatch.setattr(backend.tempfile, "tempdir", str(tmp_path))
    monkeypatch.setenv("AUTORTL_CODEX_BIN", "fake-codex.exe")
    process = Mock(returncode=1, pid=12345)
    monkeypatch.setattr(backend.subprocess, "Popen", Mock(return_value=process))
    monkeypatch.setattr(backend, "_terminate_worker", Mock())
    return process


@pytest.mark.parametrize("fixture,code", [("codex_rate_limit.jsonl", "CODEX_QUOTA"),
                                         ("codex_auth_failure.jsonl", "CODEX_AUTH")])
def test_nonzero_exit_retains_only_sanitized_error_fields(worker, fixture, code):
    worker.communicate.return_value = ((FIXTURES / fixture).read_text(), "ERROR: api_key=sk-stderr-secret")
    with pytest.raises(backend.CodexError) as caught:
        backend.ask("default", "private task")
    error = caught.value
    assert error.code == code
    assert error.metadata["returncode"] == 1
    combined = str(error) + json.dumps(error.metadata)
    for forbidden in ("PRIVATE GENERATED RTL", "test-credential-123", "sk-fixture", "fixture-access-secret",
                      "fixture-refresh-secret", "sk-stderr-secret"):
        assert forbidden not in combined
    assert "[REDACTED]" in combined


def test_zero_exit_failed_turn_classified_and_no_final_needed(worker):
    worker.returncode = 0
    worker.communicate.return_value = ((FIXTURES / "codex_auth_failure.jsonl").read_text(), "ERROR authentication failed")
    with pytest.raises(backend.CodexError) as caught:
        backend.ask("default", "task")
    assert caught.value.code == "CODEX_AUTH"
    assert caught.value.metadata["returncode"] == 0


def test_unknown_nonzero_exit_is_not_guessed(worker):
    worker.communicate.return_value = ('{"type":"item.completed","item":{"text":"PRIVATE"}}', "ordinary progress")
    with pytest.raises(backend.CodexError) as caught:
        backend.ask("default", "task")
    assert caught.value.code == "CODEX_UNAVAILABLE"
    assert caught.value.metadata["errors"] == []
    assert caught.value.metadata["stderr_tail"] == ""
    assert "PRIVATE" not in str(caught.value.metadata)


def test_diagnostic_caps_and_prompt_redaction():
    event = json.dumps({"type": "error", "message": "failure " + "x" * 800})
    diagnostic = backend._diagnostics("\n".join([event] * 30),
        "ERROR secret task input\n" + "ERROR " + "y" * 3000, 1, ("secret task input",))
    assert len(diagnostic["errors"]) == 8
    assert all(len(e["message"]) <= 400 for e in diagnostic["errors"])
    assert len(diagnostic["stderr_tail"]) <= 1000
    assert diagnostic["diagnostics_truncated"]
    assert "secret task input" not in json.dumps(diagnostic)


def test_secrets_redacted_before_tail_cut():
    secret = "sk-" + "a" * 3000
    diagnostic = backend._diagnostics(stderr="ERROR token=" + secret)
    assert "a" * 10 not in diagnostic["stderr_tail"]
    assert "[REDACTED]" in diagnostic["stderr_tail"]


def test_timeout_preserves_partial_error_diagnostics_and_cleanup(worker):
    worker.communicate.side_effect = subprocess.TimeoutExpired("codex", 1,
        output=(FIXTURES / "codex_rate_limit.jsonl").read_bytes(),
        stderr=b"ERROR token=private-timeout-token")
    with pytest.raises(backend.CodexError) as caught:
        backend.ask("default", "task", timeout_s=1)
    assert caught.value.code == "CODEX_TIMEOUT"
    assert caught.value.metadata["errors"]
    assert "private-timeout-token" not in json.dumps(caught.value.metadata)
    backend._terminate_worker.assert_called_once_with(worker)


def test_protocol_event_count_is_bounded(monkeypatch):
    monkeypatch.setattr(backend, "MAX_EVENTS", 3)
    with pytest.raises(backend.CodexError, match="event limit"):
        backend._parse_events('\n'.join(['{"type":"item.started"}'] * 4))


@pytest.fixture
def router(monkeypatch, tmp_path):
    worker = Mock()
    monkeypatch.setattr(client, "_BACKENDS", {"codex": worker})
    monkeypatch.setattr(client, "_STATS_PATH", tmp_path / "stats.jsonl")
    monkeypatch.setattr(client, "_load_routing", lambda: {
        "roles": {"generator": {"chain": ["codex.default"]}},
        "defaults": {"max_retries_per_backend": 2, "timeout_s": 10}})
    monkeypatch.setattr(client.time, "sleep", Mock())
    return worker


@pytest.mark.parametrize("code", ["CODEX_AUTH", "CODEX_QUOTA", "CODEX_PROTOCOL", "CODEX_UNAVAILABLE"])
def test_client_typed_failure_no_blind_retry(router, code):
    metadata = {"returncode": 1, "errors": [{"type": "error", "message": "bounded diagnostic"}]}
    router.ask.side_effect = backend.CodexError(code, "failure", metadata)
    budget = Budget(5, 10, 10)
    with pytest.raises(client.ModelCallError) as caught:
        client.ask("generator", "task", budget=budget)
    assert caught.value.role == "generator" and caught.value.code == code
    assert caught.value.metadata == metadata
    assert router.ask.call_count == budget.llm_calls == 1


def test_network_retry_is_bounded_and_propagates_final_code(router):
    router.ask.side_effect = [backend.CodexError("CODEX_NETWORK", "network unavailable"),
                             backend.CodexError("CODEX_AUTH", "authentication failed")]
    budget = Budget(5, 10, 10)
    with pytest.raises(client.ModelCallError) as caught:
        client.ask("generator", "task", budget=budget)
    assert caught.value.code == "CODEX_AUTH"
    assert router.ask.call_count == budget.llm_calls == 2


def test_unsupported_provider_fails_before_call(router):
    with pytest.raises(client.ModelCallError, match="unsupported backend"):
        client.ask("generator", "task", route_override="old.model")
    router.ask.assert_not_called()


def test_quota_does_not_try_another_model_in_chain(router, monkeypatch):
    monkeypatch.setattr(client, "_load_routing", lambda: {
        "roles": {"generator": {"chain": ["codex.default", "codex.other"]}},
        "defaults": {"max_retries_per_backend": 2}})
    router.ask.side_effect = backend.CodexError("CODEX_QUOTA", "quota exhausted")
    with pytest.raises(client.ModelCallError):
        client.ask("generator", "task")
    router.ask.assert_called_once()
