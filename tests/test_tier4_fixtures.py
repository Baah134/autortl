"""Tier4 build fixtures: structure, typed specs, testbench shape and mutant targets.

No Vivado, simulator or model call. Passing this establishes static fixture
invariants only; testbench qualification needs curriculum/tier4/qualify_tier4.py.
"""
import importlib.util
import json
import re
from pathlib import Path

import pytest
import yaml

from autortl.config import RunConfig
from autortl.golden import GoldenModel, qualify_against_examples, validate_examples
from autortl.linter import lint_spec, top_verilog
from autortl.spec import DesignSpec
from autortl.static_checks import check
from autortl.verilog_interface import module_declared_latency
from curriculum import runner

TIER4 = Path(__file__).resolve().parents[1] / "curriculum" / "tier4"
ENTRIES = ["crc16_stream_build", "rr_regfile_build", "spi_master_build"]
REQUIRED_META = {"mode", "top", "spec", "tb", "iterations", "objective", "pass_criteria"}


def entry_dirs():
    return sorted(p for p in TIER4.iterdir() if p.is_dir() and p.name != "__pycache__")


def load(name):
    entry = TIER4 / name
    meta = yaml.safe_load((entry / "meta.yaml").read_text(encoding="utf-8"))
    spec = DesignSpec.load(entry / meta["spec"])
    tb = (entry / meta["tb"]).read_text(encoding="utf-8")
    reference = (entry / "qualification" / "reference.v").read_text(encoding="utf-8")
    mutants = json.loads((entry / "qualification" / "mutants.json").read_text(encoding="utf-8"))
    return entry, meta, spec, tb, reference, mutants


def qualifier():
    loader = importlib.util.spec_from_file_location("qualify_tier4", TIER4 / "qualify_tier4.py")
    module = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(module)
    return module


def test_tier4_contains_exactly_the_three_build_entries():
    assert [p.name for p in entry_dirs()] == ENTRIES


@pytest.mark.parametrize("name", ENTRIES)
def test_metadata_maps_to_a_valid_build_config(name):
    entry, meta, spec, *_ = load(name)
    assert REQUIRED_META <= set(meta)
    assert meta["mode"] == "build" and meta["objective"] == "minimize_luts"
    assert meta["spec"] == "design_spec.json" and meta["iterations"] in (2, 3)
    assert meta["pass_criteria"] == {"timing_met": True}
    assert type(meta.get("generate_golden", False)) is bool
    assert runner._metadata(entry) == meta
    config = RunConfig(mode="build", top_module=meta["top"], spec_path=entry / meta["spec"],
                       testbench_path=entry / meta["tb"], objective=meta["objective"],
                       max_iterations=meta["iterations"],
                       generate_golden=meta.get("generate_golden", False))
    config.validate()
    assert spec.top_name == meta["top"]


@pytest.mark.parametrize("name", ENTRIES)
def test_spec_lints_clean_with_bounded_concrete_examples(name):
    _, _, spec, *_ = load(name)
    assert lint_spec(spec) == []
    assert DesignSpec.from_json(spec.to_json()).to_json() == spec.to_json()
    for module in spec.modules:
        assert module.validate() == []
        assert module.name != spec.top_name
        assert (module.reset.signal, module.reset.kind, module.reset.active_high) == ("rst", "sync", True)
        assert module.latency_known is True and module.clock_domains == ["clk"]
        assert 2 <= len(module.examples) <= 3
        assert all(1 <= example.after_cycles <= 2000 for example in module.examples)
        assert validate_examples(module, require_anchors=True) == []


@pytest.mark.parametrize("name", ENTRIES)
def test_testbench_is_independent_self_checking_and_bounded(name):
    _, _, spec, tb, *_ = load(name)
    assert tb.startswith("`timescale 1ns/1ps")
    assert re.search(rf"(?m)^\s*{spec.top_name}\s+(?:#\(.*?\)\s*)?\w+\s*\(", tb)
    assert re.search(rf"(?m)^module\s+{spec.top_name}_tb\b", tb)
    assert '$display("TEST PASSED")' in tb
    assert re.search(r'\$display\("TEST FAILED: %0d errors"', tb)
    assert re.search(r"initial\s+begin\s*#\d+;\s*\$display\(\"TEST FAILED: watchdog timeout\"\);\s*\$finish;", tb)
    assert re.search(r'\$display\("FAIL BEHAVIOR', tb)
    assert not re.search(r"\bdut\s*\.\s*\w", tb), "testbench must not read DUT internals"
    assert not re.search(r"\$(?:readmem|fopen|system)", tb)
    # Only the top's own name may be renamed when the harness adapts the TB.
    for module in spec.modules:
        assert not re.search(rf"\b{module.name}_tb\b", tb)


@pytest.mark.parametrize("name", ENTRIES)
def test_reference_matches_contract_and_mechanical_top(name):
    _, _, spec, _, reference, _ = load(name)
    assert top_verilog(spec) in reference
    for module in spec.modules:
        result = check(reference, module)
        assert result.passed, result.errors
        assert module_declared_latency(reference, module.name) == module.latency


