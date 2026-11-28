"""Tier6 build fixtures: structure, typed specs, testbench shape and mutant targets.

No Vivado, simulator or model call. Passing this establishes static fixture
invariants only; testbench qualification needs curriculum/tier6/qualify_tier6.py
(its recorded results are in each entry's qualification/ folder).
"""
import importlib.util
import json
import math
import re
from pathlib import Path

import pytest
import yaml

from autortl.config import RunConfig
from autortl.golden import GoldenModel, qualify_against_examples, validate_examples
from autortl.linter import lint_spec, top_verilog
from autortl.spec import DesignSpec
from autortl.static_checks import check
from autortl.tbgen import generate as generate_tb, shape_errors
from autortl.verilog_interface import module_declared_latency
from curriculum import runner

TIER6 = Path(__file__).resolve().parents[1] / "curriculum" / "tier6"
ENTRIES = ["aes128_core_build", "cordic_build", "rv32i_core_build"]
REQUIRED_META = {"mode", "top", "spec", "tb", "iterations", "objective", "pass_criteria"}
CHIP_IO = 106  # user I/O of xc7a35tcpg236-1


def entry_dirs():
    return sorted(p for p in TIER6.iterdir() if p.is_dir() and p.name != "__pycache__")


def load(name):
    entry = TIER6 / name
    meta = yaml.safe_load((entry / "meta.yaml").read_text(encoding="utf-8"))
    spec = DesignSpec.load(entry / meta["spec"])
    tb = (entry / meta["tb"]).read_text(encoding="utf-8")
    reference = (entry / "qualification" / "reference.v").read_text(encoding="utf-8")
    mutants = json.loads((entry / "qualification" / "mutants.json").read_text(encoding="utf-8"))
    return entry, meta, spec, tb, reference, mutants


def qualifier():
    loader = importlib.util.spec_from_file_location("qualify_tier6", TIER6 / "qualify_tier6.py")
    module = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(module)
    return module


def port_names(module):
    return {port.name for port in module.ports}


def test_tier6_contains_exactly_the_three_build_entries():
    assert [p.name for p in entry_dirs()] == ENTRIES


@pytest.mark.parametrize("name", ENTRIES)
def test_metadata_maps_to_a_valid_build_config(name):
    entry, meta, spec, *_ = load(name)
    assert REQUIRED_META <= set(meta)
    assert meta["mode"] == "build" and meta["objective"] == "minimize_luts"
    assert meta["spec"] == "design_spec.json" and meta["iterations"] == 4
    assert meta["pass_criteria"] == {"timing_met": True}
    assert meta["generate_golden"] is True and meta["target_freq_mhz"] == 100.0
    assert runner._metadata(entry) == meta
    config = RunConfig(mode="build", top_module=meta["top"], spec_path=entry / meta["spec"],
                       testbench_path=entry / meta["tb"], objective=meta["objective"],
                       max_iterations=meta["iterations"],
                       generate_golden=meta.get("generate_golden", False),
                       implementation=meta.get("implementation", "chip_top"))
    config.validate()
    assert spec.top_name == meta["top"]


@pytest.mark.parametrize("name", ENTRIES)
def test_out_of_context_exactly_when_ports_exceed_the_package(name):
    # chip_top_flow_for_soc_block: a top wider than the 106 user I/O is an SoC block.
    _, meta, spec, *_ = load(name)
    bits = sum(port.width for port in spec.external_ports)
    assert (meta.get("implementation", "chip_top") == "out_of_context") == (bits > CHIP_IO)
    assert bits == {"aes128_core_build": 390, "cordic_build": 54, "rv32i_core_build": 151}[name]


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
            if module.latency:
                assert example.inputs.get("rst") == 0
            else:
                assert example.after_cycles == 1
        assert validate_examples(module, require_anchors=True) == []


