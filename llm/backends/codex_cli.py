"""Bounded Codex CLI calls using the user's existing login and configuration.

No API key or authentication changes. Read-only is an OS sandbox, not a
promise that the CLI has no tools. max_turns is retained for adapter API
compatibility; only timeout_s is enforced by this adapter.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile


class CodexError(RuntimeError):
    def __init__(self, code: str, message: str, metadata: dict | None = None):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.metadata = metadata or {}


def _terminate_worker(process: subprocess.Popen) -> None:
    """Kill only this worker's process tree, then reap its direct process."""
    if os.name == "nt":
        try:
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                           capture_output=True, timeout=10, shell=False)
        except (OSError, subprocess.TimeoutExpired):
            pass
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except OSError:
            pass
    try:
        if process.poll() is None:
            process.kill()
    except OSError:
        pass
    try:
        process.communicate(timeout=5)
    except (subprocess.TimeoutExpired, OSError):
        # A descendant holding inherited pipes must not extend our deadline.
        # Windows communicate uses reader threads; closing their streams can
        # block on a reader lock if a surviving descendant still owns a pipe.
        if os.name != "nt":
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream:
                    try:
                        stream.close()
                    except OSError:
                        pass
        try:
            process.wait(timeout=5)
        except (subprocess.TimeoutExpired, OSError):
            pass  # Preserve the original timeout/cancellation outcome.


def _parse_events(stdout: str) -> dict:
    meta = {"model": None, "usage": None, "cost_usd": None,
            "session_id": None, "event_count": 0}
    completed = False
    for line in stdout.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except (ValueError, TypeError) as exc:
            raise CodexError("CODEX_PROTOCOL", "invalid JSONL event", meta) from exc
        if not isinstance(event, dict) or not isinstance(event.get("type"), str):
            raise CodexError("CODEX_PROTOCOL", "invalid event shape", meta)
        meta["event_count"] += 1
        if isinstance(event.get("model"), str):
            meta["model"] = event["model"]
        if event["type"] == "thread.started":
            meta["session_id"] = event.get("thread_id")
        if event["type"] in ("error", "turn.failed"):
            raise CodexError("CODEX_PROTOCOL", "worker reported a failed turn", meta)
        if event["type"] == "turn.completed":
            completed = True
            if isinstance(event.get("usage"), dict):
                meta["usage"] = event["usage"]
    if not completed:
        raise CodexError("CODEX_PROTOCOL", "missing completed turn", meta)
    return meta


def ask(model_alias: str, prompt: str, system: str = "",
        timeout_s: int = 180, max_turns: int = 1) -> tuple[str, dict]:
    if timeout_s <= 0:
        raise ValueError("timeout_s must be positive")
    executable = os.environ.get("AUTORTL_CODEX_BIN") or shutil.which("codex")
    if not executable:
        raise CodexError("CODEX_UNAVAILABLE", "set AUTORTL_CODEX_BIN or put codex on PATH")
    instruction = ("Return only the requested response. Do not use tools or change files.\n"
                   + (f"\nTask instructions:\n{system}\n" if system else "")
                   + f"\nRequest:\n{prompt}")
    with tempfile.TemporaryDirectory(prefix="autortl-codex-") as directory:
        final = Path(directory) / "final.txt"
        cmd = [executable, "exec", "--sandbox", "read-only", "--ephemeral",
               "--json", "--output-last-message", str(final),
               "--skip-git-repo-check", "-C", directory]
        if model_alias and model_alias != "default":
            cmd += ["--model", model_alias]
        cmd += ["-"]
        try:
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, text=True, encoding="utf-8",
                                       errors="replace", cwd=directory, shell=False,
                                       start_new_session=os.name != "nt")
        except OSError as exc:
            raise CodexError("CODEX_UNAVAILABLE", "worker could not launch") from exc
        try:
            stdout, _stderr = process.communicate(input=instruction, timeout=timeout_s)
        except subprocess.TimeoutExpired as exc:
            _terminate_worker(process)
            raise CodexError("CODEX_TIMEOUT", "worker timed out") from exc
        except BaseException:
            _terminate_worker(process)
            raise
        if process.returncode != 0:
            raise CodexError("CODEX_UNAVAILABLE", f"worker exited {process.returncode}")
        meta = _parse_events(stdout)
        meta["requested_model"] = None if model_alias == "default" else model_alias
        meta["max_turns_enforced"] = False
        try:
            response = final.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise CodexError("CODEX_PROTOCOL", "missing final response file", meta) from exc
        if not response:
            raise CodexError("CODEX_PROTOCOL", "empty final response", meta)
        return response, meta
