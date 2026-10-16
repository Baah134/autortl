import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from llm.backends import codex_cli


@pytest.fixture(autouse=True)
def temporary_workspace(monkeypatch, tmp_path):
    monkeypatch.setattr(codex_cli.tempfile, "tempdir", str(tmp_path))


@pytest.fixture
def events_file(tmp_path):
    path = tmp_path / "events.jsonl"
    events = [
        {"type": "thread.started", "thread_id": "session-1"},
        {"type": "item.completed", "item": {"type": "agent_message", "text": "draft"}},
        {"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 5}},
    ]
    path.write_text("\n".join(json.dumps(e) for e in events), encoding="utf-8")
    return path


def install_process(monkeypatch, events_file, response="module m; endmodule", returncode=0):
    captured = {}
    process = Mock(returncode=returncode, pid=12345)

    def spawn(cmd, **kwargs):
        captured.update(cmd=cmd, kwargs=kwargs)
        final = Path(cmd[cmd.index("--output-last-message") + 1])
        if response is not None:
            final.write_text(response, encoding="utf-8")
        process.communicate.return_value = (events_file.read_text(encoding="utf-8"), "")
        return process

    monkeypatch.setenv("AUTORTL_CODEX_BIN", "configured-codex.exe")
    monkeypatch.setattr(codex_cli.subprocess, "Popen", spawn)
    return process, captured


def test_default_invocation_stdin_isolation_and_metadata(monkeypatch, events_file):
    process, captured = install_process(monkeypatch, events_file)
    text, meta = codex_cli.ask("default", "RTL request", "contract law", timeout_s=12)
    cmd = captured["cmd"]
    assert cmd[0] == "configured-codex.exe"
    assert cmd[cmd.index("--sandbox") + 1] == "read-only"
    assert "--ephemeral" in cmd and "--json" in cmd and cmd[-1] == "-"
    assert "--model" not in cmd and "RTL request" not in cmd
    assert captured["kwargs"]["shell"] is False
    directory = cmd[cmd.index("-C") + 1]
    assert captured["kwargs"]["cwd"] == directory
    assert not Path(directory).exists()
    assert process.communicate.call_args.kwargs["timeout"] == 12
    prompt = process.communicate.call_args.kwargs["input"]
    assert "RTL request" in prompt and "contract law" in prompt
    assert text.startswith("module m")
    assert meta["session_id"] == "session-1"
    assert meta["usage"]["output_tokens"] == 5
    assert meta["cost_usd"] is None and meta["model"] is None
    assert meta["requested_model"] is None and not meta["max_turns_enforced"]


def test_explicit_model_and_path_lookup(monkeypatch, events_file):
    _, captured = install_process(monkeypatch, events_file)
    monkeypatch.delenv("AUTORTL_CODEX_BIN")
    monkeypatch.setattr(codex_cli.shutil, "which", lambda name: "path-codex")
    _, meta = codex_cli.ask("chosen-model", "request")
    assert captured["cmd"][0] == "path-codex"
    assert captured["cmd"][captured["cmd"].index("--model") + 1] == "chosen-model"
    assert meta["requested_model"] == "chosen-model"


@pytest.mark.parametrize("response", [None, "", "  \n"])
def test_missing_or_empty_final_rejected(monkeypatch, events_file, response):
    install_process(monkeypatch, events_file, response=response)
    with pytest.raises(codex_cli.CodexError, match="CODEX_PROTOCOL"):
        codex_cli.ask("default", "request")


@pytest.mark.parametrize("events", [
    "not json", "[]", '{}',
    '{"type":"thread.started"}',
    '{"type":"turn.completed"}\n{"type":"turn.failed"}',
    '{"type":"error"}\n{"type":"turn.completed"}',
])
def test_invalid_events_reject_even_nonempty_final(monkeypatch, events_file, events):
    events_file.write_text(events, encoding="utf-8")
    install_process(monkeypatch, events_file)
    with pytest.raises(codex_cli.CodexError, match="CODEX_PROTOCOL"):
        codex_cli.ask("default", "request")


def test_unknown_usage_remains_unknown():
    meta = codex_cli._parse_events('{"type":"turn.completed","model":"actual-model"}')
    assert meta["usage"] is None and meta["cost_usd"] is None
    assert meta["model"] == "actual-model"


def test_nonzero_exit_rejects_final(monkeypatch, events_file):
    install_process(monkeypatch, events_file, returncode=1)
    with pytest.raises(codex_cli.CodexError, match="CODEX_UNAVAILABLE"):
        codex_cli.ask("default", "request")


def test_missing_executable(monkeypatch):
    monkeypatch.delenv("AUTORTL_CODEX_BIN", raising=False)
    monkeypatch.setattr(codex_cli.shutil, "which", lambda name: None)
    with pytest.raises(codex_cli.CodexError, match="CODEX_UNAVAILABLE"):
        codex_cli.ask("default", "request")


def test_launch_error(monkeypatch):
    monkeypatch.setenv("AUTORTL_CODEX_BIN", "missing")
    monkeypatch.setattr(codex_cli.subprocess, "Popen", Mock(side_effect=OSError("missing")))
    with pytest.raises(codex_cli.CodexError, match="CODEX_UNAVAILABLE"):
        codex_cli.ask("default", "request")


def test_timeout_cleans_up_owned_worker(monkeypatch):
    monkeypatch.setenv("AUTORTL_CODEX_BIN", "codex")
    process = Mock(pid=12345)
    process.communicate.side_effect = subprocess.TimeoutExpired("codex", 1)
    monkeypatch.setattr(codex_cli.subprocess, "Popen", Mock(return_value=process))
    cleanup = Mock()
    monkeypatch.setattr(codex_cli, "_terminate_worker", cleanup)
    with pytest.raises(codex_cli.CodexError, match="CODEX_TIMEOUT"):
        codex_cli.ask("default", "request", timeout_s=1)
    cleanup.assert_called_once_with(process)


def test_interrupt_cleans_up_owned_worker(monkeypatch):
    monkeypatch.setenv("AUTORTL_CODEX_BIN", "codex")
    process = Mock(pid=12345)
    process.communicate.side_effect = KeyboardInterrupt()
    monkeypatch.setattr(codex_cli.subprocess, "Popen", Mock(return_value=process))
    cleanup = Mock()
    monkeypatch.setattr(codex_cli, "_terminate_worker", cleanup)
    with pytest.raises(KeyboardInterrupt):
        codex_cli.ask("default", "request")
    cleanup.assert_called_once_with(process)


def test_windows_tree_cleanup_uses_owned_pid(monkeypatch):
    monkeypatch.setattr(codex_cli.os, "name", "nt")
    run = Mock()
    monkeypatch.setattr(codex_cli.subprocess, "run", run)
    process = Mock(pid=12345)
    process.poll.return_value = None
    codex_cli._terminate_worker(process)
    assert run.call_args.args[0] == ["taskkill", "/PID", "12345", "/T", "/F"]
    assert run.call_args.kwargs["shell"] is False
    process.kill.assert_called_once()
    process.communicate.assert_called_once_with(timeout=5)


def test_cleanup_fallback_on_tree_kill_failure(monkeypatch):
    monkeypatch.setattr(codex_cli.os, "name", "nt")
    monkeypatch.setattr(codex_cli.subprocess, "run", Mock(side_effect=OSError("unavailable")))
    process = Mock(pid=12345)
    process.poll.return_value = None
    process.communicate.side_effect = subprocess.TimeoutExpired("codex", 5)
    codex_cli._terminate_worker(process)
    process.kill.assert_called_once()
    process.wait.assert_called_once_with(timeout=5)
    process.stdout.close.assert_not_called()
    process.stderr.close.assert_not_called()
    process.stdin.close.assert_not_called()


@pytest.mark.parametrize("outcome", [subprocess.TimeoutExpired("codex", 1), KeyboardInterrupt()])
def test_cleanup_wait_failure_preserves_original_outcome(monkeypatch, outcome):
    monkeypatch.setenv("AUTORTL_CODEX_BIN", "codex")
    monkeypatch.setattr(codex_cli.os, "name", "nt")
    monkeypatch.setattr(codex_cli.subprocess, "run", Mock())
    process = Mock(pid=12345)
    process.communicate.side_effect = [outcome, subprocess.TimeoutExpired("codex", 5)]
    process.wait.side_effect = subprocess.TimeoutExpired("codex", 5)
    monkeypatch.setattr(codex_cli.subprocess, "Popen", Mock(return_value=process))
    expected = KeyboardInterrupt if isinstance(outcome, KeyboardInterrupt) else codex_cli.CodexError
    with pytest.raises(expected):
        codex_cli.ask("default", "request")
    process.wait.assert_called_once_with(timeout=5)
    process.stdout.close.assert_not_called()
