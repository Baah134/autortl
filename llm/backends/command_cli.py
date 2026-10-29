"""Any AI command line as a backend: the prompt goes in on stdin, the answer comes out on stdout.

Used through a `kind: command` endpoint (llm/endpoints.py). The command is the
user's own configuration and runs as an argument list (never through a shell)
from an empty temporary folder. Model output never reaches its arguments; only
the endpoint's own model name, through model_flag, does. Timeouts kill the
whole process tree. Errors reuse the Codex adapter's codes and redaction, so
client retries behave the same for every backend. A command is not sandboxed
by AutoRTL: give it no tools or permissions it does not need.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile

from .codex_cli import CodexError, MAX_STDERR, _failure_code, _terminate_worker, redact


def ask(model_alias, prompt, system="", timeout_s=180, max_turns=1, *, argv, model_flag=None, label="command"):
    if timeout_s <= 0:
        raise ValueError("timeout_s must be positive")
    executable = shutil.which(argv[0]) or argv[0]
    cmd = [executable, *argv[1:]]
    if model_alias and model_alias != "default":
        if not model_flag:
            raise CodexError("CODEX_UNAVAILABLE", f"endpoint {label} has no model_flag; use {label}.default")
        cmd += [model_flag, model_alias]
    request = ("Return only the requested response. Do not use tools or change files.\n"
               + (f"\nTask instructions:\n{system}\n" if system else "") + f"\nRequest:\n{prompt}")
    secrets = (prompt, system, request)
    meta = {"model": None, "usage": None, "cost_usd": None, "session_id": None, "endpoint": label,
            "requested_model": None if model_alias == "default" else model_alias, "max_turns_enforced": False}
    with tempfile.TemporaryDirectory(prefix="autortl-command-") as scratch:
        try:
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       text=True, encoding="utf-8", errors="replace", cwd=scratch, shell=False,
                                       start_new_session=os.name != "nt")
        except OSError as exc:
            raise CodexError("CODEX_UNAVAILABLE", f"endpoint {label}: {argv[0]} could not launch: {exc}", meta) from None
        try:
            stdout, stderr = process.communicate(input=request, timeout=timeout_s)
        except subprocess.TimeoutExpired:
            _terminate_worker(process)
            raise CodexError("CODEX_TIMEOUT", f"endpoint {label} timed out after {timeout_s}s", meta) from None
        except BaseException:
            _terminate_worker(process)
            raise
    tail = redact(stderr or "", secrets)[-MAX_STDERR:]
    if process.returncode != 0:
        meta["stderr_tail"] = tail
        raise CodexError(_failure_code(tail, "CODEX_UNAVAILABLE"),
                         f"endpoint {label} exited {process.returncode}: {tail[-300:]}", meta)
    text = (stdout or "").strip()
    if not text:
        raise CodexError("CODEX_PROTOCOL", f"endpoint {label} printed nothing", meta)
    return text, meta
