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

from .backends import claude_code, nvidia_nim, openrouter

_BACKENDS = {"claude_code": claude_code, "nvidia": nvidia_nim, "openrouter": openrouter}
_ROUTING_PATH = Path(__file__).parent / "routing.yaml"
_STATS_PATH = Path(__file__).parent / "router_stats.jsonl"

_RETRYABLE = ("429", "500", "502", "503", "504", "timed out", "overloaded",
              "rate limit", "RESOURCE_EXHAUSTED", "UNAVAILABLE")


def _load_routing() -> dict:
    if yaml and _ROUTING_PATH.exists():
        return yaml.safe_load(_ROUTING_PATH.read_text())
    # minimal fallback if pyyaml missing
    return {"roles": {r: {"chain": ["claude_code.sonnet"]} for r in
                      ("planner", "generator", "evaluator", "timing_doctor")},
            "defaults": {"max_retries_per_backend": 2, "timeout_s": 180}}


def _record(role: str, entry: str, ok: bool, seconds: float) -> None:
    with open(_STATS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now().isoformat(), "role": role,
                            "entry": entry, "ok": ok, "seconds": round(seconds, 2)}) + "\n")


def ask(role: str, prompt: str, system: str = "",
        budget=None, route_override: str | None = None,
        max_turns: int = 1) -> str:
    cfg = _load_routing()
    chain = cfg["roles"].get(role, {}).get("chain", ["claude_code.sonnet"])
    if route_override:
        chain = [route_override] + [c for c in chain if c != route_override]
    retries = cfg.get("defaults", {}).get("max_retries_per_backend", 2)
    timeout = cfg.get("defaults", {}).get("timeout_s", 180)

    last_err = ""
    for entry in chain:
        backend_name, _, alias = entry.partition(".")
        backend = _BACKENDS.get(backend_name)
        if backend is None:
            continue
        for attempt in range(1, retries + 1):
            t0 = time.time()
            try:
                text, meta = backend.ask(alias, prompt, system,
                                         timeout_s=timeout, max_turns=max_turns)
                if budget is not None:
                    budget.charge_llm()
                _record(role, entry, True, time.time() - t0)
                if text:
                    return text
                last_err = "empty response"
            except Exception as e:
                last_err = str(e)
                _record(role, entry, False, time.time() - t0)
                if not any(s in last_err for s in _RETRYABLE):
                    break     # non-retryable on this backend: next chain entry
                time.sleep(2 ** attempt)
    raise RuntimeError(f"all backends failed for role '{role}': {last_err[:300]}")


def extract_verilog(response_text: str) -> str:
    """Pull the Verilog module out of a response; validates a module exists."""
    text = re.sub(r"<think>.*?</think>", "", response_text, flags=re.DOTALL).strip()
    blocks = re.findall(r"```(?:verilog|systemverilog|sv)?\s*\n(.*?)```", text, re.DOTALL)
    for b in blocks:
        s = b.strip()
        if re.search(r"^\s*module\s+\w+", s, re.MULTILINE):
            return s
    for b in blocks:
        s = b.strip()
        if "module " in s and "endmodule" in s:
            return s
    m = re.search(r"(module\s+\w+.*?endmodule)", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text.strip()


def declared_latency(verilog: str) -> int | None:
    """Parse the mandated '// @latency N' header if present."""
    m = re.search(r"//\s*@latency\s+(\d+)", verilog)
    return int(m.group(1)) if m else None
