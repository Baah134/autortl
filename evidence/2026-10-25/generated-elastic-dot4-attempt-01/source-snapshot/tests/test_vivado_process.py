"""Mocked process lifecycle tests; never launch Vivado or kill real processes."""
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from autortl import vivado
from autortl.triage import classify, FailureKind


@pytest.fixture
def worker(monkeypatch):
    process = Mock(pid=12345, returncode=0)
    process.communicate.return_value = ("normal stdout", "normal stderr")
    process.poll.return_value = None
    monkeypatch.setattr(vivado.subprocess, "Popen", Mock(return_value=process))
    monkeypatch.setattr(vivado.subprocess, "run", Mock(return_value=SimpleNamespace(returncode=0)))
    # Replace module reference, never global os.name (Path depends on it).
    monkeypatch.setattr(vivado, "os", SimpleNamespace(name="nt", killpg=Mock()))
    return process


def run_tool(tmp_path):
    return vivado._run(["vivado.bat", "-version"], tmp_path, 3, tmp_path / "tool.log")


def test_normal_execution_keeps_both_streams_without_cleanup(tmp_path, worker):
    rc, out = run_tool(tmp_path)
    assert rc == 0
    assert out == "normal stdout\nnormal stderr"
    assert (tmp_path / "tool.log").read_text() == out
    worker.communicate.assert_called_once_with(timeout=3)
    vivado.subprocess.run.assert_not_called()
    worker.kill.assert_not_called()
    kwargs = vivado.subprocess.Popen.call_args.kwargs
    assert kwargs["shell"] is False
    assert kwargs["start_new_session"] is False
    assert vivado.vivado_seconds() >= 0


def test_timeout_preserves_partial_and_final_logs_without_duplicates(tmp_path, worker):
    worker.communicate.side_effect = [
        subprocess.TimeoutExpired("vivado", 3, output=b"started\n", stderr=b"warning\n"),
        ("started\nlast output\n", "warning\nlast error\n"),
    ]
    rc, out = run_tool(tmp_path)
    assert rc == 124
    assert out.count("started\n") == 1
    assert "last output" in out and "last error" in out and "warning" in out
    assert "timed out after 3s" in out
    assert classify(out) == FailureKind.INFRA
    assert (tmp_path / "tool.log").read_text() == out
    vivado.subprocess.run.assert_called_once_with(
        ["taskkill", "/PID", "12345", "/T", "/F"],
        capture_output=True, timeout=10, shell=False)
    worker.kill.assert_called_once()


def test_timeout_with_empty_drain_keeps_exception_output(tmp_path, worker):
    worker.communicate.side_effect = [
        subprocess.TimeoutExpired("vivado", 3, output=b"kept\xff", stderr="diagnostic"),
        (None, None),
    ]
    rc, out = run_tool(tmp_path)
    assert rc == 124 and "kept" in out and "diagnostic" in out


@pytest.mark.parametrize("error,rc", [
    (FileNotFoundError("missing executable"), 127),
    (PermissionError("Permission denied"), 126),
    (OSError("invalid executable format"), 126),
])
def test_launch_failure_is_logged_without_cleanup(tmp_path, worker, error, rc):
    vivado.subprocess.Popen.side_effect = error
    actual, out = run_tool(tmp_path)
    assert actual == rc
    assert str(error) in out
    assert (tmp_path / "tool.log").read_text() == out
    vivado.subprocess.run.assert_not_called()


def test_cancel_cleans_owned_tree_and_preserves_output_then_reraises(tmp_path, worker):
    worker.communicate.side_effect = [KeyboardInterrupt(), ("partial result", "stderr")]
    with pytest.raises(KeyboardInterrupt):
        run_tool(tmp_path)
    text = (tmp_path / "tool.log").read_text()
    assert "partial result" in text and "Tool execution cancelled" in text
    assert vivado.subprocess.run.call_args.args[0] == ["taskkill", "/PID", "12345", "/T", "/F"]


def test_cleanup_failure_and_inherited_pipe_are_bounded_and_reported(tmp_path, worker):
    worker.communicate.side_effect = [
        subprocess.TimeoutExpired("vivado", 3, output=b"first"),
        subprocess.TimeoutExpired("vivado", 5, output=b"first last"),
    ]
    vivado.subprocess.run.side_effect = subprocess.TimeoutExpired("taskkill", 10)
    worker.wait.side_effect = subprocess.TimeoutExpired("vivado", 5)
    rc, out = run_tool(tmp_path)
    assert rc == 124
    assert "first last" in out
    assert "process-tree cleanup failed" in out
    assert "output may be incomplete" in out
    assert "could not be reaped" in out
    worker.wait.assert_called_once_with(timeout=5)
    # Closing pipes held by communicate reader threads could block indefinitely.
    worker.stdout.close.assert_not_called()
    worker.stderr.close.assert_not_called()


def test_posix_worker_uses_private_session_and_group_cleanup(tmp_path, worker, monkeypatch):
    fake_os = SimpleNamespace(name="posix", killpg=Mock())
    monkeypatch.setattr(vivado, "os", fake_os)
    monkeypatch.setattr(vivado, "signal", SimpleNamespace(SIGKILL=9))
    worker.communicate.side_effect = [
        subprocess.TimeoutExpired("vivado", 3), ("partial", "")]
    worker.poll.return_value = 0
    rc, _ = run_tool(tmp_path)
    assert rc == 124
    assert vivado.subprocess.Popen.call_args.kwargs["start_new_session"] is True
    fake_os.killpg.assert_called_once_with(12345, vivado.signal.SIGKILL)
    vivado.subprocess.run.assert_not_called()
    worker.kill.assert_not_called()