@pytest.mark.parametrize("name", ENTRIES)
def test_every_child_fits_the_generated_fixed_latency_path(name):
    # Every child of a multi-module build goes through the generated golden path:
    # cycle-level sequential children with clk/rst, or combinational children without.
    _, _, spec, *_ = load(name)
    assert len(spec.modules) >= 3 and len(spec.connections) >= 6
    for module in spec.modules:
        assert shape_errors(module) == []
        assert module.compare_mode == "fixed_latency" and module.latency in (0, 1)
        assert all(port.protocol == "none" and port.signed is False for port in module.ports)
        assert ({"clk", "rst"} <= port_names(module)) == (module.latency == 1)
        assert not ({"clk", "rst"} & port_names(module)) or module.latency == 1
    assert "// @latency" not in top_verilog(spec)


def test_decompositions():
    shapes = {name: sorted((m.name, m.latency) for m in load(name)[2].modules) for name in ENTRIES}
    assert shapes["rv32i_core_build"] == [("rv_alu", 0), ("rv_ctrl", 1), ("rv_decode", 0), ("rv_dmem", 1),
                                          ("rv_imem", 1), ("rv_regfile", 1)]
    assert shapes["aes128_core_build"] == [("aes_ctrl", 1), ("aes_key_step", 0), ("aes_round", 0)]
    assert shapes["cordic_build"] == [("cordic_atan", 0), ("cordic_engine", 1), ("cordic_out", 0),
                                      ("cordic_prerot", 0)]


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
        assert not re.search(rf"\b{module.name}\b", tb)


def test_aes_testbench_carries_the_fips_and_aesavs_answers():
    *_, tb, _, _ = load("aes128_core_build")
    for ciphertext in ("69c4e0d86a7b0430d8cdb78070b4c55a", "3925841d02dc09fbdc118597196a0b32",
                       "0336763e966d92595a567cc9ce537f5e", "6d251e6944b051e04eaa6fb4dbf78465",
                       "3ad78e726c1ec02b7ebfe92b23d9ec34", "0edd33d3c621e546455bd8ba1418bec8"):
        assert "128'h" + ciphertext in tb
    # The S-box is computed from the field inverse, not copied from the design.
    assert "task build_sbox" in tb and len(re.findall(r"(?<![0-9])8'h[0-9a-f]{2}\b", tb)) < 30


@pytest.mark.parametrize("name", ENTRIES)
def test_reference_matches_contract_and_mechanical_top(name):
    _, _, spec, _, reference, _ = load(name)
    assert reference.endswith(top_verilog(spec))
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
def test_recorded_qualification_matches_the_fixture(name):
    entry, meta, _, _, reference, mutants = load(name)
    record = json.loads((entry / "qualification" / "qualification.json").read_text(encoding="utf-8"))
    assert record["qualified"] is True and record["top"] == meta["top"] + "_tb"
    runs = record["runs"]
    assert [run["case"] for run in runs] == ["reference"] + [mutant["name"] for mutant in mutants]
    assert runs[0]["verdict"] == "TEST PASSED" and runs[0]["as_required"]
    for run in runs[1:]:
        assert run["as_required"] and run["assertion_detected"] and run["verdict"].startswith("TEST FAILED: ")
    console = (entry / "qualification" / "console.txt").read_text(encoding="utf-8")
    assert console.strip().endswith("QUALIFIED") and "NOT QUALIFIED" not in console


