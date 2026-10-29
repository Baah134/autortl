"""User-defined endpoints: any OpenAI-compatible server or any AI command line, per role."""
import http.server
import json
import sys
import threading

import pytest

from llm import client, endpoints
from llm.backends import command_cli
from llm.backends.codex_cli import CodexError
from tests.test_curriculum import curriculum, records  # noqa: F401  (fixture reuse)

ECHO = r'''
import sys
request = sys.stdin.read()
model = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "none"
print("```verilog\nmodule echo_%s; endmodule\n```" % model.replace("-", "_"))
print("saw-request" if "Request:" in request else "no-request")
'''


@pytest.fixture
def script(tmp_path):
    def make(body):
        path = tmp_path / f"ai_{len(list(tmp_path.glob('ai_*.py')))}.py"
        path.write_text(body, encoding="utf-8")
        return str(path)
    return make


@pytest.fixture
def configured(tmp_path, monkeypatch):
    def write(entries):
        path = tmp_path / "endpoints.yaml"
        path.write_text(json.dumps({"endpoints": entries}), encoding="utf-8")
        monkeypatch.setenv("AUTORTL_ENDPOINTS", str(path))
        return path
    return write


def test_a_command_endpoint_gets_the_prompt_on_stdin_and_the_model_by_flag(script):
    text, meta = command_cli.ask("tiny-model", "make a module", "be terse", timeout_s=30,
                                 argv=[sys.executable, script(ECHO)], model_flag="--model", label="echo")
    assert "module echo_tiny_model" in text and "saw-request" in text
    assert meta["endpoint"] == "echo" and meta["requested_model"] == "tiny-model"


def test_command_failures_map_onto_the_retry_codes(script):
    slow = script("import time; time.sleep(30)")
    with pytest.raises(CodexError) as timeout:
        command_cli.ask("default", "p", timeout_s=1, argv=[sys.executable, slow], label="slow")
    assert timeout.value.code == "CODEX_TIMEOUT"
    limited = script("import sys; sys.stderr.write('429 rate limit reached'); sys.exit(2)")
    with pytest.raises(CodexError) as quota:
        command_cli.ask("default", "p", timeout_s=30, argv=[sys.executable, limited], label="l")
    assert quota.value.code == "CODEX_QUOTA"
    silent = script("pass")
    with pytest.raises(CodexError) as empty:
        command_cli.ask("default", "p", timeout_s=30, argv=[sys.executable, silent], label="s")
    assert empty.value.code == "CODEX_PROTOCOL"
    with pytest.raises(CodexError, match="no model_flag"):
        command_cli.ask("named", "p", timeout_s=30, argv=[sys.executable, silent], label="s")


def test_every_role_can_be_routed_to_a_command_endpoint(configured, script, tmp_path, monkeypatch):
    configured({"mine": {"kind": "command", "argv": [sys.executable, script(ECHO)], "model_flag": "--model"}})
    monkeypatch.setattr(client, "_STATS_PATH", tmp_path / "stats.jsonl")
    text = client.ask("generator", "make a module", model="mine.small")
    assert client.extract_verilog(text) == "module echo_small; endmodule"


@pytest.mark.parametrize("entry, message", [
    ({"Bad": {"kind": "command", "argv": ["x"]}}, "lowercase"),
    ({"codex": {"kind": "command", "argv": ["x"]}}, "not be codex"),
    ({"x": {"kind": "openai", "base_url": "http://h/v1", "api_key": "sk-1"}}, "api_key_env"),
    ({"x": {"kind": "openai", "base_url": "ftp://h"}}, "base_url"),
    ({"x": {"kind": "openai", "base_url": "http://h", "api_key_env": "has space"}}, "variable name"),
    ({"x": {"kind": "command", "argv": []}}, "argv"),
    ({"x": {"kind": "command", "argv": ["x"], "model_flag": "model"}}, "model_flag"),
    ({"x": {"kind": "magic"}}, "kind"),
])
def test_malformed_endpoints_are_refused_with_the_reason(configured, entry, message):
    configured(entry)
    with pytest.raises(endpoints.EndpointError, match=message):
        endpoints.load()


