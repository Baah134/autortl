"""Golden sandbox gaps from the whole-harness review (golden_sandbox_allocation_and_timeout_gaps,
model_text_overflows_supervisor_parser): copies, slices, nested decorators, parser
overflow in the supervisor, and a worker timeout that must read as infrastructure."""
import json
import subprocess
import sys
import textwrap
from pathlib import Path
from unittest.mock import Mock
import pytest
from autortl import fsm, golden, golden_worker
from autortl.config import RunConfig
from autortl.golden import GoldenModel, GoldenTimeoutError
from autortl.golden_worker import MAX_SYNTAX_DEPTH, syntax_depth, validate_source
from autortl.spec import IOExample, ModuleSpec, Port


def model(tmp_path, source, **kwargs):
    path = tmp_path / "oracle.py"
    path.write_text(source, encoding="utf-8")
    return GoldenModel(path, **kwargs)


def step_body(body):
    return "def init():\n    return {}\ndef step(state, inputs):\n" + textwrap.indent(textwrap.dedent(body), "    ")


# --- 1. copies and slices are charged to the cumulative allocation cap ---

REVIEW_PROBE = step_body("""
    base = list(range(10000))
    big = []
    for n in range(300):
        big.append(base.copy())
        big.append(base[:])
    return state, {"y": len(big)}
""")


@pytest.mark.parametrize("source", [
    REVIEW_PROBE,
    REVIEW_PROBE.replace("        big.append(base[:])\n", ""),
    REVIEW_PROBE.replace("        big.append(base.copy())\n", ""),
    REVIEW_PROBE.replace("base[:]", "base[0:10000:1]").replace("        big.append(base.copy())\n", ""),
    # dict copies are charged as well
    step_body("""
        table = dict((n, n) for n in range(10000))
        big = []
        for n in range(300):
            big.append(table.copy())
        return state, {"y": len(big)}
    """),
], ids=["review_probe", "copy_only", "slice_only", "explicit_slice", "dict_copy"])
def test_copy_and_slice_retention_hits_allocation_cap(tmp_path, source):
    with pytest.raises(ValueError, match="allocation limit"):
        model(tmp_path, source).run([{}])


def test_bound_copy_held_and_called_indirectly_is_still_charged(tmp_path):
    # Rebinding a defined function's name to a bound copy reaches it through a Name call.
    source = "def grab():\n    return 0\n" + step_body("""
        base = list(range(10000))
        big = []
        for n in range(300):
            grab = base.copy
            big.append(grab())
        return state, {"y": len(big)}
    """)
    with pytest.raises(ValueError, match="allocation limit"):
        model(tmp_path, source).run([{}])


def test_slice_assignment_growth_is_charged(tmp_path):
    source = step_body("""
        grow = [0]
        for n in range(40):
            grow[:0] = grow
        return state, {"y": len(grow)}
    """)
    with pytest.raises(ValueError, match="allocation limit"):
        model(tmp_path, source).run([{}])


@pytest.mark.parametrize("statement", [
    "for grow[:0] in [grow, grow]:\n        pass",
    "grow[:0] = grow[:0] = grow",
    "grow[:0], other = grow, 1",
])
def test_uncharged_slice_store_forms_are_rejected(tmp_path, statement):
    source = step_body("grow = [0]\nother = 0\n" + statement + "\nreturn state, {'y': 0}\n")
    with pytest.raises(ValueError, match="slice assignment"):
        model(tmp_path, source)


def test_small_copies_slices_and_slice_assignment_keep_python_semantics(tmp_path):
    source = step_body("""
        values = [1, 2, 3, 4, 5]
        head = values[1:4]
        tail = values[::-2]
        text = "abcdef"[2:4]
        clone = state.copy()
        clone["k"] = 9
        values[1:3] = (n * 10 for n in range(3))
        span = range(10)[2:5]
        return clone, {"a": head[0] + head[2], "b": tail[1], "c": len(text),
                       "d": len(state), "e": values[3], "f": len(values), "g": span[0]}
    """)
    assert model(tmp_path, source).run([{}]) == [{"a": 6, "b": 3, "c": 2, "d": 0, "e": 20, "f": 6, "g": 2}]


def test_per_step_state_copy_within_budget_still_runs(tmp_path):
    source = ('def init():\n    return {"count": 0, "last": 0}\n'
              'def step(state, inputs):\n    state = state.copy()\n'
              '    history = [state["count"], state["last"]][0:2]\n'
              '    state["count"] = (state["count"] + 1) & 255\n'
              '    state["last"] = history[0]\n'
              '    return state, {"y": state["count"]}\n')
    rows = model(tmp_path, source).run([{}] * 1000)
    assert rows[-1] == {"y": 1000 & 255}


# --- 2. decorators are rejected on every function, nested included ---

@pytest.mark.parametrize("source", [
    step_body("""
        d = {"k": range}
        h = d.get("k")
        @h
        def f():
            return 1
        return state, {"y": 0}
    """),
    step_body("""
        def outer():
            @inputs.get
            def inner():
                return 1
            return 0
        return state, {"y": outer()}
    """),
])
def test_nested_decorators_are_rejected_before_child(tmp_path, monkeypatch, source):
    launch = Mock(side_effect=AssertionError("decorated code reached worker"))
    monkeypatch.setattr(golden.subprocess, "run", launch)
    with pytest.raises(ValueError, match="decorators"):
        model(tmp_path, source)
    launch.assert_not_called()


def test_lambda_remains_unsupported():
    with pytest.raises(ValueError, match="Lambda"):
        validate_source(step_body("f = lambda: 1\nreturn state, {'y': 0}\n"))


