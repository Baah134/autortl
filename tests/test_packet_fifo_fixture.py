"""Packet fixture checks only; these tests do not measure RTL behavior."""
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

ROOT = Path(__file__).resolve().parents[1] / "curriculum/tier2/packet_fifo_build"
MATRIX = [(8, 3), (1, 1), (8, 2), (8, 4), (13, 5), (16, 8)]
FAULTS = [
    "hardcoded_depth_three", "payload_capture_truncated_eight", "power_of_two_wrap",
    "early_full", "late_full", "full_simultaneous_blocked", "simultaneous_occupancy_lost",
    "simultaneous_retirement_lost", "output_truncated_eight", "unstable_stalled_payload",
    "incorrect_data_order", "asynchronous_reset", "combinational_bypass",
    "last_stuck_zero", "last_stuck_one", "current_input_last_bypass",
    "unaccepted_tag_write", "displaced_tag_read", "tag_only_stall_drift",
]


def spec():
    return DesignSpec.load(ROOT / "design_spec.json")


def qualification():
    loaded = importlib.util.spec_from_file_location(
        "packet_fifo_qualification_cases", ROOT / "qualification/cases.py")
    module = importlib.util.module_from_spec(loaded)
    loaded.loader.exec_module(module)
    return module


def test_packet_fixture_is_combined_build_with_no_reference_seed():
    meta = yaml.safe_load((ROOT / "meta.yaml").read_text(encoding="utf-8"))
    assert meta["mode"] == "build" and meta["generate_golden"] is True
    assert meta["top"] == "packet_fifo" and "design" not in meta
    assert meta["spec"] == "design_spec.json" and meta["tb"] == "packet_fifo_tb.v"
    assert "qualification" not in json.dumps(meta)
    typed = spec()
    assert lint_spec(typed) == []
    assert DesignSpec.from_json(typed.to_json()).to_json() == typed.to_json()


def test_packet_contract_preserves_defaults_symbolic_data_and_payload_markers():
    typed = spec()
    module = typed.modules[0]
    assert list(module.parameters.items()) == [("WIDTH", 8), ("DEPTH", 3)]
    assert module.latency_known is True and module.latency == 1
    assert module.compare_mode == "scoreboard" and module.reset.kind == "sync"
    ports = {port.name: port for port in module.ports}
    assert {name: ports[name].protocol for name in ("in_last", "out_last")} == {
        "in_last": "none", "out_last": "none"}
    assert ports["in_last"].width == ports["out_last"].width == 1
    assert all(ports[name].protocol == "valid_ready"
               for name in ("in_valid", "in_ready", "out_valid", "out_ready"))
    symbols = {port["name"]: port["dimensions"]
               for port in module.interface_signature["ports"]}
    assert symbols["in_data"] == symbols["out_data"] == [["WIDTH - 1", "0"]]
    assert symbols["in_last"] == symbols["out_last"] == []
    assert check(stub_verilog(module), module).passed
    reference = qualification().case_sources()["reference"]
    assert infer_module(reference, "packet_fifo_core").interface_signature == module.interface_signature
    assert not check(reference.replace("input [WIDTH-1:0] in_data", "input [7:0] in_data"), module).passed
    wrapper = top_verilog(typed)
    assert ".WIDTH(8)" in wrapper and ".DEPTH(3)" in wrapper
    top = infer_module(wrapper, "packet_fifo")
    assert top.parameters == {} and top.latency_known is True and top.latency == 1
    assert {port.name: port.width for port in top.ports}["in_data"] == 8
    for phrase in ("WIDTH 1..16", "DEPTH 1..8", "partial packet", "Invalid out_data and out_last are unspecified"):
        assert phrase in module.behavior


def test_multi_output_oracle_examples_and_generated_scoreboard_include_last(tmp_path):
    module = spec().modules[0]
    assert validate_examples(module, require_anchors=True) == []
    path = tmp_path / "oracle.py"
    path.write_text("def init():\n    return {}\ndef step(state, inputs):\n"
                    "    if inputs.get('rst',0):\n        return {}, {'out_data':0, 'out_last':0}\n"
                    "    return state, {'out_data':inputs['in_data'] & 255, 'out_last':inputs['in_last'] & 1}\n",
                    encoding="utf-8")
    oracle = GoldenModel(path)
    assert qualify_against_examples(oracle, module) == []
    rows = gen_stimulus(module, n_random=9)
    assert all(set(row) == {"in_data", "in_last"} for row in rows)
    assert expected_outputs(module, oracle, rows) == [
        {"out_data": row["in_data"], "out_last": row["in_last"]} for row in rows]
    text = generate(module, oracle, tmp_path / "generated", n_random=9).read_text(encoding="utf-8")
    assert "unstable out_data" in text and "unstable out_last" in text
    assert "output before minimum transfer latency" in text
    assert ".in_last(in_last)" in text and ".out_last(out_last)" in text