@pytest.mark.parametrize("name", ENTRIES)
def test_qualifier_builds_cases_without_launching_tools(name):
    module = qualifier()
    tb, top, cases = module.load_entry(TIER6 / name)
    _, meta, spec, *_ = load(name)
    assert tb == (TIER6 / name / meta["tb"]).resolve() and top == spec.top_name + "_tb"
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
IMEM_ORACLE = '''def init():
    return {"mem": [0] * 64, "rdata": 0}
def step(state, inputs):
    if inputs.get("rst", 0):
        return init(), {"imem_rdata": 0}
    mem = state["mem"]
    rdata = mem[inputs.get("imem_raddr", 0)]
    if inputs.get("imem_we", 0):
        mem[inputs.get("imem_waddr", 0)] = inputs.get("imem_wdata", 0)
    return {"mem": mem, "rdata": rdata}, {"imem_rdata": rdata}
'''
DECODE_ORACLE = '''def init():
    return 0
def sext(value, bits):
    value = value & ((1 << bits) - 1)
    if value >> (bits - 1):
        value = value - (1 << bits)
    return value & 4294967295
def step(state, inputs):
    i = inputs.get("instr", 0)
    opcode = i & 127
    f3 = (i >> 12) & 7
    b30 = (i >> 30) & 1
    imm_i = sext(i >> 20, 12)
    imm_s = sext(((i >> 25) << 5) | ((i >> 7) & 31), 12)
    imm_b = sext((((i >> 31) & 1) << 12) | (((i >> 7) & 1) << 11) | (((i >> 25) & 63) << 5) | (((i >> 8) & 15) << 1), 13)
    imm_u = i & 4294963200
    imm_j = sext((((i >> 31) & 1) << 20) | (((i >> 12) & 255) << 12) | (((i >> 20) & 1) << 11) | (((i >> 21) & 1023) << 1), 21)
    kind = 6
    a_sel = 0
    b_sel = 0
    op = 0
    imm = 0
    if opcode == 51:
        kind = 0
        op = (b30 << 3) | f3
    elif opcode == 19:
        kind = 0
        b_sel = 1
        imm = imm_i
        op = f3
        if f3 == 5:
            op = (b30 << 3) | f3
    elif opcode == 55:
        kind = 0
        a_sel = 2
        b_sel = 1
        imm = imm_u
    elif opcode == 23:
        kind = 0
        a_sel = 1
        b_sel = 1
        imm = imm_u
    elif opcode == 111:
        kind = 4
        a_sel = 1
        b_sel = 1
        imm = imm_j
    elif opcode == 103:
        kind = 5
        b_sel = 1
        imm = imm_i
    elif opcode == 99:
        kind = 3
        a_sel = 1
        b_sel = 1
        imm = imm_b
    elif opcode == 3:
        kind = 1
        b_sel = 1
        imm = imm_i
    elif opcode == 35:
        kind = 2
        b_sel = 1
        imm = imm_s
    return 0, {"rs1": (i >> 15) & 31, "rs2": (i >> 20) & 31, "rd": (i >> 7) & 31, "imm": imm,
               "alu_op": op, "a_sel": a_sel, "b_sel": b_sel, "kind": kind, "funct3": f3}
'''
REGFILE_ORACLE = '''def init():
    return {"regs": [0] * 32, "r1": 0, "r2": 0}
def step(state, inputs):
    if inputs.get("rst", 0):
        return init(), {"rdata1": 0, "rdata2": 0}
    regs = state["regs"]
    r1 = regs[inputs.get("raddr1", 0)]
    r2 = regs[inputs.get("raddr2", 0)]
    w = inputs.get("waddr", 0)
    if inputs.get("we", 0) and w != 0:
        regs[w] = inputs.get("wdata", 0)
    return {"regs": regs, "r1": r1, "r2": r2}, {"rdata1": r1, "rdata2": r2}
'''
ALU_ORACLE = '''M = 4294967295
def init():
    return 0
def signed(v):
    return v - 4294967296 if v >> 31 else v
def step(state, inputs):
    r1 = inputs.get("rs1_val", 0)
    r2 = inputs.get("rs2_val", 0)
    s = inputs.get("a_sel", 0)
    a = r1 if s == 0 else (inputs.get("pc_val", 0) if s == 1 else 0)
    b = inputs.get("imm", 0) if inputs.get("b_sel", 0) else r2
    op = inputs.get("op", 0)
    f = op & 7
    alt = (op >> 3) & 1
    sh = b & 31
    if f == 0:
        y = (a - b) & M if alt else (a + b) & M
    elif f == 1:
        y = (a << sh) & M
    elif f == 2:
        y = 1 if signed(a) < signed(b) else 0
    elif f == 3:
        y = 1 if a < b else 0
    elif f == 4:
        y = a ^ b
    elif f == 5:
        y = (signed(a) >> sh) & M if alt else a >> sh
    elif f == 6:
        y = a | b
    else:
        y = a & b
    return 0, {"y": y, "eq": 1 if r1 == r2 else 0, "lt": 1 if signed(r1) < signed(r2) else 0,
               "ltu": 1 if r1 < r2 else 0}
'''
DMEM_ORACLE = '''def init():
    return {"mem": [0] * 32, "rdata": 0}
def step(state, inputs):
    if inputs.get("rst", 0):
        return init(), {"rdata": 0}
    mem = state["mem"]
    a = inputs.get("addr", 0)
    rdata = mem[a]
    if inputs.get("we", 0):
        mem[a] = inputs.get("wdata", 0)
    return {"mem": mem, "rdata": rdata}, {"rdata": rdata}
'''
CTRL_ORACLE = '''M = 4294967295
def init():
    return {"st": 0, "pc": 0, "npc": 0, "res": 0, "sdata": 0, "rd": 0, "wb": 0, "store": 0, "load": 0}
def view(s):
    w = 1 if s["st"] == 5 else 0
    return {"pc": s["pc"], "imem_raddr": (s["pc"] >> 2) & 63, "retire": w, "rf_we": w & s["wb"],
            "rf_waddr": s["rd"], "rf_wdata": s["res"], "dmem_we": (1 if s["st"] == 3 else 0) & s["store"],
            "dmem_addr": (s["res"] >> 2) & 31, "dmem_wdata": s["sdata"]}
def step(state, inputs):
    if inputs.get("rst", 0):
        return init(), view(init())
    s = dict(state)
    st = state["st"]
    kind = inputs.get("kind", 0)
    if st == 0:
        if inputs.get("run", 0):
            s["st"] = 1
    elif st == 1:
        s["st"] = 2
    elif st == 2:
        y = inputs.get("y", 0)
        f3 = inputs.get("funct3", 0)
        eq = inputs.get("eq", 0)
        lt = inputs.get("lt", 0)
        ltu = inputs.get("ltu", 0)
        link = (state["pc"] + 4) & M
        s["wb"] = 1 if kind in (0, 1, 4, 5) else 0
        s["store"] = 1 if kind == 2 else 0
        s["load"] = 1 if kind == 1 else 0
        s["rd"] = inputs.get("rd", 0)
        s["sdata"] = inputs.get("rs2_val", 0)
        s["res"] = link if kind in (4, 5) else y
        cond = [eq, 1 - eq, 0, 0, lt, 1 - lt, ltu, 1 - ltu][f3]
        if kind == 4 or (kind == 3 and cond):
            s["npc"] = y
        elif kind == 5:
            s["npc"] = y & 4294967294
        else:
            s["npc"] = link
        s["st"] = 3 if kind in (1, 2) else 5
    elif st == 3:
        s["st"] = 4 if state["load"] else 5
    elif st == 4:
        s["res"] = inputs.get("dmem_rdata", 0)
        s["st"] = 5
    elif st == 5:
        s["pc"] = state["npc"]
        s["st"] = 0
    else:
        s["st"] = 0
    return s, view(s)
'''
AES_CTRL_ORACLE = '''RCON = [1, 2, 4, 8, 16, 32, 64, 128, 27, 54, 0, 0, 0, 0, 0, 0]
def init():
    return {"busy": 0, "ov": 0, "rnd": 0, "st": 0, "rk": 0}
def view(s):
    return {"in_ready": 1 if not s["busy"] and not s["ov"] else 0, "out_valid": s["ov"], "ct": s["st"],
            "rk": s["rk"], "rcon": RCON[s["rnd"]], "last": 1 if s["rnd"] == 10 else 0}
def step(state, inputs):
    if inputs.get("rst", 0):
        return init(), view(init())
    s = dict(state)
    if state["busy"]:
        s["rk"] = inputs.get("key_next", 0)
        if state["rnd"] == 0:
            s["rnd"] = 1
        else:
            s["st"] = inputs.get("round_out", 0)
            if state["rnd"] == 10:
                s["busy"] = 0
                s["ov"] = 1
                s["rnd"] = 0
            else:
                s["rnd"] = state["rnd"] + 1
    elif state["ov"]:
        if inputs.get("out_ready", 0):
            s["ov"] = 0
    elif inputs.get("in_valid", 0):
        s["st"] = inputs.get("pt", 0) ^ inputs.get("key", 0)
        s["rk"] = inputs.get("key", 0)
        s["rnd"] = 0
        s["busy"] = 1
    return s, view(s)
'''
AES_ROUND_ORACLE = '''SBOX = [99, 124, 119, 123, 242, 107, 111, 197, 48, 1, 103, 43, 254, 215, 171, 118,
        202, 130, 201, 125, 250, 89, 71, 240, 173, 212, 162, 175, 156, 164, 114, 192,
        183, 253, 147, 38, 54, 63, 247, 204, 52, 165, 229, 241, 113, 216, 49, 21,
        4, 199, 35, 195, 24, 150, 5, 154, 7, 18, 128, 226, 235, 39, 178, 117,
        9, 131, 44, 26, 27, 110, 90, 160, 82, 59, 214, 179, 41, 227, 47, 132,
        83, 209, 0, 237, 32, 252, 177, 91, 106, 203, 190, 57, 74, 76, 88, 207,
        208, 239, 170, 251, 67, 77, 51, 133, 69, 249, 2, 127, 80, 60, 159, 168,
        81, 163, 64, 143, 146, 157, 56, 245, 188, 182, 218, 33, 16, 255, 243, 210,
        205, 12, 19, 236, 95, 151, 68, 23, 196, 167, 126, 61, 100, 93, 25, 115,
        96, 129, 79, 220, 34, 42, 144, 136, 70, 238, 184, 20, 222, 94, 11, 219,
        224, 50, 58, 10, 73, 6, 36, 92, 194, 211, 172, 98, 145, 149, 228, 121,
        231, 200, 55, 109, 141, 213, 78, 169, 108, 86, 244, 234, 101, 122, 174, 8,
        186, 120, 37, 46, 28, 166, 180, 198, 232, 221, 116, 31, 75, 189, 139, 138,
        112, 62, 181, 102, 72, 3, 246, 14, 97, 53, 87, 185, 134, 193, 29, 158,
        225, 248, 152, 17, 105, 217, 142, 148, 155, 30, 135, 233, 206, 85, 40, 223,
        140, 161, 137, 13, 191, 230, 66, 104, 65, 153, 45, 15, 176, 84, 187, 22]
def init():
    return 0
def xt(a):
    a = a << 1
    if a & 256:
        a = a ^ 283
    return a
def step(state, inputs):
    x = inputs.get("state_in", 0)
    k = inputs.get("round_key", 0)
    b = []
    for n in range(16):
        b.append(SBOX[(x >> (120 - 8 * n)) & 255])
    t = []
    for n in range(16):
        r = n % 4
        c = n // 4
        t.append(b[r + 4 * ((c + r) % 4)])
    if not inputs.get("final_round", 0):
        m = []
        for c in range(4):
            a0 = t[4 * c]
            a1 = t[4 * c + 1]
            a2 = t[4 * c + 2]
            a3 = t[4 * c + 3]
            m.append(xt(a0) ^ xt(a1) ^ a1 ^ a2 ^ a3)
            m.append(a0 ^ xt(a1) ^ xt(a2) ^ a2 ^ a3)
            m.append(a0 ^ a1 ^ xt(a2) ^ xt(a3) ^ a3)
            m.append(xt(a0) ^ a0 ^ a1 ^ a2 ^ xt(a3))
        t = m
    y = 0
    for n in range(16):
        y = (y << 8) | t[n]
    return 0, {"state_out": y ^ k}
'''
AES_KEY_ORACLE = '''SBOX = [99, 124, 119, 123, 242, 107, 111, 197, 48, 1, 103, 43, 254, 215, 171, 118,
        202, 130, 201, 125, 250, 89, 71, 240, 173, 212, 162, 175, 156, 164, 114, 192,
        183, 253, 147, 38, 54, 63, 247, 204, 52, 165, 229, 241, 113, 216, 49, 21,
        4, 199, 35, 195, 24, 150, 5, 154, 7, 18, 128, 226, 235, 39, 178, 117,
        9, 131, 44, 26, 27, 110, 90, 160, 82, 59, 214, 179, 41, 227, 47, 132,
        83, 209, 0, 237, 32, 252, 177, 91, 106, 203, 190, 57, 74, 76, 88, 207,
        208, 239, 170, 251, 67, 77, 51, 133, 69, 249, 2, 127, 80, 60, 159, 168,
        81, 163, 64, 143, 146, 157, 56, 245, 188, 182, 218, 33, 16, 255, 243, 210,
        205, 12, 19, 236, 95, 151, 68, 23, 196, 167, 126, 61, 100, 93, 25, 115,
        96, 129, 79, 220, 34, 42, 144, 136, 70, 238, 184, 20, 222, 94, 11, 219,
        224, 50, 58, 10, 73, 6, 36, 92, 194, 211, 172, 98, 145, 149, 228, 121,
        231, 200, 55, 109, 141, 213, 78, 169, 108, 86, 244, 234, 101, 122, 174, 8,
        186, 120, 37, 46, 28, 166, 180, 198, 232, 221, 116, 31, 75, 189, 139, 138,
        112, 62, 181, 102, 72, 3, 246, 14, 97, 53, 87, 185, 134, 193, 29, 158,
        225, 248, 152, 17, 105, 217, 142, 148, 155, 30, 135, 233, 206, 85, 40, 223,
        140, 161, 137, 13, 191, 230, 66, 104, 65, 153, 45, 15, 176, 84, 187, 22]
def init():
    return 0
def step(state, inputs):
    k = inputs.get("key_in", 0)
    w0 = (k >> 96) & 4294967295
    w1 = (k >> 64) & 4294967295
    w2 = (k >> 32) & 4294967295
    w3 = k & 4294967295
    rot = ((w3 << 8) | (w3 >> 24)) & 4294967295
    sub = 0
    for n in range(4):
        sub = (sub << 8) | SBOX[(rot >> (24 - 8 * n)) & 255]
    temp = sub ^ (inputs.get("rcon", 0) << 24)
    w4 = w0 ^ temp
    w5 = w1 ^ w4
    w6 = w2 ^ w5
    w7 = w3 ^ w6
    return 0, {"key_out": (w4 << 96) | (w5 << 64) | (w6 << 32) | w7}
'''
PREROT_ORACLE = '''def init():
    return 0
def step(state, inputs):
    a = inputs.get("angle", 0)
    q = a >> 14
    x0 = 39797
    if q == 1 or q == 2:
        a = a ^ 32768
        x0 = 262144 - 39797
    if a >> 15:
        a = a - 65536
    return 0, {"x0": x0, "z0": (a * 16) & 1048575}
'''
ATAN_ORACLE = '''ATAN = [131072, 77376, 40884, 20753, 10417, 5213, 2607, 1304, 652, 326, 163, 81, 41, 20, 10, 5]
def init():
    return 0
def step(state, inputs):
    return 0, {"atan": ATAN[inputs.get("idx", 0)]}
'''
ENGINE_ORACLE = '''def init():
    return {"busy": 0, "ov": 0, "i": 0, "x": 0, "y": 0, "z": 0}
def sx(v, bits):
    return v - (1 << bits) if v >> (bits - 1) else v
def view(s):
    return {"in_ready": 1 if not s["busy"] and not s["ov"] else 0, "out_valid": s["ov"], "iter": s["i"],
            "x": s["x"], "y": s["y"]}
def step(state, inputs):
    if inputs.get("rst", 0):
        return init(), view(init())
    s = dict(state)
    if state["busy"]:
        i = state["i"]
        x = sx(state["x"], 18)
        y = sx(state["y"], 18)
        z = sx(state["z"], 20)
        a = inputs.get("atan_val", 0)
        xs = x >> i
        ys = y >> i
        if z >= 0:
            s["x"] = (x - ys) & 262143
            s["y"] = (y + xs) & 262143
            s["z"] = (z - a) & 1048575
        else:
            s["x"] = (x + ys) & 262143
            s["y"] = (y - xs) & 262143
            s["z"] = (z + a) & 1048575
        s["i"] = (i + 1) & 15
        if i == 15:
            s["busy"] = 0
            s["ov"] = 1
    elif state["ov"]:
        if inputs.get("out_ready", 0):
            s["ov"] = 0
    elif inputs.get("in_valid", 0):
        s["x"] = inputs.get("x0", 0)
        s["y"] = 0
        s["z"] = inputs.get("z0", 0)
        s["i"] = 0
        s["busy"] = 1
    return s, view(s)
'''
CORDIC_OUT_ORACLE = '''def init():
    return 0
def rnd(v):
    if v >> 17:
        v = v - 262144
    return ((v + 2) >> 2) & 65535
def step(state, inputs):
    return 0, {"cos_out": rnd(inputs.get("x_in", 0)), "sin_out": rnd(inputs.get("y_in", 0))}
'''
ORACLES = {"rv_imem": IMEM_ORACLE, "rv_decode": DECODE_ORACLE, "rv_regfile": REGFILE_ORACLE, "rv_alu": ALU_ORACLE,
           "rv_dmem": DMEM_ORACLE, "rv_ctrl": CTRL_ORACLE, "aes_ctrl": AES_CTRL_ORACLE, "aes_round": AES_ROUND_ORACLE,
           "aes_key_step": AES_KEY_ORACLE, "cordic_prerot": PREROT_ORACLE, "cordic_atan": ATAN_ORACLE,
           "cordic_engine": ENGINE_ORACLE, "cordic_out": CORDIC_OUT_ORACLE}


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