@pytest.mark.parametrize("name", ENTRIES)
def test_mutants_apply_cleanly_and_are_distinct(name):
    _, _, _, _, reference, mutants = load(name)
    assert 6 <= len(mutants) <= 10
    names = [mutant["name"] for mutant in mutants]
    assert len(names) == len(set(names))
    sources = {reference}
    for mutant in mutants:
        assert set(mutant) == {"name", "why", "find", "replace"}
        assert mutant["why"].strip() and mutant["find"] != mutant["replace"]
        assert reference.count(mutant["find"]) == 1, mutant["name"]
        sources.add(reference.replace(mutant["find"], mutant["replace"]))
    assert len(sources) == len(mutants) + 1


@pytest.mark.parametrize("name", ENTRIES)
def test_qualifier_builds_cases_without_launching_tools(name):
    module = qualifier()
    tb, top, cases = module.load_entry(TIER4 / name)
    _, meta, spec, *_ = load(name)
    assert tb == (TIER4 / name / meta["tb"]).resolve() and top == spec.top_name + "_tb"
    assert cases[0]["name"] == "reference" and cases[0]["expect_pass"]
    assert all(not case["expect_pass"] for case in cases[1:])


def test_qualifier_requires_raw_assertion_not_watchdog():
    judge = qualifier().judge
    assert judge("COVERAGE x\nTEST PASSED\n") == ("TEST PASSED", True, False)
    assert judge("FAIL BEHAVIOR rule=x\nTEST FAILED: 3 errors\n")[2] is True
    assert judge("TEST FAILED: watchdog timeout\n")[2] is False
    assert judge("FAIL BEHAVIOR rule=x\nTEST FAILED: watchdog timeout\n")[2] is False
    assert judge("ERROR: [VRFC 10-2989]\n")[0].startswith("NO VERDICT")


# Hand-written test-only oracles: they confirm the examples follow the stated
# semantics. They are never configured as generated goldens.
CRC_ORACLE = '''def init():
    return 0xFFFF
def update(state, value):
    state = state ^ (value << 8)
    for bit in range(8):
        state = ((state << 1) ^ 0x1021) & 0xFFFF if state & 0x8000 else (state << 1) & 0xFFFF
    return state
def step(state, inputs):
    if inputs.get("rst", 0):
        return init(), {"out_crc": 0, "out_last": 0}
    crc = update(state, inputs["in_data"])
    last = inputs.get("in_last", 0)
    return (0xFFFF if last else crc), {"out_crc": crc, "out_last": last}
'''
SPI_ORACLE = '''def init():
    return 0
def step(state, inputs):
    if inputs.get("rst", 0):
        return init(), {"rsp_data": 0, "sclk": 0, "mosi": 0, "cs_n": 1}
    received = 255 if inputs.get("miso", 0) else 0
    return state, {"rsp_data": received, "sclk": 0, "mosi": 0, "cs_n": 1}
'''
ARBITER_ORACLE = '''def init():
    return 3
def step(state, inputs):
    if inputs.get("rst", 0):
        return init(), {"grant": 0, "wr_en": 0, "wr_addr": 0, "wr_data": 0}
    request = inputs.get("req", 0)
    addresses = [inputs.get("addr0", 0), inputs.get("addr1", 0), inputs.get("addr2", 0), inputs.get("addr3", 0)]
    payloads = [inputs.get("data0", 0), inputs.get("data1", 0), inputs.get("data2", 0), inputs.get("data3", 0)]
    for offset in range(1, 5):
        index = (state + offset) % 4
        if request >> index & 1:
            return index, {"grant": 1 << index, "wr_en": 1,
                           "wr_addr": addresses[index], "wr_data": payloads[index]}
    return state, {"grant": 0, "wr_en": 0, "wr_addr": 0, "wr_data": 0}
'''
REGFILE_ORACLE = '''def init():
    return [0] * 8
def step(state, inputs):
    if inputs.get("rst", 0):
        return init(), {"rd_data": 0}
    memory = list(state)
    data = memory[inputs.get("rd_addr", 0)]
    if inputs.get("wr_en", 0):
        memory[inputs.get("wr_addr", 0)] = inputs.get("wr_data", 0)
    return memory, {"rd_data": data}
'''
ORACLES = {"crc16_stream_core": CRC_ORACLE, "spi_master_core": SPI_ORACLE,
           "rr_arbiter4": ARBITER_ORACLE, "regfile8x8": REGFILE_ORACLE}


def oracle(tmp_path, module_name):
    path = tmp_path / f"{module_name}_test_oracle.py"
    path.write_text(ORACLES[module_name], encoding="utf-8")
    model = GoldenModel(path)
    model.work_parent = tmp_path
    return model


@pytest.mark.parametrize("name", ENTRIES)
def test_examples_agree_with_test_only_oracles(name, tmp_path):
    _, _, spec, *_ = load(name)
    for module in spec.modules:
        assert qualify_against_examples(oracle(tmp_path, module.name), module) == []


def test_crc_oracle_reproduces_published_check_value(tmp_path):
    model = oracle(tmp_path, "crc16_stream_core")
    rows = [{"rst": 0, "in_valid": 1, "out_ready": 1, "in_data": 0x31 + i, "in_last": int(i == 8)}
            for i in range(9)]
    outputs = model.run(rows + rows)
    assert outputs[8] == {"out_crc": 0x29B1, "out_last": 1}
    assert outputs[17] == {"out_crc": 0x29B1, "out_last": 1}
