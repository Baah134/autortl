"""ONE public function: ask(role, prompt, ...). Routing is routing.yaml.

Records per-(role, backend) outcomes to router_stats.jsonl — RECORDING ONLY
in v4.0; reordering by observed success is enabled after ~10 runs of data.
"""
from __future__ import annotations
import json
import re
import time
from datetime import datetime
from pathlib import Path
try:
    import yaml
except ImportError:
    yaml = None

from .backends import codex_cli, openai_http

_BACKENDS = {"codex": codex_cli, "openai": openai_http}
_ROUTING_PATH = Path(__file__).parent / "routing.yaml"
_STATS_PATH = Path(__file__).parent / "router_stats.jsonl"


class ModelCallError(RuntimeError):
    """Typed provider failure; deterministic verification must not grade it as RTL."""
    def __init__(self, role: str, code: str, metadata: dict | None = None, message: str = "model worker failed"):
        self.role = role
        self.code = code
        self.metadata = metadata or {}
        super().__init__(f"{code}: role '{role}': {codex_cli.redact(message)[:400]}")

def _load_routing() -> dict:
    if yaml and _ROUTING_PATH.exists():
        return yaml.safe_load(_ROUTING_PATH.read_text())
    # minimal fallback if pyyaml missing
    return {"roles": {r: {"chain": ["codex.default"]} for r in
                      ("planner", "generator", "evaluator", "timing_doctor")},
            "defaults": {"max_retries_per_backend": 2, "timeout_s": 180}}


def _record(role: str, entry: str, ok: bool, seconds: float,
            metadata: dict | None = None, error_type: str | None = None) -> None:
    _STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_STATS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now().isoformat(), "role": role,
                            "entry": entry, "ok": ok, "seconds": round(seconds, 2),
                            "metadata": metadata or {}, "error_type": error_type}) + "\n")


def _backend(role, name):
    """A built-in backend, or a user endpoint from endpoints.local.yaml at the repository root."""
    if name in _BACKENDS:
        return _BACKENDS[name]
    from . import endpoints
    try:
        return endpoints.backend(name)
    except endpoints.EndpointError as exc:
        raise ModelCallError(role, "CODEX_UNAVAILABLE", message=str(exc)) from exc


def _is_backend(name):
    from . import endpoints
    try:
        return name in _BACKENDS or name in endpoints.load()
    except endpoints.EndpointError:
        return False


def _edits(a: str, b: str) -> int:
    """Optimal string alignment distance: insertions, deletions, substitutions, swaps."""
    d = [[i + j if i * j == 0 else 0 for j in range(len(b) + 1)] for i in range(len(a) + 1)]
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] != b[j - 1]))
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)
    return d[len(a)][len(b)]


def check_model(model: str | None) -> None:
    """Raise ValueError when a pinned model would not route where it plainly means to.

    A dotted model whose prefix names no backend is a plain alias sent to each
    routing entry's backend (Codex). That silently misroutes a misspelled backend
    (olama.x for ollama.x), so a prefix within one edit of a backend or endpoint
    name (two edits for names of six or more letters), ignoring case, is refused,
    and so is any dotted model while the endpoints file is unreadable, because the
    prefix cannot then be resolved (mistyped_endpoint_routes_to_codex).
    """
    if not model or "." not in model:
        return
    from . import endpoints
    prefix, _, rest = model.partition(".")
    try:
        defined = endpoints.load()
    except endpoints.EndpointError as exc:
        raise ValueError(f"cannot route model {model!r}: the endpoints file is unreadable "
                         f"({str(exc)[:200]}); fix it before naming a dotted model") from None
    names = set(_BACKENDS) | set(defined)
    if prefix in names:
        return
    for name in sorted(names):
        if _edits(prefix.lower(), name) <= (2 if len(name) >= 6 else 1):
            raise ValueError(f"model {model!r}: {prefix!r} is not a backend or defined endpoint; "
                             f"did you mean {name}.{rest}? (a plain alias would be sent to Codex)")


