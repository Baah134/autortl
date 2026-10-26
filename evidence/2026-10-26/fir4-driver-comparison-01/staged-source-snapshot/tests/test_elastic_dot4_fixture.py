"""Pure fixture contracts and assertion framing; no RTL compilation/simulation."""
import hashlib
import importlib.util
import json
import re
from pathlib import Path

import pytest
import yaml

from autortl.linter import lint_spec, top_verilog
from autortl.spec import DesignSpec
from autortl.tbqual import assertion_failure_proof
from autortl.verilog_interface import infer_module

ROOT = Path(__file__).resolve().parents[1] / "curriculum/tier3/elastic_dot4_build"
FAULTS = ["dropped_product", "signed_arithmetic", "pair_carry_truncation",
          "final_carry_truncation", "early_output", "late_output", "accept_full",
          "overwrite_blocked_stage1", "drop_blocked_stage1", "clear_stalled_valid",
          "corrupt_held_output", "duplicate_retirement", "lose_full_replacement",
          "throughput_bubble", "retained_stage1_reset", "retained_stage2_reset",
          "asynchronous_reset", "incorrect_downstream_ready"]


def spec():
    return DesignSpec.load(ROOT / "design_spec.json")


def qualification():
    loader = importlib.util.spec_from_file_location("elastic_dot4_cases", ROOT / "qualification/cases.py")
    module = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(module)
    return module


def shape(ports):
    return [(p.name, p.direction, p.width, p.signed) for p in ports]


def test_metadata_is_combined_build_without_reference_seed():
    meta = yaml.safe_load((ROOT / "meta.yaml").read_text(encoding="utf-8"))
    assert meta["mode"] == "build" and meta["generate_golden"] is True
    assert meta["top"] == "elastic_dot4" and meta["tb"] == "elastic_dot4_tb.v"
    assert meta["spec"] == "design_spec.json"
    assert "design" not in meta and "reference" not in json.dumps(meta)
    typed = spec()
    assert lint_spec(typed) == []
    assert DesignSpec.from_json(typed.to_json()).to_json() == typed.to_json()
    assert len(typed.modules) == 1 and typed.connections == []


def test_exact_unsigned_payload_and_handshake_ports():
    typed = spec()
    child = typed.modules[0]
    assert child.name == "elastic_dot4_core" and child.parameters == {}
    ports = {p.name: p for p in child.ports}
    controls = {p.name: p.direction for p in child.ports if p.protocol == "valid_ready"}
    assert controls == {"in_valid":"input", "in_ready":"output", "out_valid":"output", "out_ready":"input"}
    operands = [p for p in child.ports if p.direction == "input" and p.protocol == "none" and p.name not in ("clk", "rst")]
    assert [p.name for p in operands] == [f"{prefix}{i}" for i in range(4) for prefix in ("a", "b")]
    assert all(p.width == 8 and not p.signed for p in operands)
    assert ports["out_data"].width == 18 and ports["out_data"].direction == "output"
    assert all(not p.signed for p in child.ports)
    assert all(ports[name].width == 1 for name in ("clk", "rst", *controls))
    assert shape(typed.external_ports) == shape(child.ports)


def test_scoreboard_minimum_age_and_transparent_latency():
    typed = spec()
    child = typed.modules[0]
    assert child.compare_mode == "scoreboard" and child.latency == 2 and child.latency_known
    assert child.reset.kind == "sync" and child.reset.active_high and child.reset.signal == "rst"
    wrapper = top_verilog(typed)
    parsed = infer_module(wrapper, typed.top_name)
    assert parsed.latency_known and parsed.latency == 2 and parsed.parameters == {}
    assert wrapper.startswith("`timescale 1ns/1ps")
    for phrase in ("NOT total nonempty", "minimum accepted-transfer age2", "ALL eight operands",
                   "no valid bits, occupancy, pipeline queue", "Invalid out_data is unspecified"):
        assert phrase in child.behavior


def test_example_arithmetic_and_carries():
    child = spec().modules[0]
    for example in child.examples:
        inputs = example.inputs
        result = sum(inputs[f"a{i}"]*inputs[f"b{i}"] for i in range(4))
        assert example.expected == {"out_data": result}
        assert example.after_cycles == 2 and inputs["rst"] == 0
    assert max(e.expected["out_data"] for e in child.examples) == 260100
    assert 2*255*255 == 130050 > (1<<16)-1
    assert 4*255*255 == 260100 < (1<<18)
    assert 128*255 == 32640


