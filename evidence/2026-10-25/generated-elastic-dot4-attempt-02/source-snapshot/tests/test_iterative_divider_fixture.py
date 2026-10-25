"""Divider fixture regressions; these never simulate or establish RTL correctness."""
import hashlib
import importlib.util
import json
import re
from pathlib import Path

import pytest
import yaml

from autortl.golden import GoldenModel, qualify_against_examples, validate_examples
from autortl.linter import lint_spec, stub_verilog, top_verilog
from autortl.spec import DesignSpec
from autortl.static_checks import check
from autortl.tbgen import expected_outputs, gen_stimulus, generate
from autortl.verilog_interface import infer_module

ROOT = Path(__file__).resolve().parents[1] / "curriculum/tier3/iterative_divider_build"
MATRIX = [8, 1, 2, 4, 13, 16]
FAULTS = [
    "strict_subtraction_compare", "addition_instead_of_subtraction", "quotient_shift_right",
    "wrong_dividend_shift_bit", "trial_data_msb_cleared", "zero_divisor_quotient_zero",
    "zero_divisor_remainder_zero", "captured_dividend_truncated_eight",
    "captured_divisor_truncated_eight", "hardcoded_eight_iterations", "early_completion",
    "trivial_operand_shortcut", "ready_while_busy", "ready_on_retirement_edge",
    "current_divisor_not_captured", "current_dividend_during_computation",
    "stalled_quotient_drift", "stalled_remainder_drift", "asynchronous_reset",
    "reset_preserves_held_result",
]


def spec():
    return DesignSpec.load(ROOT / "design_spec.json")


def qualification():
    loaded = importlib.util.spec_from_file_location(
        "iterative_divider_qualification_cases", ROOT / "qualification/cases.py")
    module = importlib.util.module_from_spec(loaded)
    loaded.loader.exec_module(module)
    return module


def arithmetic(dividend, divisor, width=8):
    mask = (1 << width) - 1
    return {"quotient": mask if divisor == 0 else dividend // divisor,
            "remainder": dividend if divisor == 0 else dividend % divisor}


def test_divider_fixture_is_combined_build_with_no_reference_seed():
    meta = yaml.safe_load((ROOT / "meta.yaml").read_text(encoding="utf-8"))
    assert meta["mode"] == "build" and meta["generate_golden"] is True
    assert meta["top"] == "iterative_divider" and "design" not in meta
    assert meta["spec"] == "design_spec.json" and meta["tb"] == "iterative_divider_tb.v"
    assert "qualification" not in json.dumps(meta)
    typed = spec()
    assert lint_spec(typed) == []
    assert DesignSpec.from_json(typed.to_json()).to_json() == typed.to_json()


def test_divider_contract_keeps_unsigned_symbolic_operands_and_default_latency():
    typed = spec()
    module = typed.modules[0]
    assert list(module.parameters.items()) == [("WIDTH", 8)]
    assert module.latency_known is True and module.latency == 9
    assert module.compare_mode == "scoreboard" and module.reset.kind == "sync"
    ports = {port.name: port for port in module.ports}
    assert all(ports[name].protocol == "valid_ready"
               for name in ("in_valid", "in_ready", "out_valid", "out_ready"))
    symbols = {port["name"]: port for port in module.interface_signature["ports"]}
    for name in ("dividend", "divisor", "quotient", "remainder"):
        assert ports[name].width == 8 and ports[name].protocol == "none"
        assert ports[name].signed is False
        assert symbols[name]["dimensions"] == [["WIDTH - 1", "0"]]
        assert symbols[name]["signed"] is False
    assert check(stub_verilog(module), module).passed
    reference = qualification().case_sources()["reference"]
    assert infer_module(reference, "iterative_divider_core").interface_signature == module.interface_signature
    assert not check(reference.replace("input [WIDTH-1:0] dividend", "input [7:0] dividend"), module).passed
    wrapper = top_verilog(typed)
    assert ".WIDTH(8)" in wrapper
    top = infer_module(wrapper, "iterative_divider")
    assert top.parameters == {} and top.latency_known is True and top.latency == 9
    assert {port.name: port.width for port in top.ports}["dividend"] == 8
    for phrase in ("WIDTH 1..16", "WIDTH+1", "one outstanding transaction",
                   "no early result", "invalid output fields are unspecified"):
        assert phrase in module.behavior


