"""Scoreboard example payload coverage; no vendor or model processes."""
import copy
import json
import random
from pathlib import Path
from unittest.mock import Mock

import pytest

from autortl import tbgen
from autortl.spec import DesignSpec, IOExample, ModuleSpec, Port, ResetSpec


def module_spec(width=8, *, active_high=True, renamed=False):
    reset = "reset_n" if renamed else "rst"
    iv, ir, ov, ore = (("request_valid", "request_ready", "response_valid", "response_ready")
                       if renamed else ("in_valid", "in_ready", "out_valid", "out_ready"))
    return ModuleSpec(
        name="example_channel", behavior="one accepted pair gives one result",
        ports=[Port("clk", "input", 1), Port(reset, "input", 1),
               Port("a", "input", width), Port("b", "input", width),
               Port("y", "output", width),
               Port(iv, "input", 1, protocol="valid_ready"),
               Port(ir, "output", 1, protocol="valid_ready"),
               Port(ov, "output", 1, protocol="valid_ready"),
               Port(ore, "input", 1, protocol="valid_ready")],
        latency=1, compare_mode="scoreboard",
        reset=ResetSpec(signal=reset, active_high=active_high, duration_cycles=3))


def example(a=7, b=9, *, inputs=None, expected=None, after_cycles=1):
    values = {"rst": 0, "in_valid": 1, "a": a, "b": b}
    if inputs is not None:
        values = inputs
    return IOExample(values, {"y": 0} if expected is None else expected, after_cycles)


def old_rows(spec, n_random, seed):
    inputs = [p for p in spec.ports if p.name in ("a", "b")]
    corners = [{p.name: fn(p.width) for p in inputs}
               for fn in (lambda width: 0, lambda width: (1 << width)-1,
                          lambda width: 1 << (width-1))]
    rng = random.Random(seed)
    return corners + [{p.name: rng.randrange(1 << p.width) for p in inputs}
                      for _ in range(n_random)]


def test_seeds_follow_original_corners_and_preserve_exact_random_tail():
    spec = module_spec()
    spec.examples = [example(7, 9), example(255, 0), example(7, 9), example(0, 0),
                     example(255, 255), example(128, 128), example(2, 3)]
    before = copy.deepcopy(spec.examples)
    actual = tbgen.gen_stimulus(spec, n_random=17, seed=751)
    original = old_rows(spec, 17, 751)
    assert actual[:3] == original[:3]
    assert actual[3:6] == [{"a": 7, "b": 9}, {"a": 255, "b": 0}, {"a": 2, "b": 3}]
    assert actual[6:] == original[3:]
    assert actual == tbgen.gen_stimulus(spec, n_random=17, seed=751)
    assert spec.examples == before
    assert all(set(row) == {"a", "b"} for row in actual)


@pytest.mark.parametrize("inputs", [
    {"rst": 0, "in_valid": 0, "a": 7, "b": 9},
    {"rst": 0, "a": 7, "b": 9},
    {"in_valid": 1, "a": 7, "b": 9},
    {"rst": 1, "in_valid": 1, "a": 7, "b": 9},
    {"rst": 0, "in_valid": 1, "a": 7},
    {"rst": 0, "in_valid": 1, "b": 9},
])
def test_valid_partial_inactive_or_reset_examples_are_not_seeded(inputs):
    spec = module_spec()
    spec.examples = [example(inputs=inputs)]
    assert tbgen.gen_stimulus(spec, n_random=0) == old_rows(spec, 0, 1234)


@pytest.mark.parametrize("ready", [None, 0, 1])
def test_example_backpressure_is_not_a_payload_eligibility_condition(ready):
    spec = module_spec()
    given = {"rst": 0, "in_valid": 1, "a": 7, "b": 9}
    if ready is not None:
        given["out_ready"] = ready
    spec.examples = [example(inputs=given, after_cycles=9)]
    assert tbgen.gen_stimulus(spec, n_random=0)[3:] == [{"a": 7, "b": 9}]


