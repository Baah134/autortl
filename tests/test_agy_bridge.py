"""Antigravity bridge: stdin framing, result parsing and error mapping, with agy faked."""
import importlib.util
import io
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("agy_bridge", ROOT / "scripts" / "agy_bridge.py")
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


def events(*items):
    return "\n".join(json.dumps(e) for e in items) + "\n"


OK = events({"event": "init", "init": {"model": "m"}},
            {"event": "step_update", "step_update": {"text_delta": "module"}},
            {"event": "result", "result": {"status": "SUCCESS", "response": "module m; endmodule\n",
                                           "usage": {"input_tokens": 7, "output_tokens": 3}}})


class Fake:
    def __init__(self, stdout, stderr="", code=0):
        self.stdout, self.stderr, self.code, self.calls = stdout, stderr, code, []

    def __call__(self, cmd, **kwargs):
        self.calls.append((cmd, kwargs["input"]))
        return subprocess.CompletedProcess(cmd, self.code, self.stdout, self.stderr)


def test_prompt_goes_on_stdin_as_one_stream_json_message(monkeypatch, capsys):
    monkeypatch.setenv("AUTORTL_AGY_BIN", "agy-test")
    fake = Fake(OK)
    prompt = 'Write "TopModule"\nwith C:\\paths and {braces}'
    assert bridge.main(["--model", "gemini-x"], stdin=io.StringIO(prompt), run=fake) == 0
    cmd, sent = fake.calls[0]
    assert cmd[:3] == ["agy-test", "--model", "gemini-x"] and cmd[-1] == "--print="
    assert "--sandbox" in cmd and prompt not in " ".join(cmd)  # model input never on the command line
    assert json.loads(sent) == {"event": "user", "message": {"content": prompt}} and sent.count("\n") == 1
    assert capsys.readouterr().out == "module m; endmodule\n"


def test_default_model_passes_no_model_flag(monkeypatch):
    monkeypatch.setenv("AUTORTL_AGY_BIN", "agy-test")
    fake = Fake(OK)
    bridge.main([], stdin=io.StringIO("x"), run=fake)
    assert "--model" not in fake.calls[0][0]


def test_error_result_exits_1_with_reason_on_stderr(monkeypatch, capsys):
    monkeypatch.setenv("AUTORTL_AGY_BIN", "agy-test")
    quota = events({"event": "result", "result": {"status": "ERROR", "response": "",
                                                  "error": "RESOURCE_EXHAUSTED: quota exceeded"}})
    assert bridge.main([], stdin=io.StringIO("x"), run=Fake(quota, stderr="error: 429")) == 1
    err = capsys.readouterr().err
    assert "quota exceeded" in err and "429" in err  # the command backend maps this to CODEX_QUOTA


def test_parse_handles_missing_and_empty_results():
    assert bridge.parse("noise\n{not json\n") == (False, "agy printed no result event", {})
    empty = events({"event": "result", "result": {"status": "SUCCESS", "response": "  "}})
    assert bridge.parse(empty)[0] is False
    assert bridge.parse(OK) == (True, "module m; endmodule", {"input_tokens": 7, "output_tokens": 3})


def test_reply_produced_with_tools_is_refused(monkeypatch, capsys):
    # agy_endpoint_uses_tools: Flash-high web-searched the task name before answering
    monkeypatch.setenv("AUTORTL_AGY_BIN", "agy-test")
    searched = events({"event": "step_update", "step_update": {"state": "ACTIVE", "tool_name": "search_web",
                                                               "tool_info": {"parameters": {"query": "q"}}}},
                      {"event": "step_update", "step_update": {"state": "DONE", "tool_name": "search_web"}},
                      {"event": "step_update", "step_update": {"state": "DONE", "tool_name": "run_command"}},
                      {"event": "result", "result": {"status": "SUCCESS", "response": "module m; endmodule"}})
    assert bridge.parse(searched)[:2] == (False, "MODEL_TOOL_USE: agy used tools ['search_web', 'run_command']; "
                                                 "a model endpoint must answer without tools")
    assert bridge.main([], stdin=io.StringIO("x"), run=Fake(searched)) == 1
    out = capsys.readouterr()
    assert out.out == "" and "MODEL_TOOL_USE" in out.err  # command backend: failed cell, not infra


def test_quota_error_wins_over_tool_use_and_odd_shapes_are_tolerated():
    quota_after_tool = events({"event": "step_update", "step_update": {"tool_name": "search_web"}},
                              {"event": "result", "result": {"status": "ERROR", "error": "RESOURCE_EXHAUSTED"}})
    assert bridge.parse(quota_after_tool)[:2] == (False, "RESOURCE_EXHAUSTED")
    odd = events({"event": "step_update", "step_update": "text"}, ["list"],
                 {"event": "result", "result": {"status": "SUCCESS", "response": "ok"}})
    assert bridge.parse(odd)[:2] == (True, "ok")
    other_shapes = events({"event": "tool_call", "name": "x"},
                          {"event": "result", "result": {"status": "SUCCESS", "response": "ok"}})
    assert bridge.parse(other_shapes)[0] is False


def test_empty_stdin_is_refused_without_calling_agy(capsys):
    fake = Fake(OK)
    assert bridge.main([], stdin=io.StringIO("  \n"), run=fake) == 2 and fake.calls == []