def test_examples_and_generated_scoreboard_use_unsigned_two_output_arithmetic(tmp_path):
    module = spec().modules[0]
    assert validate_examples(module, require_anchors=True) == []
    for example in module.examples:
        assert example.expected == arithmetic(example.inputs["dividend"], example.inputs["divisor"])
        assert example.after_cycles == 9
    assert any(example.inputs["divisor"] == 0 for example in module.examples)
    path = tmp_path / "arithmetic_oracle.py"
    path.write_text("def init():\n    return {}\ndef step(state, inputs):\n"
                    "    if inputs.get('rst',0):\n        return {}, {'quotient':0, 'remainder':0}\n"
                    "    a=inputs['dividend'] & 255\n    b=inputs['divisor'] & 255\n"
                    "    return state, {'quotient':255 if b==0 else a//b, 'remainder':a if b==0 else a%b}\n",
                    encoding="utf-8")
    oracle = GoldenModel(path)
    assert qualify_against_examples(oracle, module) == []
    rows = gen_stimulus(module, n_random=11)
    assert all(set(row) == {"dividend", "divisor"} for row in rows)
    assert expected_outputs(module, oracle, rows) == [
        arithmetic(row["dividend"], row["divisor"]) for row in rows]
    text = generate(module, oracle, tmp_path / "generated", n_random=11).read_text(encoding="utf-8")
    assert "unstable quotient" in text and "unstable remainder" in text
    assert "output before minimum transfer latency" in text
    assert ".quotient(quotient)" in text and ".remainder(remainder)" in text
    assert ".WIDTH(8)" in text


def test_independent_tb_has_selected_widths_exact_schedule_and_completion_gates():
    # Text presence checks preserve fixture structure; real simulation is separate.
    text = (ROOT / "iterative_divider_tb.v").read_text(encoding="utf-8")
    configured = [int(width) for width in re.findall(
        r"iterative_divider_case #\(\.WIDTH\((\d+)\)", text)]
    assert configured == MATRIX == qualification().MATRIX
    assert ".USE_TOP(1),.CASE_ID(0)" in text and "wire [5:0] finished, failed" in text
    checker, enclosing = text.split("module iterative_divider_tb;", 1)
    assert "TEST PASSED" not in checker and "TEST FAILED" not in checker
    assert text.count('$display("TEST PASSED")') == 1
    assert "wait (&finished)" in enclosing and "failed===6'b000000" in enclosing
    assert "watchdog" in enclosing and "dut." not in text
    for marker in ("exact WIDTH-step result availability / no early or late valid",
                   "single outstanding readiness / retirement-edge bubble",
                   "unsigned quotient / stable held result", "unsigned remainder / stable held result",
                   "accepted transfer age below WIDTH+1", "accepted-retired-discarded conservation",
                   "expected_quotient=dividend_value/divisor_value", "expected_remainder=dividend_value%divisor_value",
                   "expected_quotient=MAX_VALUE", "expected_remainder=dividend_value",
                   "reset_phases!=WIDTH+1", "exhaustive_pairs", "zero_divisors", "random_pairs",
                   "required arithmetic / temporal / reset coverage missing", "COVERAGE case=%0d"):
        assert marker in checker
    assert checker.count("if (model_started) check_outputs;") == 2
    assert "#1;\n            model_started=1;\n            check_outputs;" in checker


def assert_stalled_result_reset_scenario(text):
    """Require explicit stimulus AND measured coverage; presence is not a kill."""
    # Ignore comments and formatting, keeping actual executable tokens in order.
    compact = re.sub(r"\s+", "", re.sub(r"//[^\n]*", "", text))
    assert "reset_stalled_result=0" in compact
    assert "if(result_pending&&!out_ready)reset_stalled_result=reset_stalled_result+1;" in compact
    assert "reset_stalled_result<1" in compact
    assert "reset_stalled_result=%0d" in compact
    assert "reset_result,reset_stalled_result,reset_phases" in compact
    # This reset cannot be hidden by normal output retirement: ready stays low
    # throughout computation, two held cycles and the reset edge itself.
    assert re.search(
        r"step\(0,1,MAX_VALUE,1,0\);"
        r'(?:if\(!last_accept\)fail\("[^"]*"\);)?'
        r"repeat\(WIDTH\)step\(0,1,1,MAX_VALUE,0\);"
        r"repeat\(2\)step\(0,1,1,MAX_VALUE,0\);"
        r"step\(1,1,1,MAX_VALUE,0\);"
        r"step\(0,0,0,0,1\);"
        r"repeat\(WIDTH\+2\)step\(0,0,MAX_VALUE,0,1\);",
        compact,
    )


def test_independent_tb_resets_stalled_result_without_normal_retirement():
    text = (ROOT / "iterative_divider_tb.v").read_text(encoding="utf-8")
    assert_stalled_result_reset_scenario(text)