def ask(role: str, prompt: str, system: str = "",
        budget=None, route_override: str | None = None,
        max_turns: int = 1, model: str | None = None) -> str:
    cfg = _load_routing()
    chain = cfg["roles"].get(role, {}).get("chain", ["codex.default"])
    try:
        check_model(model)
    except ValueError as exc:  # never fall through to Codex (mistyped_endpoint_routes_to_codex)
        raise ModelCallError(role, "CODEX_UNAVAILABLE", message=str(exc)) from None
    if model and _is_backend(model.partition(".")[0]):
        # A backend-qualified model (openai.gpt-4o-mini) pins backend and alias.
        chain = [model]
    elif model:
        # A run-pinned model keeps each entry's backend and replaces its alias.
        chain = list(dict.fromkeys(entry.partition(".")[0] + "." + model for entry in chain))
    if route_override:
        chain = [route_override]
    retries = cfg.get("defaults", {}).get("max_retries_per_backend", 2)
    timeout = cfg.get("defaults", {}).get("timeout_s", 180)

    last_error, succeeded = None, None
    for entry in chain:
        if succeeded:
            break
        backend_name, _, alias = entry.partition(".")
        backend = _backend(role, backend_name)
        if backend is None:
            raise ModelCallError(role, "CODEX_UNAVAILABLE", message=f"unsupported backend '{backend_name}'")
        for attempt in range(1, retries + 1):
            call_timeout = timeout
            if budget is not None:
                if budget.exhausted() or budget.llm_calls >= budget.max_llm_calls:
                    raise RuntimeError("LLM_BUDGET: model call budget exhausted")
                call_timeout = min(timeout, max(0.001,
                    (budget.max_wall_minutes - budget.wall_minutes) * 60))
                budget.charge_llm()
            t0 = time.time()
            try:
                text, meta = backend.ask(alias, prompt, system,
                                         timeout_s=call_timeout, max_turns=max_turns)
                if text and text.strip():
                    _record(role, entry, True, time.time() - t0, meta)
                    succeeded = (text, meta)
                    break
                raise codex_cli.CodexError("CODEX_PROTOCOL", "empty response", meta)
            except Exception as e:
                last_error = e
                _record(role, entry, False, time.time() - t0,
                        getattr(e, "metadata", None), type(e).__name__)
                if isinstance(e, codex_cli.CodexError) and e.code in ("CODEX_AUTH", "CODEX_QUOTA"):
                    raise ModelCallError(role, e.code, e.metadata, str(e)) from e
                if not isinstance(e, codex_cli.CodexError) or e.code not in ("CODEX_TIMEOUT", "CODEX_NETWORK"):
                    break     # non-retryable on this backend: next chain entry
                if attempt < retries:
                    delay = 2 ** attempt
                    if budget is not None:
                        delay = min(delay, max(0,
                            (budget.max_wall_minutes - budget.wall_minutes) * 60))
                    time.sleep(delay)
    if succeeded:
        text, meta = succeeded
        # Outside the retry handling: a checkpoint lock here propagates unchanged
        # instead of discarding a charged response (token_save_lock_misattributed).
        if budget is not None and hasattr(budget, "charge_tokens"):
            budget.charge_tokens((meta or {}).get("usage"))
        return text
    raise ModelCallError(role, getattr(last_error, "code", "CODEX_UNAVAILABLE"),
                         getattr(last_error, "metadata", None),
                         str(last_error) if last_error else "no backend attempts configured") from last_error


def extract_verilog(response_text: str) -> str:
    """Pull the Verilog module out of a response; validates a module exists."""
    text = re.sub(r"<think>.*?</think>", "", response_text, flags=re.DOTALL).strip()
    # Models differ in fence tags (verilog, Verilog, v, SystemVerilog). HDL or
    # untagged fences come first; any other tag only if it holds a module.
    fenced = re.findall(r"```[ \t]*([\w+-]*)[ \t]*\r?\n(.*?)```", text, re.DOTALL)
    hdl = [b for tag, b in fenced if tag.lower() in ("", "verilog", "systemverilog", "sv", "v")]
    blocks = hdl + [b for tag, b in fenced if tag.lower() not in ("", "verilog", "systemverilog", "sv", "v")]
    # One module per fence: join them when every module name is distinct, so a
    # multi-module answer is never returned partially. Repeated names (a "before"
    # and an "after" version) keep the first block, as before.
    designs = [b.strip() for b in hdl if re.search(r"^\s*module\s+\w+", b, re.MULTILINE)]
    names = [n for b in designs for n in re.findall(r"(?m)^\s*module\s+(\w+)", b)]
    if len(designs) > 1 and len(names) == len(set(names)):
        return "\n\n".join(designs)
    # incomplete_block_preferred: a draft that never closes its modules (a model
    # leaving a placeholder, then writing the full version) never wins over a
    # complete block; complete blocks keep the first-wins rule above.
    complete = lambda s: (len(re.findall(r"(?m)^\s*module\s+\w+", s))
                          == len(re.findall(r"(?m)^\s*endmodule\b", s)) > 0)
    whole = [b.strip() for b in blocks if complete(b.strip())]
    if whole and not complete(next((b.strip() for b in blocks
                                    if re.search(r"^\s*module\s+\w+", b, re.MULTILINE)), "")):
        return whole[0]
    for b in blocks:
        s = b.strip()
        if re.search(r"^\s*module\s+\w+", s, re.MULTILINE):
            return s
    for b in blocks:
        s = b.strip()
        if "module " in s and "endmodule" in s:
            return s
    m = re.search(r"(?m)^[ \t]*((?:(?:`timescale[^\n]*|//[^\n]*)\n[ \t]*)*module\s+\w+.*?endmodule)", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text.strip()


def declared_latency(verilog: str, top: str | None = None) -> int | None:
    """Read only the selected module's real annotation; ambiguous files stay unknown."""
    from autortl.verilog_interface import module_declared_latency
    return module_declared_latency(verilog, top)