def test_no_file_means_no_endpoints_but_a_named_missing_file_is_an_error(tmp_path, monkeypatch):
    monkeypatch.delenv("AUTORTL_ENDPOINTS", raising=False)
    monkeypatch.setattr(endpoints, "LOCAL", tmp_path / "absent.yaml")
    assert endpoints.load() == {}
    monkeypatch.setenv("AUTORTL_ENDPOINTS", str(tmp_path / "missing.yaml"))
    with pytest.raises(endpoints.EndpointError, match="missing"):
        endpoints.load()


class Fake(http.server.BaseHTTPRequestHandler):
    seen = []

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        Fake.seen.append((self.headers.get("Authorization"), body["model"]))
        reply = json.dumps({"choices": [{"message": {"content": "ok"}}],
                            "usage": {"prompt_tokens": 3, "completion_tokens": 1}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(reply)))
        self.end_headers()
        self.wfile.write(reply)

    def log_message(self, *args):
        pass


@pytest.fixture
def server():
    httpd = http.server.HTTPServer(("127.0.0.1", 0), Fake)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    Fake.seen.clear()
    yield f"http://127.0.0.1:{httpd.server_port}/v1"
    httpd.shutdown()


def test_openai_endpoints_send_a_key_only_when_they_name_one(configured, server, tmp_path, monkeypatch):
    configured({"local": {"kind": "openai", "base_url": server},
                "hosted": {"kind": "openai", "base_url": server, "api_key_env": "HOSTED_KEY"}})
    monkeypatch.setattr(client, "_STATS_PATH", tmp_path / "stats.jsonl")
    monkeypatch.setenv("HOSTED_KEY", "sk-hosted-1234")
    assert client.ask("planner", "p", model="local.llama3.1") == "ok"
    assert client.ask("planner", "p", model="hosted.big-model") == "ok"
    assert Fake.seen == [(None, "llama3.1"), ("Bearer sk-hosted-1234", "big-model")]
    monkeypatch.delenv("HOSTED_KEY")
    with pytest.raises(client.ModelCallError, match="HOSTED_KEY"):
        client.ask("planner", "p", model="hosted.big-model")


def test_doctor_lists_endpoints_as_optional(configured, script, monkeypatch):
    from autortl import doctor
    configured({"mine": {"kind": "command", "argv": [sys.executable, script(ECHO)]},
                "absent": {"kind": "command", "argv": ["no-such-ai-cli"]},
                "hosted": {"kind": "openai", "base_url": "https://api.example.com/v1", "api_key_env": "UNSET_KEY_X"}})
    monkeypatch.delenv("UNSET_KEY_X", raising=False)
    checks = {c.name: c for c in doctor.endpoint_checks()}
    assert checks["endpoint mine"].status == "OK"
    assert checks["endpoint absent"].status == "WARN" and not checks["endpoint absent"].required
    assert checks["endpoint hosted"].status == "WARN" and "UNSET_KEY_X" in checks["endpoint hosted"].fix


def test_the_endpoint_definition_is_part_of_the_cohort(curriculum, configured):  # noqa: F811
    from curriculum import runner
    _, _, output = curriculum
    path = configured({"mine": {"kind": "command", "argv": ["ai-v1"]}})
    assert runner.run_tier(0, output_root=output, model="mine.m") == 0
    path.write_text(json.dumps({"endpoints": {"mine": {"kind": "command", "argv": ["ai-v2"]}}}), encoding="utf-8")
    assert runner.run_tier(0, output_root=output, model="mine.m") == 0
    first, second = records()[-2:]
    assert first["runtime_identity"]["model_endpoint_sha256"] != second["runtime_identity"]["model_endpoint_sha256"]
    assert first["cohort"] != second["cohort"] and second["consecutive_qualifying_runs"] == 1