@pytest.mark.parametrize("omission", ["directed_reset", "counter", "gate", "report"])
def test_stalled_reset_structure_regression_rejects_coverage_omissions(omission):
    text = (ROOT / "iterative_divider_tb.v").read_text(encoding="utf-8")
    targets = {
        "directed_reset": ("step(1,1,1,MAX_VALUE,0);", "step(1,1,1,MAX_VALUE,1);"),
        "counter": ("if (result_pending&&!out_ready) reset_stalled_result=reset_stalled_result+1;", ""),
        "gate": ("reset_stalled_result<1", "1'b0"),
        "report": ("reset_stalled_result=%0d", "untracked_stalled_reset=%0d"),
    }
    original, replacement = targets[omission]
    assert text.count(original) == 1
    changed = text.replace(original, replacement, 1)
    with pytest.raises(AssertionError):
        assert_stalled_result_reset_scenario(changed)


@pytest.mark.parametrize("name", ["reference", *FAULTS])
def test_twenty_one_sources_preserve_claimed_interface_and_default_latency(name):
    sources = qualification().case_sources()
    assert set(sources) == {"reference", *FAULTS}
    assert len(sources) == len(set(sources.values())) == 21
    assert check(sources[name], spec().modules[0]).passed
    assert "// @latency 9" in sources[name]
    if name != "reference":
        assert sources[name] != sources["reference"]


def test_every_fault_has_exact_replayable_edits_and_truthful_scope_notes():
    helper = qualification()
    sources = helper.case_sources()
    targets = helper.mutation_targets(sources["reference"])
    assert set(targets) == set(FAULTS)
    for name, edits in targets.items():
        assert edits
        reconstructed = sources["reference"]
        for original, replacement in edits:
            assert original != replacement and sources["reference"].count(original) == 1
            reconstructed = reconstructed.replace(original, replacement, 1)
        assert reconstructed == sources[name]
    assert "guard bit can be equivalent" in helper.MUTATION_NOTES["trial_data_msb_cleared"]
    assert "symbolic register and public port widths remain unchanged" in helper.MUTATION_NOTES["captured_dividend_truncated_eight"]
    assert "initial unknown out_valid to reset normally" in helper.MUTATION_NOTES["reset_preserves_held_result"]
    for name in ("stalled_quotient_drift", "stalled_remainder_drift"):
        assert sources[name].count("always @") == 1


@pytest.mark.parametrize("name", FAULTS)
@pytest.mark.parametrize("kind", ["missing", "duplicate"])
def test_mutation_rejects_reference_anchor_drift(name, kind):
    helper = qualification()
    reference = helper.case_sources()["reference"]
    target = helper.MUTATIONS[name][0][0]
    changed = reference.replace(target, "// missing target") if kind == "missing" else reference + "\n" + target
    with pytest.raises(ValueError, match="qualification target no longer unique"):
        helper.case_sources(changed)


def test_materializer_records_exact_sources_matrix_and_assertion_requirements(tmp_path):
    result = qualification().materialize_cases(tmp_path / "cases")
    assert result["status"] == "prepared_not_simulated" and result["top"] == "iterative_divider_tb"
    assert result["domain"] == dict(width_min=1, width_max=16)
    assert [row["width"] for row in result["matrix"]] == MATRIX
    assert [row["default_wrapper"] for row in result["matrix"]] == [True, False, False, False, False, False]
    assert len(result["cases"]) == 21
    expected_tb = hashlib.sha256((ROOT / "iterative_divider_tb.v").read_bytes()).hexdigest()
    expected_sources = qualification().case_sources()
    for case in result["cases"]:
        files = {Path(item["path"]).name: item for item in case["files"]}
        assert set(files) == {"iterative_divider_core.v", "iterative_divider.v", "iterative_divider_tb.v"}
        for item in files.values():
            assert hashlib.sha256(Path(item["path"]).read_bytes()).hexdigest() == item["sha256"]
        assert files["iterative_divider_tb.v"]["sha256"] == expected_tb
        assert Path(files["iterative_divider_core.v"]["path"]).read_bytes() == expected_sources[case["name"]].encode("utf-8")
        control = case["name"] == "reference"
        assert case["expected_verdict"] == ("TEST PASSED" if control else "TEST FAILED")
        assert case["required_failure_kind"] == (None if control else "behavioral_assertion")
        assert bool(case["mutation_targets"]) is not control
    assert json.loads((tmp_path / "cases/manifest.json").read_text(encoding="utf-8")) == result
    with pytest.raises(FileExistsError):
        qualification().materialize_cases(tmp_path / "cases")