def plain(module_name):
    """The oracle as ordinary in-process functions, for composing children."""
    namespace = {}
    exec(ORACLES[module_name], namespace)  # trusted test source, not model output
    return namespace


def test_aes_oracles_compose_to_fips197():
    ctrl, rnd, ks = plain("aes_ctrl"), plain("aes_round"), plain("aes_key_step")
    state = ctrl["init"]()
    _, out = ctrl["step"](state, {"rst": 1})
    row = {"in_valid": 1, "key": 0x000102030405060708090A0B0C0D0E0F, "pt": 0x00112233445566778899AABBCCDDEEFF,
           "out_ready": 0}
    edges = 0
    while not out["out_valid"]:
        key_next = ks["step"](0, {"key_in": out["rk"], "rcon": out["rcon"]})[1]["key_out"]
        round_out = rnd["step"](0, {"state_in": out["ct"], "round_key": out["rk"],
                                    "final_round": out["last"]})[1]["state_out"]
        state, out = ctrl["step"](state, dict(row, round_out=round_out, key_next=key_next))
        edges += 1
    assert edges == 12 and out["ct"] == 0x69C4E0D86A7B0430D8CDB78070B4C55A


def test_cordic_oracles_compose_to_sin_and_cos():
    pre, tab, eng, post = plain("cordic_prerot"), plain("cordic_atan"), plain("cordic_engine"), plain("cordic_out")
    for angle in (0, 0x1555, 0x4000, 0x6000, 0x8000, 0x9234, 0xC000, 0xFFFF):
        state = eng["init"]()
        _, out = eng["step"](state, {"rst": 1})
        start = pre["step"](0, {"angle": angle})[1]
        edges = 0
        while not out["out_valid"]:
            atan = tab["step"](0, {"idx": out["iter"]})[1]["atan"]
            state, out = eng["step"](state, {"in_valid": 1, "x0": start["x0"], "z0": start["z0"],
                                             "atan_val": atan, "out_ready": 0})
            edges += 1
        result = post["step"](0, {"x_in": out["x"], "y_in": out["y"]})[1]
        theta = (angle - 65536 if angle >> 15 else angle) * 2 * math.pi / 65536
        signed = [value - 65536 if value >> 15 else value for value in (result["cos_out"], result["sin_out"])]
        assert edges == 17
        assert abs(signed[0] - 16384 * math.cos(theta)) <= 4 and abs(signed[1] - 16384 * math.sin(theta)) <= 4