def test_independent_tb_matrix_scenarios_and_single_final_verdict_are_explicit():
    # Presence checks are fixture regressions, never behavioral admission proof.
    text = (ROOT / "packet_fifo_tb.v").read_text(encoding="utf-8")
    configured = [(int(width), int(depth)) for width, depth in re.findall(
        r"packet_fifo_case #\(\.WIDTH\((\d+)\),\.DEPTH\((\d+)\)", text)]
    assert configured == MATRIX == qualification().MATRIX
    assert ".USE_TOP(1),.CASE_ID(0)" in text and "wire [5:0] finished, failed" in text
    checker, enclosing = text.split("module packet_fifo_tb;", 1)
    assert "TEST PASSED" not in checker and "TEST FAILED" not in checker
    assert text.count('$display("TEST PASSED")') == 1
    assert "wait (&finished)" in enclosing and "failed===6'b000000" in enclosing
    assert "watchdog" in enclosing and "dut." not in text
    for marker in ("before capture", "accepted transfer age below one", "expected_data[shift_index]=expected_data[shift_index+1]",
                   "expected_last[shift_index]=expected_last[shift_index+1]", "beat conservation", "marker conservation",
                   "full_boundary_simultaneous", "ending_stalls", "ordinary_stalls", "idle_tag_changes",
                   "required scenario coverage missing", "partial packet", "marker_resets", "COVERAGE case=%0d"):
        assert marker in checker
    for length in (1, 2, 3, 4, 7, 17):
        assert "packet_length=" + str(length) + ";" in checker


@pytest.mark.parametrize("name", ["reference", *FAULTS])
def test_twenty_qualification_sources_preserve_claimed_interface_and_latency(name):
    sources = qualification().case_sources()
    assert set(sources) == {"reference", *FAULTS}
    assert len(sources) == len(set(sources.values())) == 20
    assert check(sources[name], spec().modules[0]).passed
    assert "// @latency 1" in sources[name]
    if name != "reference":
        assert sources[name] != sources["reference"]


def test_fault_provenance_is_exact_and_every_fault_changes_source():
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
    capture = sources["payload_capture_truncated_eight"]
    assert "reg [WIDTH:0] memory" in capture
    assert "memory[write_pointer][WIDTH-1:0] <= in_data & 8'hff;" in capture
    for name in ("unaccepted_tag_write", "tag_only_stall_drift"):
        assert sources[name].count("always @") == 1
    bypass = sources["combinational_bypass"]
    assert "always" not in bypass and "assign out_last = in_last;" in bypass
    assert infer_module(bypass, "packet_fifo_core").latency == 1  # Annotation is not proof.


@pytest.mark.parametrize("kind", ["missing", "duplicate"])
def test_mutation_rejects_reference_target_drift(kind):
    helper = qualification()
    reference = helper.case_sources()["reference"]
    target = helper.MUTATIONS["hardcoded_depth_three"][0][0]
    changed = reference.replace(target, "// missing target") if kind == "missing" else reference + "\n" + target
    with pytest.raises(ValueError, match="qualification target no longer unique"):
        helper.case_sources(changed)


def test_materialized_inputs_have_expected_verdicts_and_exact_byte_hashes(tmp_path):
    result = qualification().materialize_cases(tmp_path / "cases")
    assert result["status"] == "prepared_not_simulated" and result["top"] == "packet_fifo_tb"
    assert result["domain"] == dict(width_min=1, width_max=16, depth_min=1, depth_max=8)
    assert [(row["width"], row["depth"]) for row in result["matrix"]] == MATRIX
    assert [row["default_wrapper"] for row in result["matrix"]] == [True, False, False, False, False, False]
    assert len(result["cases"]) == 20
    expected_tb = hashlib.sha256((ROOT / "packet_fifo_tb.v").read_bytes()).hexdigest()
    for case in result["cases"]:
        files = {Path(item["path"]).name: item for item in case["files"]}
        assert set(files) == {"packet_fifo_core.v", "packet_fifo.v", "packet_fifo_tb.v"}
        for item in files.values():
            assert hashlib.sha256(Path(item["path"]).read_bytes()).hexdigest() == item["sha256"]
        assert files["packet_fifo_tb.v"]["sha256"] == expected_tb
        control = case["name"] == "reference"
        assert case["expected_verdict"] == ("TEST PASSED" if control else "TEST FAILED")
        assert case["required_failure_kind"] == (None if control else "behavioral_assertion")
        assert bool(case["mutation_targets"]) is not control
        if case["name"] == "payload_capture_truncated_eight":
            assert "does not change the declared physical memory width" in case["mutation_note"]
    assert json.loads((tmp_path / "cases/manifest.json").read_text(encoding="utf-8")) == result
    with pytest.raises(FileExistsError):
        qualification().materialize_cases(tmp_path / "cases")