def test_renamed_valid_and_active_low_reset_follow_driver_channel_rule():
    spec = module_spec(active_high=False, renamed=True)
    spec.examples = [
        example(inputs={"reset_n": 1, "request_valid": 1, "a": 7, "b": 9}),
        example(inputs={"reset_n": 0, "request_valid": 1, "a": 2, "b": 3}),
        example(inputs={"reset_n": 1, "request_valid": 0, "a": 4, "b": 5}),
    ]
    rows = tbgen.gen_stimulus(spec, n_random=0)
    assert rows[3:] == [{"a": 7, "b": 9}]
    text = tbgen.generate_scoreboard_tb(spec, rows, [{"y": 0}] * len(rows))
    assert "request_valid = (_autortl_push" in text
    assert "response_ready = (_autortl_cycle" in text


@pytest.mark.parametrize("case", ["missing", "ambiguous", "wide"])
def test_seed_selection_rejects_invalid_input_valid_channel_before_rng(monkeypatch, case):
    spec = module_spec()
    if case == "missing":
        spec.ports = [port for port in spec.ports if port.name != "in_valid"]
    elif case == "ambiguous":
        spec.ports.append(Port("other_valid", "input", 1, protocol="valid_ready"))
    else:
        next(port for port in spec.ports if port.name == "in_valid").width = 2
    rng = Mock(side_effect=AssertionError("must not allocate random rows"))
    monkeypatch.setattr(tbgen.random, "Random", rng)
    with pytest.raises(ValueError, match="exactly one input and output valid/ready channel"):
        tbgen.gen_stimulus(spec)
    rng.assert_not_called()


def test_width_one_keeps_duplicate_original_corners_but_deduplicates_seeds():
    spec = module_spec(width=1)
    spec.examples = [example(1, 1), example(0, 1), example(0, 1)]
    assert tbgen.gen_stimulus(spec, n_random=0) == [
        {"a": 0, "b": 0}, {"a": 1, "b": 1}, {"a": 1, "b": 1}, {"a": 0, "b": 1}]


def test_generate_uses_oracle_expected_outputs_not_declared_example_outputs(tmp_path):
    spec = module_spec()
    spec.examples = [example(7, 9, expected={"y": 123}, after_cycles=17)]
    golden = Mock()
    golden.run.side_effect = lambda rows: [{"y": row["a"] ^ row["b"]} for row in rows]
    output = tmp_path / "generated"
    tbgen.generate(spec, golden, output, n_random=0)
    saved = json.loads((output / "stimulus.json").read_text(encoding="utf-8"))
    assert saved["stimulus"][3] == {"a": 7, "b": 9}
    assert saved["expected"][3] == {"y": 14}
    rows = golden.run.call_args.args[0]
    assert len(rows) == 3 + 4  # Reset prefix plus four transaction rows, not 17 trace steps.
    assert all(row["rst"] == 1 for row in rows[:3])
    assert rows[-1] == {"a": 7, "b": 9, "in_valid": 1, "out_ready": 1, "rst": 0}


def malformed_examples(case):
    result = [example()]
    if case == "list_type":
        return None
    if case == "count":
        return result * 101
    if case == "object":
        return [object()]
    row = result[0]
    if case == "input_bool": row.inputs["a"] = True
    elif case == "valid_bool": row.inputs["in_valid"] = True
    elif case == "reset_bool": row.inputs["rst"] = False
    elif case == "expected_bool": row.expected["y"] = False
    elif case == "large_input": row.inputs["a"] = 256
    elif case == "negative_input": row.inputs["b"] = -1
    elif case == "large_expected": row.expected["y"] = 256
    elif case == "unknown_input": row.inputs["unknown"] = 1
    elif case == "missing_expected": row.expected = {}
    elif case == "unknown_expected": row.expected["unknown"] = 1
    elif case == "cycles_bool": row.after_cycles = True
    elif case == "cycles_zero": row.after_cycles = 0
    elif case == "cycles_large": row.after_cycles = 10001
    elif case == "combined_cycles": return [example(after_cycles=6000), example(after_cycles=6000)]
    elif case == "inactive_malformed": row.inputs.update(in_valid=0, a=256)
    else: raise AssertionError("unknown malformed case")
    return result


