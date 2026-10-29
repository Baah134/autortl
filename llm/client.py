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

from .backends import codex_cli

_BACKENDS = {"codex": codex_cli}
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


def ask(role: str, prompt: str, system: str = "",
        budget=None, route_override: str | None = None,
        max_turns: int = 1, model: str | None = None) -> str:
    cfg = _load_routing()
    chain = cfg["roles"].get(role, {}).get("chain", ["codex.default"])
    if model:
        # A run-pinned model keeps each entry's backend and replaces its alias.
        chain = list(dict.fromkeys(entry.partition(".")[0] + "." + model for entry in chain))
    if route_override:
        chain = [route_override]
    retries = cfg.get("defaults", {}).get("max_retries_per_backend", 2)
    timeout = cfg.get("defaults", {}).get("timeout_s", 180)

    last_error = None
    for entry in chain:
        backend_name, _, alias = entry.partition(".")
        backend = _BACKENDS.get(backend_name)
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
                    return text
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
