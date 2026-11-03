"""Tier5 build fixtures: structure, typed specs, testbench shape and mutant targets.

No Vivado, simulator or model call. Passing this establishes static fixture
invariants only; testbench qualification needs curriculum/tier5/qualify_tier5.py.
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
from autortl.tbgen import generate as generate_tb
from autortl.verilog_interface import module_declared_latency
from curriculum import runner

TIER5 = Path(__file__).resolve().parents[1] / "curriculum" / "tier5"
ENTRIES = ["axil_regs_build", "fir16_sym_build", "uart_rx_fifo_build"]
REQUIRED_META = {"mode", "top", "spec", "tb", "iterations", "objective", "pass_criteria"}


def entry_dirs():
    return sorted(p for p in TIER5.iterdir() if p.is_dir() and p.name != "__pycache__")


def load(name):
    entry = TIER5 / name
    meta = yaml.safe_load((entry / "meta.yaml").read_text(encoding="utf-8"))
    spec = DesignSpec.load(entry / meta["spec"])
    tb = (entry / meta["tb"]).read_text(encoding="utf-8")
    reference = (entry / "qualification" / "reference.v").read_text(encoding="utf-8")
    mutants = json.loads((entry / "qualification" / "mutants.json").read_text(encoding="utf-8"))
    return entry, meta, spec, tb, reference, mutants


def qualifier():
    loader = importlib.util.spec_from_file_location("qualify_tier5", TIER5 / "qualify_tier5.py")
    module = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(module)
    return module


def test_tier5_contains_exactly_the_three_build_entries():
    assert [p.name for p in entry_dirs()] == ENTRIES


@pytest.mark.parametrize("name", ENTRIES)
def test_metadata_maps_to_a_valid_build_config(name):
    entry, meta, spec, *_ = load(name)
    assert REQUIRED_META <= set(meta)
    assert meta["mode"] == "build" and meta["objective"] == "minimize_luts"
    # fir16_sym_build needs eight: closing 150 MHz took four in fir16-ooc-02.
    assert meta["spec"] == "design_spec.json" and meta["iterations"] == (8 if meta["top"] == "fir16_sym" else 3)
    assert meta["pass_criteria"] == {"timing_met": True}
    assert type(meta.get("generate_golden", False)) is bool
    assert runner._metadata(entry) == meta
    config = RunConfig(mode="build", top_module=meta["top"], spec_path=entry / meta["spec"],
                       testbench_path=entry / meta["tb"], objective=meta["objective"],
                       max_iterations=meta["iterations"],
                       generate_golden=meta.get("generate_golden", False))
    config.validate()
    assert spec.top_name == meta["top"]


def test_fir_targets_150_mhz():
    _, meta, *_ = load("fir16_sym_build")
    assert meta["target_freq_mhz"] == 150.0


@pytest.mark.parametrize("name", ENTRIES)
def test_spec_lints_clean_with_bounded_constant_examples(name):
    _, _, spec, *_ = load(name)
    assert lint_spec(spec) == []
    assert DesignSpec.from_json(spec.to_json()).to_json() == spec.to_json()
    for module in spec.modules:
        assert module.validate() == []
        assert module.name != spec.top_name
        assert (module.reset.signal, module.reset.kind, module.reset.active_high) == ("rst", "sync", True)
        assert module.latency_known is True and module.clock_domains == ["clk"]
        assert 2 <= len(module.examples) <= 3
        for example in module.examples:
            assert 1 <= example.after_cycles <= 2000
            # One integer per port, held constant for after_cycles steps from reset.
            assert all(type(value) is int for value in example.inputs.values())
            assert all(type(value) is int for value in example.expected.values())
            assert example.inputs.get("rst") == 0
        assert validate_examples(module, require_anchors=True) == []


@pytest.mark.parametrize("name", ["axil_regs_build", "uart_rx_fifo_build"])
def test_multi_module_children_fit_the_generated_fixed_latency_path(name):
    # Every child of a multi-module build goes through the generated golden path.
    _, _, spec, *_ = load(name)
    assert len(spec.modules) == 3 and len(spec.connections) >= 4
    for module in spec.modules:
        assert module.compare_mode == "fixed_latency" and module.latency == 1
        assert all(port.protocol == "none" for port in module.ports)
    assert "// @latency" not in top_verilog(spec)


def test_fir_is_a_single_scoreboard_child():
    _, _, spec, *_ = load("fir16_sym_build")
    (module,) = spec.modules
    assert module.compare_mode == "scoreboard" and module.latency == 5
    controls = sorted((p.name, p.direction) for p in module.ports if p.protocol == "valid_ready")
    assert controls == [("in_ready", "output"), ("in_valid", "input"), ("out_ready", "input"), ("out_valid", "output")]
    assert "// @latency 5" in top_verilog(spec)


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


def test_uart_testbench_covers_non_default_parameters_through_the_children():
    *_, tb, _, _ = load("uart_rx_fifo_build")
    cases = re.findall(r"uart_rx_fifo_case #\(\.D\((\d+)\),\.A\((\d+)\)", tb)
    assert ("2", "2") in cases and len({d for d, _ in cases}) == 3 and len({a for _, a in cases}) == 3
    assert "uart_rx_core #(.OVERSAMPLE_DIV(D))" in tb and "rx_fifo #(.ADDR_BITS(A))" in tb


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
    _, _, spec, _, reference, mutants = load(name)
    assert len(mutants) == 10
    names = [mutant["name"] for mutant in mutants]
    assert len(names) == len(set(names))
    sources = {reference}
    for mutant in mutants:
        assert set(mutant) == {"name", "why", "find", "replace"}
        assert mutant["why"].strip() and mutant["find"] != mutant["replace"]
        assert reference.count(mutant["find"]) == 1, mutant["name"]
        mutated = reference.replace(mutant["find"], mutant["replace"])
        sources.add(mutated)
        # A mutant keeps every contract interface: it is a behavioral fault only.
        for module in spec.modules:
            assert not [error for error in check(mutated, module).errors if "interface" in error or "port" in error]
    assert len(sources) == len(mutants) + 1


@pytest.mark.parametrize("name", ENTRIES)
def test_qualifier_builds_cases_without_launching_tools(name):
    module = qualifier()
    tb, top, cases = module.load_entry(TIER5 / name)
    _, meta, spec, *_ = load(name)
    assert tb == (TIER5 / name / meta["tb"]).resolve() and top == spec.top_name + "_tb"
    assert cases[0]["name"] == "reference" and cases[0]["expect_pass"]
    assert len(cases) == 11 and all(not case["expect_pass"] for case in cases[1:])


def test_qualifier_requires_raw_assertion_not_watchdog():
    judge = qualifier().judge
    assert judge("COVERAGE x\nTEST PASSED\n") == ("TEST PASSED", True, False)
    assert judge("FAIL BEHAVIOR rule=x\nTEST FAILED: 3 errors\n")[2] is True
    assert judge("TEST FAILED: watchdog timeout\n")[2] is False
    assert judge("FAIL BEHAVIOR rule=x\nTEST FAILED: watchdog timeout\n")[2] is False
    assert judge("ERROR: [VRFC 10-2989]\n")[0].startswith("NO VERDICT")


# Hand-written test-only oracles: they confirm the examples follow the stated
# semantics and that each child fits the generated testbench path. They are
# never configured as generated goldens.
UART_ORACLE = '''def init():
    return {"sync1": 1, "sync2": 1, "mode": 0, "offset": 0, "votes": [0, 0, 0], "bits": 0, "data": 0}
def step(state, inputs):
    if inputs.get("rst", 0):
        return init(), {"rx_data": 0, "rx_strobe": 0, "frame_err": 0}
    d = 2
    s = dict(state)
    line = state["sync2"]
    strobe = 0
    ferr = 0
    if state["mode"] == 0:
        if line == 0:
            s["mode"] = 1
            s["offset"] = 0
    elif state["mode"] == 2:
        if line == 1:
            s["mode"] = 0
    else:
        offset = state["offset"] + 1
        s["offset"] = offset
        bit = offset // (16 * d)
        phase = offset % (16 * d)
        votes = list(state["votes"])
        if phase == 7 * d:
            votes[0] = line
        if phase == 8 * d:
            votes[1] = line
        if phase == 9 * d:
            votes[2] = line
            value = 1 if votes[0] + votes[1] + votes[2] >= 2 else 0
            if bit == 0:
                if value:
                    s["mode"] = 0
            elif bit <= 8:
                s["bits"] = state["bits"] | (value << (bit - 1))
            else:
                if value:
                    s["data"] = state["bits"]
                    strobe = 1
                    s["mode"] = 0
                else:
                    ferr = 1
                    s["mode"] = 2
                s["bits"] = 0
        s["votes"] = votes
    s["sync2"] = state["sync1"]
    s["sync1"] = inputs.get("rx", 0)
    return s, {"rx_data": s["data"], "rx_strobe": strobe, "frame_err": ferr}
'''
FIFO_ORACLE = '''def init():
    return []
def step(state, inputs):
    if inputs.get("rst", 0):
        return init(), {"out_data": 0, "out_valid": 0, "overflow": 0}
    queue = list(state)
    pop = inputs.get("out_ready", 0) and len(queue) > 0
    push = inputs.get("wr_en", 0) and (len(queue) < 4 or pop)
    if pop:
        queue.pop(0)
    if push:
        queue.append(inputs.get("wr_data", 0))
    overflow = 1 if inputs.get("wr_en", 0) and not push else 0
    head = queue[0] if queue else 0
    return queue, {"out_data": head, "out_valid": 1 if queue else 0, "overflow": overflow}
'''
COUNT_ORACLE = '''def init():
    return (0, 0)
def step(state, inputs):
    if inputs.get("rst", 0):
        return init(), {"ferr_count": 0, "ovf_count": 0}
    ferr = state[0]
    ovf = state[1]
    if inputs.get("ferr_in", 0) and ferr < 15:
        ferr = ferr + 1
    if inputs.get("ovf_in", 0) and ovf < 15:
        ovf = ovf + 1
    return (ferr, ovf), {"ferr_count": ferr, "ovf_count": ovf}
'''
FIR_ORACLE = '''COEFFS = [-6, -20, -24, 18, 110, 226, 330, 390, 390, 330, 226, 110, 18, -24, -20, -6]
def init():
    return [0] * 15
def step(state, inputs):
    if inputs.get("rst", 0):
        return init(), {"out_sample": 0}
    sample = inputs.get("in_sample", 0)
    if sample >= 32768:
        sample = sample - 65536
    window = [sample] + list(state)
    acc = 0
    for k in range(16):
        acc = acc + COEFFS[k] * window[k]
    r = (acc + 1024) >> 11
    if r > 32767:
        r = 32767
    if r < -32768:
        r = -32768
    return window[0:15], {"out_sample": r & 65535}
'''
WR_ORACLE = '''def init():
    return {"awf": 0, "addr": 0, "wf": 0, "data": 0, "strb": 0, "bvalid": 0, "bresp": 0}
def view(s):
    write = s["awf"] and s["wf"] and not s["bvalid"]
    return {"awready": 1 - s["awf"], "wready": 1 - s["wf"], "bvalid": s["bvalid"], "bresp": s["bresp"],
            "wr_en": 1 if write and not (s["addr"] >> 5) & 1 else 0, "wr_idx": (s["addr"] >> 2) & 7,
            "wr_data": s["data"], "wr_strb": s["strb"]}
def step(state, inputs):
    if inputs.get("rst", 0):
        return init(), view(init())
    s = dict(state)
    if state["awf"] and state["wf"] and not state["bvalid"]:
        s["awf"] = 0
        s["wf"] = 0
        s["bvalid"] = 1
        s["bresp"] = 2 if (state["addr"] >> 5) & 1 else 0
    elif state["bvalid"] and inputs.get("bready", 0):
        s["bvalid"] = 0
    if inputs.get("awvalid", 0) and not state["awf"]:
        s["awf"] = 1
        s["addr"] = inputs.get("awaddr", 0)
    if inputs.get("wvalid", 0) and not state["wf"]:
        s["wf"] = 1
        s["data"] = inputs.get("wdata", 0)
        s["strb"] = inputs.get("wstrb", 0)
    return s, view(s)
'''
BANK_ORACLE = '''ID = 1381256245
def init():
    return [0, 0, 256, 0, 0, 0, ID, 0]
def view(regs):
    flat = 0
    for i in range(8):
        flat = flat | (regs[i] << (32 * i))
    return {"regs_flat": flat, "ctrl": regs[0], "irq": 1 if regs[3] & regs[4] & 255 else 0}
def merge(old, new, strobe):
    out = 0
    for lane in range(4):
        source = new if (strobe >> lane) & 1 else old
        out = out | (source & (255 << (8 * lane)))
    return out
def step(state, inputs):
    if inputs.get("rst", 0):
        return init(), view(init())
    regs = list(state)
    en = inputs.get("wr_en", 0)
    idx = inputs.get("wr_idx", 0)
    data = inputs.get("wr_data", 0)
    strobe = inputs.get("wr_strb", 0)
    clear = data & 255 if en and idx == 4 and strobe & 1 else 0
    regs[5] = inputs.get("status_in", 0)
    regs[4] = (state[4] & (255 ^ clear)) | inputs.get("irq_set", 0)
    if en:
        regs[7] = (state[7] + 1) & 4294967295
        if idx <= 2:
            regs[idx] = merge(state[idx], data, strobe)
        if idx == 3 and strobe & 1:
            regs[3] = data & 255
    return regs, view(regs)
'''
RD_ORACLE = '''def init():
    return (0, 0, 0)
def view(s):
    return {"arready": 1 - s[0], "rvalid": s[0], "rdata": s[1], "rresp": s[2]}
def step(state, inputs):
    if inputs.get("rst", 0):
        return init(), view(init())
    s = state
    if inputs.get("arvalid", 0) and not state[0]:
        addr = inputs.get("araddr", 0)
        if (addr >> 5) & 1:
            s = (1, 0, 2)
        else:
            s = (1, (inputs.get("regs_flat", 0) >> (32 * ((addr >> 2) & 7))) & 4294967295, 0)
    elif state[0] and inputs.get("rready", 0):
        s = (0, state[1], state[2])
    return s, view(s)
'''
ORACLES = {"uart_rx_core": UART_ORACLE, "rx_fifo": FIFO_ORACLE, "rx_err_count": COUNT_ORACLE,
           "fir16_sym_core": FIR_ORACLE, "axil_wr_if": WR_ORACLE, "axil_regbank": BANK_ORACLE,
           "axil_rd_if": RD_ORACLE}


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


@pytest.mark.parametrize("name", ENTRIES)
def test_every_child_fits_the_generated_testbench_path(name, tmp_path):
    _, _, spec, *_ = load(name)
    for module in spec.modules:
        path = generate_tb(module, oracle(tmp_path, module.name), tmp_path / module.name, n_random=20)
        text = path.read_text(encoding="utf-8")
        assert re.search(rf"(?m)^module {module.name}_tb;", text) and "TEST PASSED" in text


def test_fir_oracle_rounds_ties_up_and_saturates(tmp_path):
    model = oracle(tmp_path, "fir16_sym_core")
    rows = [{"rst": 0, "in_valid": 1, "out_ready": 1, "in_sample": value}
            for value in [512] + [0] * 15 + [32767] * 13]
    outputs = [row["out_sample"] for row in model.run(rows)]
    # 512 * h[k] for even h is an exact tie: -3072 -> -1.5 rounds up to -1.
    assert outputs[0] == 65535 and outputs[3] == 5  # 512*18 = 9216 -> 4.5 -> 5
    assert outputs[-1] == 32767  # 32767 * 2098 saturates


def test_uart_oracle_receives_a_frame_at_the_specified_edge(tmp_path):
    model = oracle(tmp_path, "uart_rx_core")
    value, d = 0xA5, 2
    line = [1] * 4 + [0] * (16 * d)
    for bit in range(8):
        line += [(value >> bit) & 1] * (16 * d)
    line += [1] * (16 * d + 8)
    outputs = model.run([{"rst": 0, "rx": bit} for bit in line])
    strobes = [index for index, row in enumerate(outputs) if row["rx_strobe"]]
    # rx first low before edge 5 (index 4), detected at edge 7, stop decided at 7 + 153*D.
    assert strobes == [6 + 153 * d] and outputs[strobes[0]]["rx_data"] == value
