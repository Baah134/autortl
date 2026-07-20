"""Claude Code headless backend: subprocess -> claude -p --output-format json.

Generator/evaluator are deliberately de-agented (--max-turns 1, no tools):
the harness owns the loop; the model is a function call.
"""
from __future__ import annotations
import json
import subprocess

MODEL_ALIASES = {"opus": "opus", "sonnet": "sonnet"}


def ask(model_alias: str, prompt: str, system: str = "",
        timeout_s: int = 180, max_turns: int = 1) -> tuple[str, dict]:
    model = MODEL_ALIASES.get(model_alias, model_alias)
    cmd = ["claude", "-p", prompt, "--output-format", "json",
           "--model", model, "--max-turns", str(max_turns)]
    if system:
        cmd += ["--append-system-prompt", system]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
    if r.returncode != 0:
        raise RuntimeError(f"claude exited {r.returncode}: {r.stderr[:300]}")
    data = json.loads(r.stdout)
    text = data.get("result", "") or data.get("content", "")
    meta = {"cost_usd": data.get("total_cost_usd"),
            "duration_ms": data.get("duration_ms"),
            "session_id": data.get("session_id")}
    return text, meta
