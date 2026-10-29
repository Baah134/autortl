"""openai_http backend against a local fake chat-completions server (no real network)."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import threading
import time
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from llm import client
from llm.backends import openai_http
from llm.backends.codex_cli import CodexError
from autortl.budget import Budget

KEY = "test-key-0123456789abcdef"
OK_BODY = {"id": "chatcmpl-1", "model": "test-model",
           "choices": [{"index": 0, "finish_reason": "stop",
                        "message": {"role": "assistant", "content": "module m; endmodule"}}],
           "usage": {"prompt_tokens": 120, "completion_tokens": 30,
                     "prompt_tokens_details": {"cached_tokens": 100}}}


class FakeServer:
    """Serves one scripted reply per request and records what it received."""
    def __init__(self):
        self.status, self.body, self.delay = 200, OK_BODY, 0.0
        self.extra_headers = {}
        self.requests = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                outer.requests.append({"path": self.path, "headers": dict(self.headers),
                                       "body": json.loads(self.rfile.read(length))})
                if outer.delay:
                    time.sleep(outer.delay)
                raw = outer.body if isinstance(outer.body, bytes) else json.dumps(outer.body).encode()
                try:
                    self.send_response(outer.status)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(raw)))
                    for name, value in outer.extra_headers.items():
                        self.send_header(name, value)
                    self.end_headers()
                    self.wfile.write(raw)
                except OSError:
                    pass       # the client gave up (timeout test)

            def log_message(self, *args):
                pass

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.httpd.daemon_threads = True
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}/v1"
        self.thread = threading.Thread(target=self.httpd.serve_forever, args=(0.02,), daemon=True)
        self.thread.start()

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


@pytest.fixture
def server(monkeypatch):
    fake = FakeServer()
    monkeypatch.setenv("AUTORTL_OPENAI_BASE_URL", fake.url)
    monkeypatch.setenv("AUTORTL_OPENAI_API_KEY", KEY)
    monkeypatch.delenv("AUTORTL_OPENAI_MODEL", raising=False)
    yield fake
    fake.close()


def test_success_returns_text_and_usage(server):
    text, meta = openai_http.ask("test-model", "make a module", "be terse", timeout_s=10)
    assert text == "module m; endmodule"
    assert meta["usage"] == {"input_tokens": 120, "output_tokens": 30, "cached_input_tokens": 100}
    assert meta["model"] == "test-model" and meta["requested_model"] == "test-model"
    assert meta["http_status"] == 200 and meta["finish_reason"] == "stop"
    request = server.requests[0]
    assert request["path"] == "/v1/chat/completions"
    assert request["headers"]["Authorization"] == f"Bearer {KEY}"
    assert request["body"] == {"model": "test-model", "messages": [
        {"role": "system", "content": "be terse"}, {"role": "user", "content": "make a module"}]}
    assert "temperature" not in request["body"]
    assert KEY not in json.dumps(meta)


def test_no_system_sends_only_the_user_message(server):
    openai_http.ask("test-model", "hi", timeout_s=10)
    assert server.requests[0]["body"]["messages"] == [{"role": "user", "content": "hi"}]


def test_default_alias_uses_the_model_variable(server, monkeypatch):
    monkeypatch.setenv("AUTORTL_OPENAI_MODEL", "env-model")
    _, meta = openai_http.ask("default", "hi", timeout_s=10)
    assert server.requests[0]["body"]["model"] == "env-model" and meta["requested_model"] is None


def test_default_alias_without_model_variable_is_unavailable(server):
    with pytest.raises(CodexError) as err:
        openai_http.ask("default", "hi", timeout_s=10)
    assert err.value.code == "CODEX_UNAVAILABLE" and "AUTORTL_OPENAI_MODEL" in str(err.value)
    assert not server.requests


def test_missing_key_is_unavailable_and_sends_nothing(server, monkeypatch):
    monkeypatch.delenv("AUTORTL_OPENAI_API_KEY")
    with pytest.raises(CodexError) as err:
        openai_http.ask("test-model", "hi", timeout_s=10)
    assert err.value.code == "CODEX_UNAVAILABLE" and "AUTORTL_OPENAI_API_KEY" in str(err.value)
    assert not server.requests


@pytest.mark.parametrize("status, code", [(401, "CODEX_AUTH"), (403, "CODEX_AUTH"),
                                          (429, "CODEX_QUOTA"), (500, "CODEX_NETWORK"),
                                          (503, "CODEX_NETWORK"), (404, "CODEX_UNAVAILABLE")])
def test_http_status_maps_to_retry_codes(server, status, code):
    server.status = status
    server.body = {"error": {"message": "nope", "type": "server_error", "code": str(status)}}
    with pytest.raises(CodexError) as err:
        openai_http.ask("test-model", "hi", timeout_s=10)
    assert err.value.code == code and err.value.metadata["http_status"] == status
    assert "nope" in str(err.value)


def test_redirect_is_refused_so_the_key_is_not_forwarded(server):
    server.status, server.body = 307, b""
    server.extra_headers = {"Location": server.url + "/elsewhere"}
    with pytest.raises(CodexError) as err:
        openai_http.ask("test-model", "hi", timeout_s=10)
    assert err.value.code == "CODEX_UNAVAILABLE" and len(server.requests) == 1


def test_key_echoed_by_the_server_is_redacted(server):
    server.status = 401
    server.body = {"error": {"message": f"Incorrect API key provided: {KEY}. prompt was secret-prompt-text"}}
    with pytest.raises(CodexError) as err:
        openai_http.ask("test-model", "secret-prompt-text", timeout_s=10)
    stored = str(err.value) + json.dumps(err.value.metadata)
    assert KEY not in stored and "secret-prompt-text" not in stored
    assert "[REDACTED]" in stored


def test_timeout_is_typed(server):
    server.delay = 2.0
    t0 = time.monotonic()
    with pytest.raises(CodexError) as err:
        openai_http.ask("test-model", "hi", timeout_s=0.3)
    assert err.value.code == "CODEX_TIMEOUT" and time.monotonic() - t0 < 1.5


@pytest.mark.parametrize("body", [b"not json{", b"[1, 2]", json.dumps({"choices": []}).encode(),
                                  json.dumps({"choices": [{"message": {"content": None}}]}).encode(),
                                  json.dumps({"choices": [{"message": {"content": "  "}}]}).encode()])
def test_malformed_body_is_protocol_error(server, body):
    server.body = body
    with pytest.raises(CodexError) as err:
        openai_http.ask("test-model", "hi", timeout_s=10)
    assert err.value.code == "CODEX_PROTOCOL"


def test_unreachable_endpoint_is_network(monkeypatch):
    fake = FakeServer()
    url = fake.url
    fake.close()                       # nothing listens on this port any more
    monkeypatch.setenv("AUTORTL_OPENAI_BASE_URL", url)
    monkeypatch.setenv("AUTORTL_OPENAI_API_KEY", KEY)
    with pytest.raises(CodexError) as err:
        openai_http.ask("test-model", "hi", timeout_s=5)
    assert err.value.code == "CODEX_NETWORK" and KEY not in str(err.value)


def test_bad_base_url_is_unavailable(monkeypatch):
    monkeypatch.setenv("AUTORTL_OPENAI_API_KEY", KEY)
    monkeypatch.setenv("AUTORTL_OPENAI_BASE_URL", "file:///etc/passwd")
    with pytest.raises(CodexError) as err:
        openai_http.ask("test-model", "hi", timeout_s=5)
    assert err.value.code == "CODEX_UNAVAILABLE"


@pytest.fixture
def routed(monkeypatch, tmp_path):
    monkeypatch.setattr(client, "_STATS_PATH", tmp_path / "stats.jsonl")
    monkeypatch.setattr(client.time, "sleep", Mock())


def test_client_routes_openai_and_charges_tokens(server, routed):
    budget = Budget(3, 10, 10)
    text = client.ask("generator", "make a module", system="be terse", budget=budget,
                      route_override="openai.test-model")
    assert text == "module m; endmodule"
    assert budget.llm_calls == 1
    assert budget.tokens["input_tokens"] == 120 and budget.tokens["output_tokens"] == 30
    assert budget.tokens["cached_input_tokens"] == 100
    record = json.loads(client._STATS_PATH.read_text())
    assert record["ok"] and record["entry"] == "openai.test-model"
    assert KEY not in client._STATS_PATH.read_text()


def test_client_retries_server_errors_then_raises_typed(server, routed):
    server.status, server.body = 502, {"error": "bad gateway"}
    budget = Budget(5, 10, 10)
    with pytest.raises(client.ModelCallError) as err:
        client.ask("generator", "hi", budget=budget, route_override="openai.test-model")
    assert err.value.code == "CODEX_NETWORK" and len(server.requests) == 2
    assert budget.llm_calls == 2


def test_client_stops_at_once_on_quota(server, routed):
    server.status, server.body = 429, {"error": {"message": "rate limited"}}
    with pytest.raises(client.ModelCallError) as err:
        client.ask("generator", "hi", route_override="openai.test-model")
    assert err.value.code == "CODEX_QUOTA" and len(server.requests) == 1


def test_backend_qualified_run_model_pins_the_backend(server, routed):
    assert client.ask("generator", "hi", model="openai.test-model") == "module m; endmodule"
    assert server.requests[0]["body"]["model"] == "test-model"


def test_plain_run_model_keeps_the_routed_backend(monkeypatch, routed):
    codex = Mock()
    codex.ask.return_value = ("RTL", {})
    monkeypatch.setattr(client, "_BACKENDS", {"codex": codex, "openai": Mock()})
    monkeypatch.setattr(client, "_load_routing", lambda: {
        "roles": {"generator": {"chain": ["codex.default"]}}, "defaults": {}})
    assert client.ask("generator", "hi", model="gpt-5.6-luna") == "RTL"
    assert codex.ask.call_args.args[0] == "gpt-5.6-luna"
