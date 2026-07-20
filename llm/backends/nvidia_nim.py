"""NVIDIA Build (NIM) backend — OpenAI-compatible, stdlib only."""
from __future__ import annotations
import json
import os
import urllib.request

BASE = "https://integrate.api.nvidia.com/v1"
MODEL_ALIASES = {
    "nemotron-ultra": "nvidia/nemotron-3-ultra-550b-a55b",
    "nemotron-super": "nvidia/nemotron-3-super-120b-a12b",
}
THINKING = {
    "nvidia/nemotron-3-ultra-550b-a55b": {"chat_template_kwargs": {"enable_thinking": True}, "reasoning_budget": 8192},
    "nvidia/nemotron-3-super-120b-a12b": {"chat_template_kwargs": {"enable_thinking": True}, "reasoning_budget": 8192},
}


def ask(model_alias: str, prompt: str, system: str = "",
        timeout_s: int = 180, max_turns: int = 1) -> tuple[str, dict]:
    key = os.environ.get("NVIDIA_API_KEY", "").strip()
    if not key:
        raise RuntimeError("NVIDIA_API_KEY not set")
    model = MODEL_ALIASES.get(model_alias, model_alias)
    messages = ([{"role": "system", "content": system}] if system else []) + \
               [{"role": "user", "content": prompt}]
    payload = {"model": model, "messages": messages,
               "max_tokens": 8192, "temperature": 0.4}
    payload.update(THINKING.get(model, {}))
    req = urllib.request.Request(
        f"{BASE}/chat/completions", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        method="POST")
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        data = json.loads(resp.read().decode())
    return data["choices"][0]["message"]["content"], {"cost_usd": 0.0}
