"""tier3 uart_fifo_build: prose spec with a fixed top, trusted testbench and qualification.

No Vivado, simulator or model call. The xsim qualification itself is recorded in
qualification/qualification.json (curriculum/tier4/qualify_tier4.py); these
tests check the static invariants and bind that record to the current files.
"""
import hashlib
import importlib.util
import json
import re
from pathlib import Path

import pytest
import yaml

from autortl.config import RunConfig
from autortl.linter import lint_spec, top_verilog
from autortl.spec import DesignSpec
from autortl.static_checks import check
from curriculum import runner

ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "curriculum" / "tier3" / "uart_fifo_build"
TOP_PORTS = {"clk": ("input", 1), "rst": ("input", 1), "in_data": ("input", 8),
             "in_valid": ("input", 1), "in_ready": ("output", 1), "tx": ("output", 1)}
TX_PORTS = {"clk": ("input", 1), "rst": ("input", 1), "tx_data": ("input", 8),
            "tx_valid": ("input", 1), "tx_ready": ("output", 1), "tx": ("output", 1)}


def text(name):
    return (ENTRY / name).read_text(encoding="utf-8")


def lf_bytes(path):
    return path.read_bytes().replace(b"\r\n", b"\n")


def meta():
    return yaml.safe_load(text("meta.yaml"))


def mutants():
    return json.loads(text("qualification/mutants.json"))


def qualifier():
    loader = importlib.util.spec_from_file_location("qualify_tier4", ROOT / "curriculum/tier4/qualify_tier4.py")
    module = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(module)
    return module


def spec_port_table():
    rows = re.findall(r"(?m)^\| `(\w+)` \| (input|output) \| (\d+) \|", text("spec.md"))
    return {name: (direction, int(width)) for name, direction, width in rows}


def test_metadata_names_top_and_trusted_testbench():
    data = meta()
    assert runner._metadata(ENTRY) == data
    assert data["mode"] == "build" and data["top"] == "uart_fifo" and data["spec"] == "spec.md"
    assert data["tb"] == "uart_fifo_tb.v" and data["generate_golden"] is False
    assert data["pass_criteria"] == {"timing_met": True}
    RunConfig(mode="build", top_module=data["top"], spec_path=ENTRY / data["spec"],
              testbench_path=ENTRY / data["tb"], objective=data["objective"],
              max_iterations=data["iterations"], generate_golden=data["generate_golden"]).validate()


def test_prose_spec_states_the_exact_interface():
    raw = text("spec.md")
    with pytest.raises((ValueError, KeyError, TypeError)):
        DesignSpec.from_json(raw)  # stays prose: the planner writes the typed spec
    assert "## Top module `uart_fifo` (exact name, no parameters)" in raw
    assert spec_port_table() == TOP_PORTS
    spec = " ".join(raw.split())
    assert "module uart_tx #(parameter CLKS_PER_BIT = 16)" in spec
    for name, (direction, width) in TX_PORTS.items():
        assert f"`{name}` ({direction} {width})" in spec
    for phrase in ("synchronous, active-high reset", "CLKS_PER_BIT = 16", "DEPTH = 8",
                   "every value from 2 to 255", "least significant bit first", "idle high",
                   "waiting < 8", "registered state only", "k+1", "no idle cycle"):
        assert phrase in spec, phrase
    assert "uart_fifo_tx" not in spec and "868" not in spec  # the old top name and divisor


