"""Bounded text generation using the user's existing Codex login.

User config is ignored for worker execution. Capability flags and an effective
MCP configuration check restrict the configured worker; event validation also
rejects tool trajectories. This is not a universal OS isolation guarantee, and
rejecting an event afterwards cannot undo side effects. No auth/security
environment is rewritten. max_turns remains an unenforced compatibility field.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time

MAX_EVENTS = 4096
MAX_ERROR_EVENTS = 8
MAX_MESSAGE = 400
MAX_STDERR = 1000
MAX_CONFIG_BYTES = 256 * 1024
WORKER_DISABLED_FEATURES = (
    "shell_tool", "apps", "view_image", "hooks", "plugins", "multi_agent",
    "code_mode", "computer_use", "browser_use", "image_generation",
)
TEXT_ITEM_TYPES = {"agent_message", "reasoning"}
WORKER_EVENT_TYPES = {"thread.started", "turn.started", "turn.completed", "turn.failed", "error",
                      "item.started", "item.updated", "item.completed"}


def _remaining(deadline):
    seconds = deadline - time.monotonic()
    if seconds <= 0:
        raise CodexError("CODEX_TIMEOUT", "worker deadline exhausted")
    return seconds


def _configured_mcp(executable, directory, overrides, deadline):
    """Inspect config only; never initialize MCP servers or retain transports."""
    try:
        result = subprocess.run([executable, "mcp", "list", "--json", *overrides], cwd=directory,
                                capture_output=True, text=True, encoding="utf-8", errors="replace",
                                shell=False, timeout=min(10, _remaining(deadline)))
    except subprocess.TimeoutExpired as exc:
        raise CodexError("CODEX_TIMEOUT", "worker configuration check timed out") from exc
    except OSError as exc:
        raise CodexError("CODEX_UNAVAILABLE", "worker configuration check could not launch") from exc
    if result.returncode:
        # Config output can contain private transports/env. Never include it in
        # diagnostics and never retry with weaker restrictions.
        raise CodexError("CODEX_UNAVAILABLE", "worker configuration check failed",
                         {"configuration_stage": "mcp_list", "returncode": result.returncode})
    if not isinstance(result.stdout, str) or len(result.stdout.encode("utf-8", errors="replace")) > MAX_CONFIG_BYTES:
        raise CodexError("CODEX_PROTOCOL", "worker configuration result exceeded its bound")
    try:
        records = json.loads(result.stdout)
    except (ValueError, TypeError) as exc:
        raise CodexError("CODEX_PROTOCOL", "invalid worker configuration result") from exc
    if not isinstance(records, list) or len(records) > 128:
        raise CodexError("CODEX_PROTOCOL", "invalid worker configuration result")
    servers = {}
    for record in records:
        if not isinstance(record, dict):
            raise CodexError("CODEX_PROTOCOL", "invalid worker configuration entry")
        name, enabled = record.get("name"), record.get("enabled")
        if (not isinstance(name, str) or not name or len(name) > 200 or name in servers
                or any(ord(c) < 32 or 0xD800 <= ord(c) <= 0xDFFF for c in name) or type(enabled) is not bool):
            raise CodexError("CODEX_PROTOCOL", "invalid worker configuration entry")
        servers[name] = enabled
    return servers


def _worker_config(executable, directory, deadline):
    overrides = [arg for feature in WORKER_DISABLED_FEATURES for arg in ("--disable", feature)]
    overrides += ["-c", 'web_search="disabled"']
    servers = _configured_mcp(executable, directory, [*overrides, "-c", "mcp_servers={}"], deadline)
    # Empty tables do not erase inherited entries in the tested CLI. A complete
    # disabled entry needs a transport to pass bootstrap schema validation. Use
    # an inert command, not the user's actual executable/URL/credentials.
    entries = [json.dumps(name, ensure_ascii=False) + '={command="__autortl_disabled_mcp__",enabled=false}'
               for name in sorted(servers)]
    overrides += ["-c", "mcp_servers={" + ",".join(entries) + "}"]
    effective = _configured_mcp(executable, directory, overrides, deadline)
    if any(effective.values()):
        raise CodexError("CODEX_PROTOCOL", "worker configuration still enables MCP servers")
    return overrides


def redact(text, secrets=()):
    """Redact credentials before truncation so a cut token cannot escape masking."""
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="replace")
    text = str(text or "")
    for secret in secrets:
        if secret:
            text = text.replace(secret, "[PROMPT REDACTED]")
            for line in secret.splitlines():
                if len(line.strip()) >= 8:
                    text = text.replace(line.strip(), "[PROMPT REDACTED]")
    text = re.sub(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+", "Bearer [REDACTED]", text)
    text = re.sub(r"\bsk-[A-Za-z0-9_-]+", "[REDACTED]", text)
    text = re.sub(r"(?i)((?:api[_-]?key|access[_-]?token|refresh[_-]?token|id[_-]?token|token|authorization|password|secret)[\"']?\s*[:=]\s*)(?:\"[^\"]*\"|'[^']*'|[^\s,;}]+)",
                  r"\1[REDACTED]", text)
    text = re.sub(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", "[REDACTED]", text)
    return text


def _failure_code(text, fallback):
    if re.search(r"(?i)quota|usage limit|rate.?limit|too many requests|\b429\b|insufficient_quota", text):
        return "CODEX_QUOTA"
    if re.search(r"(?i)unauthori[sz]ed|authentication|invalid.api.key|not.logged.in|login.required|\b401\b|token.expired", text):
        return "CODEX_AUTH"
    if re.search(r"(?i)connection (?:reset|refused)|network|dns|temporarily unavailable|\b(?:502|503|504)\b|stream disconnected", text):
        return "CODEX_NETWORK"
    return fallback


def _diagnostics(stdout="", stderr="", returncode=None, secrets=()):
    """Only explicit error-event fields; never retain ordinary stdout messages."""
    result = {"returncode": returncode, "errors": [], "stderr_tail": "", "diagnostics_truncated": False}
    text = stdout.decode("utf-8", errors="replace") if isinstance(stdout, bytes) else stdout or ""
    for index, line in enumerate(text.splitlines()):
        if index >= MAX_EVENTS:
            result["diagnostics_truncated"] = True
            break
        try:
            event = json.loads(line)
        except (ValueError, TypeError):
            continue
        if not isinstance(event, dict) or event.get("type") not in ("error", "turn.failed"):
            continue
        error = event.get("error")
        if isinstance(error, dict):
            message = error.get("message", "")
            code = error.get("code", "")
        else:
            message = event.get("message", error if isinstance(error, str) else "")
            code = event.get("code", "")
        message = redact(message if isinstance(message, str) else "", secrets)
        code = redact(code if isinstance(code, str) else "", secrets)[:80]
        if len(result["errors"]) >= MAX_ERROR_EVENTS:
            result["diagnostics_truncated"] = True
            continue
        result["diagnostics_truncated"] |= len(message) > MAX_MESSAGE
        result["errors"].append({"type": event["type"], "message": message[:MAX_MESSAGE], "code": code})
    clean = redact(stderr, secrets)
    # CLI stderr can contain progress, echoed prompts or serialized agent items.
    # Retain diagnostic lines only; ordinary stdout is deliberately discarded.
    lines = [line for line in clean.splitlines()
             if re.search(r"(?i)error|warn|fail|quota|limit|auth|network|connection|denied|expired|unavailable|\b(?:401|429|50[234])\b", line)
             and not re.search(r'"type"\s*:\s*"(?:item\.|agent_message|user_message)', line)]
    tail = "\n".join(lines)
    result["diagnostics_truncated"] |= len(tail) > MAX_STDERR
    result["stderr_tail"] = tail[-MAX_STDERR:]
    return result


class CodexError(RuntimeError):
    def __init__(self, code: str, message: str, metadata: dict | None = None):
        super().__init__(f"{code}: {redact(message)[:MAX_MESSAGE]}")
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


def _parse_events(stdout: str, secrets=()) -> dict:
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
        if meta["event_count"] > MAX_EVENTS:
            raise CodexError("CODEX_PROTOCOL", "event limit exceeded", meta)
        if event["type"] not in WORKER_EVENT_TYPES:
            raise CodexError("CODEX_PROTOCOL", "unsupported text-worker event", meta)
        if event["type"].startswith("item."):
            item = event.get("item")
            if (not isinstance(item, dict) or not isinstance(item.get("type"), str)
                    or item["type"] not in TEXT_ITEM_TYPES):
                # Rejection is after execution, not a side-effect prevention
                # boundary. Do not retain tool names, arguments or results.
                raise CodexError("CODEX_PROTOCOL", "tool or unsupported item in text-worker response", meta)
        if isinstance(event.get("model"), str):
            meta["model"] = redact(event["model"], secrets)[:200]
        if event["type"] == "thread.started":
            identity = event.get("thread_id")
            meta["session_id"] = redact(identity, secrets)[:200] if isinstance(identity, str) else None
        if event["type"] in ("error", "turn.failed"):
            diagnostic = _diagnostics(stdout, secrets=secrets)
            meta.update(diagnostic)
            detail = " ".join(item["code"] + " " + item["message"] for item in diagnostic["errors"])
            raise CodexError(_failure_code(detail, "CODEX_PROTOCOL"),
                             detail or "worker reported a failed turn", meta)
        if event["type"] == "turn.completed":
            completed = True
            if isinstance(event.get("usage"), dict):
                meta["usage"] = {key: value for key, value in event["usage"].items()
                                 if key in ("input_tokens", "output_tokens", "cached_input_tokens")
                                 and type(value) is int and value >= 0}
    if not completed:
        raise CodexError("CODEX_PROTOCOL", "missing completed turn", meta)
    return meta


def ask(model_alias: str, prompt: str, system: str = "",
        timeout_s: int = 180, max_turns: int = 1) -> tuple[str, dict]:
    if timeout_s <= 0:
        raise ValueError("timeout_s must be positive")
    deadline = time.monotonic() + timeout_s
    executable = os.environ.get("AUTORTL_CODEX_BIN") or shutil.which("codex")
    if not executable:
        raise CodexError("CODEX_UNAVAILABLE", "set AUTORTL_CODEX_BIN or put codex on PATH")
    instruction = ("Return only the requested response. Do not use tools or change files.\n"
                   + (f"\nTask instructions:\n{system}\n" if system else "")
                   + f"\nRequest:\n{prompt}")
    with tempfile.TemporaryDirectory(prefix="autortl-codex-") as directory:
        final = Path(directory) / "final.txt"
        config = _worker_config(executable, directory, deadline)
        cmd = [executable, "exec", "--ignore-user-config", "--strict-config",
               "--sandbox", "read-only", "--ephemeral",
               "--json", "--output-last-message", str(final),
               "--skip-git-repo-check", "-C", directory, *config]
        if model_alias and model_alias != "default":
            cmd += ["--model", model_alias]
        cmd += ["-"]
        _remaining(deadline)  # An expired configuration check must not start generation.
        try:
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, text=True, encoding="utf-8",
                                       errors="replace", cwd=directory, shell=False,
                                       start_new_session=os.name != "nt")
        except OSError as exc:
            raise CodexError("CODEX_UNAVAILABLE", "worker could not launch") from exc
        try:
            stdout, stderr = process.communicate(input=instruction, timeout=_remaining(deadline))
        except subprocess.TimeoutExpired as exc:
            _terminate_worker(process)
            diagnostic = _diagnostics(exc.output, exc.stderr, process.returncode, (prompt, system, instruction))
            raise CodexError("CODEX_TIMEOUT", "worker timed out", diagnostic) from exc
        except BaseException:
            _terminate_worker(process)
            raise
        if process.returncode != 0:
            diagnostic = _diagnostics(stdout, stderr, process.returncode, (prompt, system, instruction))
            detail = " ".join(item["code"] + " " + item["message"] for item in diagnostic["errors"])
            code = _failure_code(detail + " " + diagnostic["stderr_tail"], "CODEX_UNAVAILABLE")
            raise CodexError(code, f"worker exited {process.returncode}: " + (detail or diagnostic["stderr_tail"]), diagnostic)
        try:
            meta = _parse_events(stdout, (prompt, system, instruction))
        except CodexError as exc:
            exc.metadata.update(_diagnostics(stdout, stderr, process.returncode, (prompt, system, instruction)))
            raise
        meta["requested_model"] = None if model_alias == "default" else model_alias
        meta["max_turns_enforced"] = False
        meta["worker_policy"] = "restricted_text_v1"
        meta["mcp_configuration_checked"] = True
        meta["tool_items_observed"] = 0
        try:
            response = final.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise CodexError("CODEX_PROTOCOL", "missing final response file", meta) from exc
        if not response:
            raise CodexError("CODEX_PROTOCOL", "empty final response", meta)
        return response, meta