def test_case_inventory_and_exact_targets():
    module = qualification()
    cases = module.case_sources()
    assert list(cases) == ["reference"] + FAULTS and list(module.MUTATIONS) == FAULTS
    assert len(set(cases.values())) == 19
    assert cases["reference"] == (ROOT / "qualification/reference.v").read_text(encoding="utf-8")
    for name, edits in module.MUTATIONS.items():
        source = cases["reference"]
        for old, new in edits:
            assert source.count(old) == 1
            source = source.replace(old, new, 1)
        assert source == cases[name]
    assert "if(in_ready || in_valid) begin // capture_gate" in cases["overwrite_blocked_stage1"]
    for i in (1, 2):
        assert f"if(v{i}) v{i}<=v{i}; else v{i}<=0;" in cases[f"retained_stage{i}_reset"]


@pytest.mark.parametrize("name", ["reference"] + FAULTS)
def test_mutants_preserve_interface_and_declared_age(name):
    child = spec().modules[0]
    parsed = infer_module(qualification().case_sources()[name], child.name)
    assert shape(parsed.ports) == shape(child.ports)
    assert parsed.latency_known and parsed.latency == 2 and parsed.parameters == {}


def test_materialized_inputs_hashes_and_identical_tb(tmp_path):
    module = qualification()
    cases = module.case_sources()
    output = tmp_path / "prepared"
    manifest = module.materialize_cases(output)
    assert manifest["status"] == "prepared_not_simulated" and manifest["top"] == "elastic_dot4_tb"
    assert len(manifest["cases"]) == 19
    assert json.loads((output / "manifest.json").read_text()) == manifest
    tb = (ROOT / "elastic_dot4_tb.v").read_bytes()
    count = 0
    for entry in manifest["cases"]:
        assert entry["expected_verdict"] == ("TEST PASSED" if entry["name"] == "reference" else "TEST FAILED")
        assert entry["required_failure_kind"] == (None if entry["name"] == "reference" else "behavioral_assertion")
        assert {Path(f["path"]).name for f in entry["files"]} == {"children.v", "elastic_dot4.v", "elastic_dot4_tb.v"}
        for file in entry["files"]:
            path = Path(file["path"])
            assert path.is_relative_to(output)
            assert hashlib.sha256(path.read_bytes()).hexdigest() == file["sha256"]
            count += 1
        assert (output / entry["name"] / "elastic_dot4_tb.v").read_bytes() == tb
        assert (output / entry["name"] / "children.v").read_text(encoding="utf-8") == cases[entry["name"]]
        assert (output / entry["name"] / "elastic_dot4.v").read_text(encoding="utf-8") == top_verilog(spec())
    assert count == 57
    before = (output / "manifest.json").read_bytes()
    with pytest.raises(FileExistsError):
        module.materialize_cases(output)
    assert (output / "manifest.json").read_bytes() == before


def test_actual_behavior_display_matches_unchanged_assertion_protocol(tmp_path):
    source = (ROOT / "elastic_dot4_tb.v").read_text(encoding="utf-8")
    task = re.search(r"task behavior_fail;(.*?)endtask", source, re.S).group(1)
    display = re.search(r'\$display\("([^"]+)"', task).group(1)
    assert display.startswith("FAIL BEHAVIOR rule=")
    assert "BEHAVIOR_FAIL" not in display
    # Synthetic retained log tests framing only, not actual simulator behavior.
    (tmp_path / "sim_log.txt").write_text("FAIL BEHAVIOR rule=capacity cycle=4\nTEST FAILED: 1 assertions\n")
    assert assertion_failure_proof(tmp_path)[0]


@pytest.mark.parametrize("detail", ["COVERAGE_FAIL rule=missing cycle=4",
    "CHECKER_FAIL rule=reference cycle=4", "BEHAVIOR_FAIL rule=capacity cycle=4",
    "TEST FAILED: watchdog", ""])
def test_nonbehavior_or_old_marker_is_not_assertion_proof(tmp_path, detail):
    (tmp_path / "sim_log.txt").write_text(detail + "\nTEST FAILED: 1 assertions\n")
    assert not assertion_failure_proof(tmp_path)[0]


def test_checker_and_coverage_tasks_cannot_emit_behavioral_prefix():
    source = (ROOT / "elastic_dot4_tb.v").read_text(encoding="utf-8")
    for task_name in ("checker_fail", "coverage_fail"):
        task = re.search(r"task " + task_name + r";(.*?)endtask", source, re.S).group(1)
        assert '"FAIL ' not in task and '"BEHAVIOR_FAIL' not in task
    assert "stage1_pulses!=1 || both_pulses!=1" in source
    assert "full_replacements<30" in source and "steady_best<30" in source