# sum = 1 + 2 + ... + 10 in a loop, stored, loaded back and doubled; then halt.
RV_PROGRAM = [
    0x00000093,  # addi x1, x0, 0      (sum)
    0x00A00113,  # addi x2, x0, 10     (counter)
    0x002080B3,  # loop: add x1, x1, x2
    0xFFF10113,  # addi x2, x2, -1
    0xFE011CE3,  # bne x2, x0, loop
    0x00102423,  # sw x1, 8(x0)
    0x00802183,  # lw x3, 8(x0)
    0x00318233,  # add x4, x3, x3
    0x0000006F,  # halt: jal x0, 0
]


def test_rv32i_oracles_compose_into_a_working_core():
    names = ("rv_imem", "rv_decode", "rv_regfile", "rv_alu", "rv_dmem", "rv_ctrl")
    imem, dec, rf, alu, dmem, ctrl = (plain(name) for name in names)
    seq = {"imem": imem, "rf": rf, "dmem": dmem, "ctrl": ctrl}
    state = {key: model["init"]() for key, model in seq.items()}
    outs = {}
    for key, model in seq.items():
        state[key], outs[key] = model["step"](state[key], {"rst": 1})
    for index, word in enumerate(RV_PROGRAM):
        state["imem"], outs["imem"] = imem["step"](state["imem"], {"imem_we": 1, "imem_waddr": index,
                                                                   "imem_wdata": word, "imem_raddr": 0})
    writes, stores = [], []
    for _ in range(400):
        c = outs["ctrl"]
        d = dec["step"](0, {"instr": outs["imem"]["imem_rdata"]})[1]
        a = alu["step"](0, {"a_sel": d["a_sel"], "b_sel": d["b_sel"], "op": d["alu_op"],
                            "rs1_val": outs["rf"]["rdata1"], "rs2_val": outs["rf"]["rdata2"],
                            "pc_val": c["pc"], "imm": d["imm"]})[1]
        if c["rf_we"] and c["rf_waddr"]:
            writes.append((c["rf_waddr"], c["rf_wdata"]))
        if c["dmem_we"]:
            stores.append((c["dmem_addr"], c["dmem_wdata"]))
        state["imem"], outs["imem"] = imem["step"](state["imem"], {"imem_we": 0, "imem_waddr": 0, "imem_wdata": 0,
                                                                   "imem_raddr": c["imem_raddr"]})
        state["rf"], outs["rf"] = rf["step"](state["rf"], {"we": c["rf_we"], "waddr": c["rf_waddr"],
                                                           "wdata": c["rf_wdata"], "raddr1": d["rs1"],
                                                           "raddr2": d["rs2"]})
        state["dmem"], outs["dmem"] = dmem["step"](state["dmem"], {"we": c["dmem_we"], "addr": c["dmem_addr"],
                                                                   "wdata": c["dmem_wdata"]})
        state["ctrl"], outs["ctrl"] = ctrl["step"](state["ctrl"], {
            "run": 1, "kind": d["kind"], "funct3": d["funct3"], "rd": d["rd"], "y": a["y"], "eq": a["eq"],
            "lt": a["lt"], "ltu": a["ltu"], "rs2_val": outs["rf"]["rdata2"], "dmem_rdata": outs["dmem"]["rdata"]})
    expected, total = [(1, 0), (2, 10)], 0
    for count in range(10, 0, -1):
        total += count
        expected += [(1, total), (2, count - 1)]
    assert writes == expected + [(3, 55), (4, 110)]
    assert stores == [(2, 55)]