def test_testbench_is_independent_self_checking_and_bounded():
    tb = text("uart_fifo_tb.v")
    assert tb.startswith("`timescale 1ns/1ps")
    assert re.search(r"(?m)^module\s+uart_fifo_tb\b", tb)
    top = re.search(r"(?m)^\s*uart_fifo\s+dut\s*\((.*?)\);", tb, re.S)
    assert top and set(re.findall(r"\.(\w+)\(", top.group(1))) == set(TOP_PORTS)
    child = re.search(r"(?m)^\s*uart_tx\s+#\(\.CLKS_PER_BIT\(CPB\)\)\s+dut\s*\((.*?)\);", tb, re.S)
    assert child and set(re.findall(r"\.(\w+)\(", child.group(1))) == set(TX_PORTS)
    assert '$display("TEST PASSED")' in tb
    assert re.search(r'\$display\("TEST FAILED: %0d errors"', tb)
    assert re.search(r"initial\s+begin\s*#\d+;\s*\$display\(\"TEST FAILED: watchdog timeout\"\);\s*\$finish;", tb)
    assert re.search(r'\$display\("FAIL BEHAVIOR', tb)
    assert not re.search(r"\bdut\s*\.\s*\w", tb), "testbench must not read DUT internals"
    assert not re.search(r"\$(?:readmem|fopen|system)", tb)
    assert not re.search(r"\b(?:uart_tx|sync_fifo)_tb\b", tb)
    cases = re.findall(r"uart_fifo_case #\(\.CPB\((\d+)\),\.USE_TOP\((\d)\)", tb)
    assert ("16", "1") in cases and {cpb for cpb, top in cases if top == "0"} == {"2", "3", "7"}


def test_reference_matches_mechanical_top_and_fixed_interfaces():
    reference = text("qualification/reference.v")
    spec = DesignSpec.load(ENTRY / "qualification" / "reference_spec.json")
    assert spec.top_name == meta()["top"] and lint_spec(spec) == []
    assert reference.endswith(top_verilog(spec))
    assert {p.name: (p.direction, p.width) for p in spec.external_ports} == TOP_PORTS
    tx = spec.module("uart_tx")
    assert {p.name: (p.direction, p.width) for p in tx.ports} == TX_PORTS
    assert tx.parameters == {"CLKS_PER_BIT": 16}
    assert len(spec.modules) == 2
    for module in spec.modules:
        assert module.validate() == []
        result = check(reference, module)
        assert result.passed, result.errors


def test_mutants_apply_cleanly_and_are_distinct():
    reference = text("qualification/reference.v")
    items = mutants()
    assert len(items) == 10
    assert len({m["name"] for m in items}) == len(items)
    sources = {reference}
    for mutant in items:
        assert set(mutant) == {"name", "why", "find", "replace"}
        assert mutant["why"].strip() and mutant["find"] != mutant["replace"]
        assert reference.count(mutant["find"]) == 1, mutant["name"]
        sources.add(reference.replace(mutant["find"], mutant["replace"]))
    assert len(sources) == len(items) + 1


def test_qualifier_builds_cases_without_launching_tools():
    tb, top, cases = qualifier().load_entry(ENTRY)
    assert tb == (ENTRY / "uart_fifo_tb.v").resolve() and top == "uart_fifo_tb"
    assert [case["name"] for case in cases] == ["reference"] + [m["name"] for m in mutants()]
    assert cases[0]["expect_pass"] and not any(case["expect_pass"] for case in cases[1:])


def test_recorded_qualification_binds_current_testbench_and_sources():
    record = json.loads(text("qualification/qualification.json"))
    _, _, cases = qualifier().load_entry(ENTRY)
    assert record["qualified"] is True and record["top"] == "uart_fifo_tb"
    assert record["testbench_sha256"] == hashlib.sha256(lf_bytes(ENTRY / "uart_fifo_tb.v")).hexdigest()
    assert [run["case"] for run in record["runs"]] == [case["name"] for case in cases]
    for run, case in zip(record["runs"], cases):
        source = case["source"].replace("\r\n", "\n").encode("utf-8")
        assert run["source_sha256"] == hashlib.sha256(source).hexdigest(), run["case"]
        assert run["as_required"] is True
        if case["expect_pass"]:
            assert run["verdict"] == "TEST PASSED"
        else:
            assert run["assertion_detected"] is True and run["verdict"].startswith("TEST FAILED: ")
    console = text("qualification/console.txt").splitlines()
    assert console[-1] == "QUALIFIED" and len(console) == len(cases) + 1