@pytest.mark.parametrize("case", [
    "list_type", "count", "object", "input_bool", "valid_bool", "reset_bool", "expected_bool",
    "large_input", "negative_input", "large_expected", "unknown_input", "missing_expected",
    "unknown_expected", "cycles_bool", "cycles_zero", "cycles_large", "combined_cycles", "inactive_malformed",
])
def test_malformed_examples_fail_before_random_or_oracle_or_output_creation(tmp_path, monkeypatch, case):
    spec = module_spec()
    spec.examples = malformed_examples(case)
    golden = Mock()
    rng = Mock(side_effect=AssertionError("must not allocate random rows"))
    monkeypatch.setattr(tbgen.random, "Random", rng)
    output = tmp_path / "not_created"
    with pytest.raises(ValueError, match="invalid scoreboard examples"):
        tbgen.generate(spec, golden, output, n_random=10)
    rng.assert_not_called()
    golden.run.assert_not_called()
    assert not output.exists()


@pytest.mark.parametrize("count", [True, False, -1, 9995, 10**12, 1.5, "4"])
def test_original_random_bound_rejects_before_examples_or_rng(tmp_path, monkeypatch, count):
    spec = module_spec()
    validation = Mock(side_effect=AssertionError("must not inspect examples"))
    rng = Mock(side_effect=AssertionError("must not allocate random rows"))
    monkeypatch.setattr(tbgen, "validate_examples", validation)
    monkeypatch.setattr(tbgen.random, "Random", rng)
    golden = Mock()
    with pytest.raises(ValueError, match="invalid stimulus count including reset prefix"):
        tbgen.generate(spec, golden, tmp_path / "not_created", n_random=count)
    validation.assert_not_called()
    rng.assert_not_called()
    golden.run.assert_not_called()
    assert not (tmp_path / "not_created").exists()


def test_extra_unique_seed_overflow_rejected_before_rng_or_oracle(tmp_path, monkeypatch):
    spec = module_spec()
    spec.examples = [example(7, 9)]
    rng = Mock(side_effect=AssertionError("must not allocate random rows"))
    monkeypatch.setattr(tbgen.random, "Random", rng)
    golden = Mock()
    with pytest.raises(ValueError, match="including example payloads and reset exceeds 10000"):
        tbgen.generate(spec, golden, tmp_path / "not_created", n_random=9994)
    rng.assert_not_called()
    golden.run.assert_not_called()
    assert not (tmp_path / "not_created").exists()


def test_original_upper_boundary_remains_available_without_unique_seeds():
    spec = module_spec()
    spec.examples = [example(0, 0), example(255, 255), example(128, 128)]
    assert len(tbgen.gen_stimulus(spec, n_random=9994)) + spec.reset.duration_cycles == 10000


def test_maximum_example_list_seeds_are_bounded_before_large_random_tail():
    spec = module_spec()
    spec.examples = [example(index, 0) for index in range(1, 101)]
    rows = tbgen.gen_stimulus(spec, n_random=9894)
    assert len(rows) + spec.reset.duration_cycles == 10000
    assert rows[3:103] == [{"a": index, "b": 0} for index in range(1, 101)]
    with pytest.raises(ValueError, match="including example payloads and reset exceeds 10000"):
        tbgen.gen_stimulus(spec, n_random=9895)


def test_fixed_latency_stimulus_ignores_examples_and_preserves_original_sequence():
    spec = module_spec()
    spec.compare_mode = "fixed_latency"
    spec.ports = [port for port in spec.ports if port.protocol == "none"]
    spec.examples = None  # This path did not validate or seed examples before this change.
    assert tbgen.gen_stimulus(spec, n_random=7, seed=71) == old_rows(spec, 7, 71)


def test_actual_divider_spec_seeds_nonzero_dividend_zero_divisor():
    root = Path(__file__).resolve().parents[1]
    spec = DesignSpec.load(root / "curriculum/tier3/iterative_divider_build/design_spec.json").modules[0]
    rows = tbgen.gen_stimulus(spec, n_random=100, seed=1234)
    assert {"dividend": 255, "divisor": 0} in rows[3:-100]
    original_rng = random.Random(1234)
    expected_tail = [{"dividend": original_rng.randrange(256), "divisor": original_rng.randrange(256)}
                     for _ in range(100)]
    assert rows[-100:] == expected_tail
