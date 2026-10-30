"""User-defined model endpoints: plug any AI into every harness role.

Endpoints live in a local file that is never committed: `endpoints.local.yaml`
at the repository root, or the path in AUTORTL_ENDPOINTS. Each one has a
name, used as `run.py --model <name>.<model>`, and a kind:

    endpoints:
      ollama:                          # any OpenAI-compatible chat-completions server
        kind: openai
        base_url: http://localhost:11434/v1
        api_key_env: OLLAMA_API_KEY    # optional: the environment variable holding the key
      claude:                          # any program that reads the prompt on stdin
        kind: command
        argv: [claude, -p]
        model_flag: --model            # optional: how to pass <model> on the command line

Keys are never written in the file, only the name of the variable that holds
one. A command endpoint gets the prompt on stdin, never in its arguments, and
runs from an empty temporary folder with the harness timeout. The digest of an
endpoint's definition is recorded in the bench cohort, so editing an endpoint
starts a new cohort. See llm/endpoints.example.yaml.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

try:
    import yaml
except ImportError:  # the harness requires pyyaml; endpoints also accept JSON
    yaml = None

# Outside autortl/, llm/, data/ and .claude/skills, so editing it never changes the
# harness identity that resume checks; its definition is recorded in the cohort instead.
LOCAL = Path(__file__).resolve().parents[1] / "endpoints.local.yaml"
BUILTIN = ("codex", "openai")
NAME = re.compile(r"[a-z][a-z0-9_-]{0,31}")
ENV_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,63}")


class EndpointError(ValueError):
    """The endpoints file is unreadable or an endpoint is malformed."""


def path() -> Path:
    return Path(os.environ["AUTORTL_ENDPOINTS"]) if os.environ.get("AUTORTL_ENDPOINTS") else LOCAL


def _validate(name, spec):
    if not NAME.fullmatch(name) or name in BUILTIN:
        raise EndpointError(f"endpoint name {name!r} must be lowercase letters, digits, _ or -, "
                            f"start with a letter, and not be {' or '.join(BUILTIN)}")
    if not isinstance(spec, dict):
        raise EndpointError(f"endpoint {name}: expected a mapping")
    kind = spec.get("kind")
    allowed = {"openai": {"kind", "base_url", "api_key_env"}, "command": {"kind", "argv", "model_flag"}}
    if kind not in allowed:
        raise EndpointError(f"endpoint {name}: kind must be openai or command")
    unknown = set(spec) - allowed[kind]
    if unknown:
        raise EndpointError(f"endpoint {name}: unknown fields {', '.join(sorted(unknown))}"
                            + (" (put keys in an environment variable named by api_key_env)"
                               if {"api_key", "key", "token"} & unknown else ""))
    if kind == "openai":
        base = spec.get("base_url")
        if not isinstance(base, str) or not re.match(r"https?://[^/\s]+", base):
            raise EndpointError(f"endpoint {name}: base_url must be an http(s) URL")
        env = spec.get("api_key_env")
        if env is not None and (not isinstance(env, str) or not ENV_NAME.fullmatch(env)):
            raise EndpointError(f"endpoint {name}: api_key_env must be an environment variable name")
    else:
        argv = spec.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(a, str) and a for a in argv):
            raise EndpointError(f"endpoint {name}: argv must be a non-empty list of strings")
        flag = spec.get("model_flag")
        if flag is not None and (not isinstance(flag, str) or not flag.startswith("-")):
            raise EndpointError(f"endpoint {name}: model_flag must be an option such as --model")
    return dict(spec)


def load(source: Path | None = None) -> dict:
    """{name: definition} from the endpoints file; {} when there is none."""
    source = Path(source) if source else path()
    if not source.is_file():
        if os.environ.get("AUTORTL_ENDPOINTS") and source == path():
            raise EndpointError(f"AUTORTL_ENDPOINTS names a missing file: {source}")
        return {}
    text = source.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(text) if yaml else json.loads(text)
    except Exception as exc:
        raise EndpointError(f"{source}: cannot parse: {exc}") from exc
    entries = (data or {}).get("endpoints", {}) if isinstance(data, dict) else None
    if not isinstance(entries, dict):
        raise EndpointError(f"{source}: expected an 'endpoints' mapping")
    return {name: _validate(name, spec) for name, spec in entries.items()}


def digest(definition: dict) -> str:
    return hashlib.sha256(json.dumps(definition, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class Endpoint:
    """A user endpoint with the same ask() signature as the built-in backends."""

    def __init__(self, name: str, definition: dict):
        self.name, self.definition = name, definition

    def ask(self, model_alias, prompt, system="", timeout_s=180, max_turns=1):
        from .backends import command_cli, openai_http
        d = self.definition
        if d["kind"] == "openai":
            return openai_http.ask(model_alias, prompt, system, timeout_s, max_turns,
                                   base_url=d["base_url"], api_key_env=d.get("api_key_env"),
                                   label=self.name)
        return command_cli.ask(model_alias, prompt, system, timeout_s, max_turns,
                               argv=d["argv"], model_flag=d.get("model_flag"), label=self.name)


def backend(name: str):
    """The user endpoint called name, or None."""
    definition = load().get(name)
    return Endpoint(name, definition) if definition is not None else None
