"""OpenRouter backend — free Nemotron tier as the NIM-breaks fallback.

Uses the models array so OpenRouter falls back within one request.
429s here are INFRA failures (free tier throttles at peak), never design.
"""
from __future__ import annotations
import json
import os
import urllib.request

BASE = "https://openrouter.ai/api/v1"
MODEL_ALIASES = {
    "nemotron-ultra": "nvidia/nemotron-3-ultra-550b-a55b:free",
    "nemotron-super": "nvidia/nemotron-3-super-120b-a12b:free",
}


def ask(model_alias: str, prompt: str, system: str = "",
        timeout_s: int = 180, max_turns: int = 1) -> tuple[str, dict]:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    primary = MODEL_ALIASES.get(model_alias, model_alias)
    fallbacks = [m for m in MODEL_ALIASES.values() if m != primary]
    messages = ([{"role": "system", "content": system}] if system else []) + \
               [{"role": "user", "content": prompt}]
    payload = {"model": primary, "models": [primary] + fallbacks,
               "messages": messages, "max_tokens": 8192, "temperature": 0.4}
    req = urllib.request.Request(
        f"{BASE}/chat/completions", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {key}",
                 "X-Title": "AutoRTL"},
        method="POST")
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        data = json.loads(resp.read().decode())
    return data["choices"][0]["message"]["content"], {"cost_usd": 0.0}
