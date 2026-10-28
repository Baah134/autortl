import json
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from autortl.golden import GoldenModel
from autortl import golden

GOOD = 'def init():\n    return {"v": 0}\ndef step(state, inputs):\n    state["v"] = state["v"] + inputs.get("x", 0)\n    return state, {"y": state["v"]}\n'


def model(tmp_path, source=GOOD, **kwargs):
    path = tmp_path / "oracle.py"
    path.write_text(source)
    return GoldenModel(path, **kwargs)


@pytest.mark.parametrize("statement", [
    'import os', 'from pathlib import Path', 'open("stolen", "w")',
    'eval("1")', 'exec("pass")', 'getattr(state, "get")',
    'state.__class__', 'inputs.get.__globals__', 'dict(__builtins__)',
])
def test_forbidden_python_rejected_before_child(tmp_path, monkeypatch, statement):
    launch = Mock(side_effect=AssertionError("forbidden code reached worker"))
    monkeypatch.setattr(golden.subprocess, "run", launch)
    with pytest.raises(ValueError):
        model(tmp_path, GOOD.replace('    state["v"] =', f"    {statement}\n    state[\"v\"] ="))
    launch.assert_not_called()


def test_top_level_execution_is_rejected_without_side_effects(tmp_path):
    with pytest.raises(ValueError):
        model(tmp_path, GOOD + '\nopen("proof", "w").write("bad")')
    assert not (tmp_path / "proof").exists()


def test_real_worker_runs_stateful_oracle_and_resets_each_call(tmp_path):
    gm = model(tmp_path)
    assert gm.run([{"x": 1}, {"x": 3}]) == [{"y": 1}, {"y": 4}]
    assert gm.run([{"x": 1}]) == [{"y": 1}]


def test_child_receives_only_minimal_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "secret-test")
    monkeypatch.setenv("UNRELATED_PRIVATE_VALUE", "secret-test")
    launch = Mock(return_value=SimpleNamespace(returncode=0, stdout='{"outputs": [{"y": 1}]}'))
    monkeypatch.setattr(golden.subprocess, "run", launch)
    assert model(tmp_path).run([{"x": 1}]) == [{"y": 1}]
    args, kw = launch.call_args
    assert args[0][1:3] == ["-I", "-S"]
    assert set(kw["env"]) <= {"SYSTEMROOT", "WINDIR", "TEMP", "TMP"}
    assert kw["shell"] is False
    assert kw["timeout"] <= 30


def test_timeout_is_reported_as_error(tmp_path, monkeypatch):
    monkeypatch.setattr(golden.subprocess, "run", Mock(side_effect=subprocess.TimeoutExpired("oracle", 1)))
    with pytest.raises(ValueError, match="timed out"):
        model(tmp_path).run([{"x": 1}])


def test_infinite_loop_exhausts_instruction_budget_in_child(tmp_path):
    source = 'def init():\n    while True:\n        pass\ndef step(state, inputs):\n    return state, {"y": 0}'
    with pytest.raises(ValueError, match="budget|timed out"):
        model(tmp_path, source).run([{}])


@pytest.mark.parametrize("expression", [
    '1 << 1000000000', '[0] * 1000000000', 'range(1000000000)',
    'list(x for x in range(10000) for y in range(2))',
])
def test_large_single_operations_are_bounded_before_allocation(tmp_path, expression):
    source = GOOD.replace('state["v"] + inputs.get("x", 0)', expression)
    with pytest.raises(ValueError, match="limit"):
        model(tmp_path, source).run([{"x": 1}])


def test_non_integer_oracle_output_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="integers"):
        model(tmp_path, GOOD.replace('{"y": state["v"]}', '{"y": "wrong"}')).run([{"x": 1}])


def test_unsupported_power_rejected_before_execution(tmp_path):
    with pytest.raises(ValueError, match="Pow"):
        model(tmp_path, GOOD.replace('state["v"] + inputs.get("x", 0)', '2 ** 1000000000'))


@pytest.mark.parametrize("expression", ['b"abc"', '1.5', '2j', '[x for x in range(10)]', '{x: x for x in range(10)}'])
def test_unsupported_constants_and_eager_comprehensions_rejected(tmp_path, expression):
    with pytest.raises(ValueError, match="unsupported"):
        model(tmp_path, GOOD.replace('state["v"] + inputs.get("x", 0)', expression))


def test_format_string_modulo_rejected_before_large_allocation(tmp_path):
    source = GOOD.replace('state["v"] + inputs.get("x", 0)', '"%1000000000d" % 1')
    with pytest.raises(ValueError, match="modulo supports only integers"):
        model(tmp_path, source).run([{"x": 1}])


def test_numeric_modulo_remains_supported(tmp_path):
    source = GOOD.replace('state["v"] + inputs.get("x", 0)', 'inputs.get("x", 0) % 3')
    assert model(tmp_path, source).run([{"x": 7}]) == [{"y": 1}]


def test_sum_cannot_bypass_sequence_allocation_checks(tmp_path):
    source = GOOD.replace('state["v"] + inputs.get("x", 0)', 'sum([[0] * 10000] * 10000, [])')
    with pytest.raises(ValueError, match="sum supports only integers"):
        model(tmp_path, source).run([{"x": 1}])


def test_repeated_allocations_have_cumulative_budget(tmp_path):
    source = GOOD.replace('state["v"] + inputs.get("x", 0)', 'list([0] * 10000 for n in range(100))')
    with pytest.raises(ValueError, match="allocation limit"):
        model(tmp_path, source).run([{"x": 1}])
