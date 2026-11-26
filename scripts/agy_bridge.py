"""Antigravity CLI (`agy`) as an AutoRTL command endpoint: prompt on stdin, answer on stdout.

`agy --print` takes its prompt as an argument, which is too small for harness
prompts on Windows and would put model input on a command line. Its
stream-json mode reads the prompt from stdin, so this bridge wraps stdin in one
`{"event": "user", "message": {"content": ...}}` line, runs

    agy --model <m> --sandbox --disable-slash-commands
        --input-format stream-json --output-format stream-json --print=

and prints only the final `result.response`. A failed result goes to stderr
with exit 1, so the command backend classifies quota, auth and network errors
as it does for every other CLI. Configure it in `endpoints.local.yaml` (ignored
by Git) at the repository root:

    endpoints:
      antigravity:
        kind: command
        argv: [python, scripts/agy_bridge.py]
        model_flag: --model

then `--model antigravity.gemini-3.8-flash-high` (list names with `agy models`).
The executable is found on PATH, in `%LOCALAPPDATA%/agy/bin`, or from
`AUTORTL_AGY_BIN`. Use an absolute script path in `argv` if the harness runs
from another folder: the command backend starts commands in an empty folder.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
from pathlib import Path

FLAGS = ["--sandbox", "--disable-slash-commands", "--input-format", "stream-json",
         "--output-format", "stream-json", "--print="]


def find_agy() -> str:
    explicit = os.environ.get("AUTORTL_AGY_BIN")
    if explicit:
        return explicit
    found = shutil.which("agy")
    if found:
        return found
    local = Path(os.environ.get("LOCALAPPDATA", "")) / "agy" / "bin" / "agy.exe"
    if local.is_file():
        return str(local)
    raise FileNotFoundError("agy not found: install the Antigravity CLI or set AUTORTL_AGY_BIN")


def command(agy: str, model: str | None) -> list[str]:
    return [agy, *(["--model", model] if model else []), *FLAGS]


def tool_names(event: dict) -> list[str]:
    """Tool names an agy event shows: step_update.tool_name, or any event or key naming a tool."""
    names = []
    step = event.get("step_update")
    if isinstance(step, dict):
        if step.get("tool_name"):
            names.append(str(step["tool_name"]))
        elif any("tool" in key for key in step if key != "tools"):
            names.append(str(step.get("step_type") or "unnamed tool"))
    kind = str(event.get("event") or "")
    if "tool" in kind:
        names.append(kind)
    return names


def parse(stdout: str) -> tuple[bool, str, dict]:
    """(ok, response or error, usage) from agy's stream-json output; the last result event wins.

    agy is an agent: `--sandbox` restricts its terminal, not its tools, and permission
    deny rules did not stop `search_web` (November 21 probe). A reply produced with any
    tool call (web search, commands, file reads) is refused, so a model endpoint
    answers from the prompt alone, as the Codex backend does (agy_endpoint_uses_tools).
    """
    result, tools = None, []
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        if event.get("event") == "result" and isinstance(event.get("result"), dict):
            result = event["result"]
        for name in tool_names(event):
            if name not in tools:
                tools.append(name)
    usage = (result or {}).get("usage") or {}
    if result is not None and result.get("status") != "SUCCESS":
        # A quota or auth error is reported as such even if tools ran first.
        return False, result.get("error") or f"agy status {result.get('status')}", usage
    if tools:
        # MODEL_TOOL_USE: the command backend maps it to a failed cell, never infrastructure.
        return False, f"MODEL_TOOL_USE: agy used tools {tools}; a model endpoint must answer without tools", {}
    if result is None:
        return False, "agy printed no result event", {}
    response = (result.get("response") or "").strip()
    return (True, response, usage) if response else (False, "agy returned an empty response", usage)


def _is_result(line: str) -> bool:
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        return False
    return isinstance(event, dict) and event.get("event") == "result"


def _stop(proc: subprocess.Popen) -> None:
    """End agy and anything it started; on Windows only taskkill /T reaches the children."""
    if proc.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
    else:
        proc.kill()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()


def run_until_result(cmd, *, input, encoding="utf-8", errors="replace", **_ignored):
    """Like subprocess.run, but returns as soon as agy prints its result event.

    agy_exits_late_after_result: the agy build installed November 25 printed its result
    about 3 s into a trivial call and then kept running for about 100 s before exiting,
    so waiting for exit pushed calls toward the 180 s limit. Nothing agy prints after
    the result changes the answer (tool events precede it), so the process is stopped
    once the result line has been read.
    """
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, encoding=encoding, errors=errors)
    err: list[str] = []
    reader = threading.Thread(target=lambda: err.append(proc.stderr.read()), daemon=True)
    reader.start()
    try:
        proc.stdin.write(input)
        proc.stdin.close()
    except OSError:
        pass  # agy exited early; its stdout and stderr say why
    out, seen = [], False
    for line in proc.stdout:
        out.append(line)
        if _is_result(line.strip()):
            seen = True
            break
    if seen:
        _stop(proc)
    else:
        proc.wait()
    reader.join(timeout=5)
    code = 0 if seen else proc.returncode
    return subprocess.CompletedProcess(cmd, code, "".join(out), "".join(err))


def main(argv=None, *, stdin=None, run=run_until_result) -> int:
    parser = argparse.ArgumentParser(prog="agy_bridge")
    parser.add_argument("--model")
    a = parser.parse_args(argv)
    prompt = (stdin if stdin is not None else sys.stdin).read()
    if not prompt.strip():
        print("agy_bridge: empty prompt on stdin", file=sys.stderr)
        return 2
    try:
        cmd = command(find_agy(), a.model)
    except FileNotFoundError as exc:
        print(f"agy_bridge: {exc}", file=sys.stderr)
        return 1
    message = json.dumps({"event": "user", "message": {"content": prompt}}) + "\n"
    done = run(cmd, input=message, capture_output=True, text=True, encoding="utf-8", errors="replace")
    ok, text, _usage = parse(done.stdout or "")
    if ok:
        sys.stdout.write(text + "\n")
        return 0
    detail = (done.stderr or "").strip()[-500:]
    print(f"agy_bridge: {text}" + (f" | {detail}" if detail else ""), file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
