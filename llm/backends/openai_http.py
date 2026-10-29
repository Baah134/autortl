"""Bounded calls to any OpenAI-compatible chat-completions HTTP API.

Configuration comes from the environment only, never from repo files:

    AUTORTL_OPENAI_API_KEY   required; sent as a Bearer token, never stored
    AUTORTL_OPENAI_BASE_URL  default https://api.openai.com/v1 (any server
                             that serves POST <base>/chat/completions, for
                             example a local Ollama or vLLM endpoint)
    AUTORTL_OPENAI_MODEL     model used when the routing alias is `default`

Failures raise codex_cli.CodexError with the same codes the client already
retries on, so routing behaves identically across backends. Every error text
is redacted (API key, prompt, system text) before it is stored. Redirects are
refused so the Authorization header never reaches another host, and loopback
endpoints bypass any configured proxy. Standard library only.
"""
from __future__ import annotations

import http.client
import json
import os
import socket
import time
import urllib.error
import urllib.parse
import urllib.request

from .codex_cli import CodexError, MAX_MESSAGE, redact

DEFAULT_BASE_URL = "https://api.openai.com/v1"
MAX_RESPONSE_BYTES = 16 * 1024 * 1024
MAX_ERROR_BYTES = 64 * 1024
_CHUNK = 64 * 1024
_LOOPBACK = ("localhost", "127.0.0.1", "::1")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """A redirect would forward the Authorization header; refuse it instead."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _scrub(text, key, secrets=()):
    text = str(text or "")
    if key and len(key) >= 6:      # shorter values are placeholder keys, not secrets
        text = text.replace(key, "[REDACTED]")
    return redact(text, secrets)


def _endpoint(base_url=None):
    base = (base_url or os.environ.get("AUTORTL_OPENAI_BASE_URL") or DEFAULT_BASE_URL).strip().rstrip("/")
    try:
        parts = urllib.parse.urlsplit(base)
        port = parts.port
    except ValueError:
        parts, port = None, None
    if parts is None or parts.scheme not in ("http", "https") or not parts.hostname:
        raise CodexError("CODEX_UNAVAILABLE",
                         "AUTORTL_OPENAI_BASE_URL must be an http(s) URL such as https://api.openai.com/v1")
    # Diagnostics name only scheme, host and port; never userinfo, path or query.
    shown = f"[{parts.hostname}]" if ":" in parts.hostname else parts.hostname
    origin = f"{parts.scheme}://{shown}" + (f":{port}" if port else "")
    return base + "/chat/completions", parts.hostname, origin


def _opener(host):
    handlers = [_NoRedirect()]
    if host in _LOOPBACK:
        handlers.append(urllib.request.ProxyHandler({}))
    return urllib.request.build_opener(*handlers)


def _read(resp, limit, deadline):
    chunks, size = [], 0
    while True:
        if time.monotonic() > deadline:
            raise TimeoutError("response deadline exceeded")
        chunk = resp.read(min(_CHUNK, limit + 1 - size))
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)
        size += len(chunk)
        if size > limit:
            raise OverflowError("response too large")


def _status_code(status):
    if status in (401, 403):
        return "CODEX_AUTH"
    if status == 429:
        return "CODEX_QUOTA"
    if status == 408:
        return "CODEX_TIMEOUT"
    if status >= 500:
        return "CODEX_NETWORK"
    return "CODEX_UNAVAILABLE"     # redirects and other refusals: not retryable


def _error_detail(body, key, secrets):
    text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body or "")
    try:
        data = json.loads(text)
    except ValueError:
        data = None
    if isinstance(data, dict):
        error = data.get("error")
        if isinstance(error, dict):
            text = " ".join(str(error.get(k) or "") for k in ("code", "type", "message")).strip()
        elif isinstance(error, str):
            text = error
        elif isinstance(data.get("message"), str):
            text = data["message"]
    return _scrub(text, key, secrets)[:MAX_MESSAGE]


def _usage(raw):
    if not isinstance(raw, dict):
        return None
    details = raw.get("prompt_tokens_details")
    pairs = (("input_tokens", raw.get("prompt_tokens")),
             ("output_tokens", raw.get("completion_tokens")),
             ("cached_input_tokens", details.get("cached_tokens") if isinstance(details, dict) else None))
    return {name: value for name, value in pairs if type(value) is int and value >= 0}


def _content(message):
    content = message.get("content") if isinstance(message, dict) else None
    if isinstance(content, list):   # some servers return typed content parts
        content = "".join(part.get("text", "") for part in content
                          if isinstance(part, dict) and isinstance(part.get("text"), str))
    return content if isinstance(content, str) else None


def ask(model_alias: str, prompt: str, system: str = "",
        timeout_s: int = 180, max_turns: int = 1, *, base_url=None, api_key_env=None,
        label="openai") -> tuple[str, dict]:
    """base_url/api_key_env come from a user endpoint (llm/endpoints.py); without
    them this is the built-in backend configured by AUTORTL_OPENAI_*."""
    if timeout_s <= 0:
        raise ValueError("timeout_s must be positive")
    if base_url is None:
        key = (os.environ.get("AUTORTL_OPENAI_API_KEY") or "").strip()
        if not key:
            raise CodexError("CODEX_UNAVAILABLE",
                             "set AUTORTL_OPENAI_API_KEY to use the openai backend")
        model = model_alias if model_alias and model_alias != "default" else \
            (os.environ.get("AUTORTL_OPENAI_MODEL") or "").strip()
        if not model:
            raise CodexError("CODEX_UNAVAILABLE",
                             "openai.default needs AUTORTL_OPENAI_MODEL, or name the model (openai.<model>)")
    else:
        # A user endpoint sends a key only when it names the variable holding one.
        key = (os.environ.get(api_key_env) or "").strip() if api_key_env else ""
        if api_key_env and not key:
            raise CodexError("CODEX_UNAVAILABLE", f"endpoint {label}: set {api_key_env} (it holds the API key)")
        model = model_alias if model_alias and model_alias != "default" else ""
        if not model:
            raise CodexError("CODEX_UNAVAILABLE", f"endpoint {label} needs a model name: use {label}.<model>")
    url, host, origin = _endpoint(base_url)
    secrets = (prompt, system)
    meta = {"model": None, "usage": None, "cost_usd": None, "session_id": None,
            "requested_model": None if model_alias == "default" else model_alias,
            "max_turns_enforced": False, "endpoint": origin, "http_status": None}
    messages = ([{"role": "system", "content": system}] if system else []) + \
               [{"role": "user", "content": prompt}]
    request = urllib.request.Request(
        url, data=json.dumps({"model": model, "messages": messages}).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json",
                 **({"Authorization": f"Bearer {key}"} if key else {})},
        method="POST")
    deadline = time.monotonic() + timeout_s
    try:
        with _opener(host).open(request, timeout=timeout_s) as resp:
            meta["http_status"] = resp.status
            body = _read(resp, MAX_RESPONSE_BYTES, deadline)
    except urllib.error.HTTPError as exc:
        meta["http_status"] = exc.code
        try:
            detail = _error_detail(_read(exc, MAX_ERROR_BYTES, deadline), key, secrets)
        except (OSError, OverflowError, http.client.HTTPException):
            detail = ""
        finally:
            exc.close()
        meta["error"] = detail
        raise CodexError(_status_code(exc.code), f"HTTP {exc.code} from {origin}"
                         + (f": {detail}" if detail else ""), meta) from None
    except (TimeoutError, socket.timeout):
        raise CodexError("CODEX_TIMEOUT", f"no complete response from {origin} within {timeout_s}s", meta) from None
    except OverflowError:
        raise CodexError("CODEX_PROTOCOL", f"response exceeded {MAX_RESPONSE_BYTES} bytes", meta) from None
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, (TimeoutError, socket.timeout)):
            raise CodexError("CODEX_TIMEOUT", f"no response from {origin} within {timeout_s}s", meta) from None
        raise CodexError("CODEX_NETWORK", f"cannot reach {origin}: "
                         + _scrub(exc.reason, key, secrets), meta) from None
    except (ConnectionError, http.client.HTTPException, OSError) as exc:
        raise CodexError("CODEX_NETWORK", f"connection to {origin} failed: "
                         + _scrub(f"{type(exc).__name__} {exc}", key, secrets), meta) from None

    try:
        data = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise CodexError("CODEX_PROTOCOL", "response body is not JSON", meta) from None
    if not isinstance(data, dict):
        raise CodexError("CODEX_PROTOCOL", "response body is not a JSON object", meta)
    if isinstance(data.get("model"), str):
        meta["model"] = _scrub(data["model"], key, secrets)[:200]
    if isinstance(data.get("id"), str):
        meta["session_id"] = _scrub(data["id"], key, secrets)[:200]
    meta["usage"] = _usage(data.get("usage"))
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise CodexError("CODEX_PROTOCOL", "response has no choices", meta)
    if isinstance(choices[0].get("finish_reason"), str):
        meta["finish_reason"] = choices[0]["finish_reason"][:40]
    text = _content(choices[0].get("message"))
    if text is None:
        raise CodexError("CODEX_PROTOCOL", "choices[0].message.content is missing", meta)
    text = text.strip()
    if not text:
        raise CodexError("CODEX_PROTOCOL", "empty response content", meta)
    return text, meta