# --- 3. supervisor parsing never leaks MemoryError or RecursionError ---

@pytest.mark.parametrize("source", [
    "{'y': " + "-" * 30000 + "1}",
    "x = " + "+".join(["1"] * 5000),
    "x = y" + "[0]" * 5000,
    "x = " + "not " * 15000 + "1",
    step_body("return state, {'y': " + "+".join(["1"] * 5000) + "}\n"),
    # parseable, but deeper than the worker can transform and compile reliably
    step_body("return state, {'y': " + "+".join(["1"] * 400) + "}\n"),
], ids=["unary_chain", "long_sum", "deep_subscript", "not_chain", "long_sum_in_step", "over_depth_cap"])
def test_overflowing_model_text_is_an_ordinary_validation_error(tmp_path, source):
    with pytest.raises(ValueError, match="nest|complex"):
        validate_source(source)
    with pytest.raises(ValueError, match="nest|complex"):
        model(tmp_path, source)


def test_top_level_literal_eval_recursion_is_converted(monkeypatch):
    def overflow(node):
        raise RecursionError("maximum recursion depth exceeded")
    monkeypatch.setattr(golden_worker.ast, "literal_eval", overflow)
    with pytest.raises(ValueError, match="complex"):
        validate_source("TABLE = [1]\n" + step_body("return state, {'y': 0}\n"))


def test_expression_just_under_depth_cap_still_runs_in_worker(tmp_path):
    terms = 170
    source = step_body("return state, {'y': " + "+".join(["1"] * terms) + "}\n")
    assert syntax_depth(validate_source(source)) <= MAX_SYNTAX_DEPTH
    assert model(tmp_path, source).run([{}]) == [{"y": terms}]


# --- 4. a worker timeout is infrastructure, not an oracle rejection ---

GOOD = step_body("return state, {'y': inputs.get('a', 0)}\n")


def test_real_worker_deadline_raises_golden_timeout_not_value_error(tmp_path):
    gm = model(tmp_path, GOOD, timeout_s=0.001)
    with pytest.raises(GoldenTimeoutError, match="timed out") as caught:
        gm.run([{"a": 1}])
    assert not isinstance(caught.value, ValueError)
    assert issubclass(GoldenTimeoutError, RuntimeError) and not issubclass(GoldenTimeoutError, ValueError)


def test_timeout_message_does_not_look_like_a_budget_stop():
    # The orchestrator re-raises RuntimeErrors except LLM_BUDGET:/TOOL_BUDGET: stops.
    message = str(GoldenTimeoutError("golden worker timed out after 5s"))
    assert not message.startswith(("LLM_BUDGET:", "TOOL_BUDGET:"))


@pytest.fixture
def oracle_build(tmp_path, monkeypatch):
    o = fsm.Orchestrator(RunConfig(mode="build", top_module="m"), tmp_path / "run")
    spec = ModuleSpec("m", "increment modulo256", [Port("a", "input", 8), Port("y", "output", 8)],
                      examples=[IOExample({"a": 1}, {"y": 2})])
    folder = tmp_path / "module"
    folder.mkdir()
    monkeypatch.setattr(o, "_generate_verified", Mock(return_value="module m; endmodule"))
    monkeypatch.setattr(fsm, "qualify_tb", Mock(return_value=(True, "controlled assertion proof")))
    return o, spec, folder


def test_build_oracle_timeout_blocks_as_infra_without_spending_a_repair(oracle_build, monkeypatch):
    o, spec, folder = oracle_build
    good = "def init():\n    return {}\ndef step(state, inputs):\n    return state, {'y': (inputs['a'] + 1) & 255}\n"
    generator = Mock(return_value=good)
    monkeypatch.setattr(o.generator, "golden_model", generator)
    monkeypatch.setattr(fsm.GoldenModel, "run",
                        Mock(side_effect=GoldenTimeoutError("golden worker timed out after 5s")))
    assert o._build_module(spec, folder) is None
    assert generator.call_count == 1  # no feedback round
    assert o._build_blocker["failure_kind"] == "infra"
    assert "timed out" in o._build_blocker["error"]
    assert not (folder / "golden_attempt_1.log").exists()  # never recorded as a model rejection
    o._generate_verified.assert_not_called()
    assert o.state.read_designs() == []


# --- Windows Job Object memory cap for the worker ---

@pytest.mark.skipif(sys.platform != "win32", reason="Windows Job Object limit")
def test_windows_job_object_caps_worker_memory(tmp_path):
    worker_dir = Path(golden_worker.__file__).resolve().parent
    probe = textwrap.dedent(f"""
        import json, sys
        sys.path.insert(0, {str(worker_dir)!r})
        import golden_worker
        limited = golden_worker.limit_windows_process_memory(64 * 1024 * 1024)
        try:
            block = bytearray(256 * 1024 * 1024)
            outcome = "allocated"
        except MemoryError:
            outcome = "MemoryError"
        print(json.dumps({{"limited": limited, "outcome": outcome}}))
    """)
    result = subprocess.run([sys.executable, "-I", "-S", "-c", probe], capture_output=True,
                            text=True, timeout=60, cwd=tmp_path)
    report = json.loads(result.stdout)
    if not report["limited"]:
        pytest.skip("this host refused a nested job object; the worker falls back silently")
    assert report["outcome"] == "MemoryError"


def test_job_object_limit_is_a_silent_no_op_off_windows(monkeypatch):
    monkeypatch.setattr(golden_worker.sys, "platform", "linux")
    assert golden_worker.limit_windows_process_memory(1) is False
