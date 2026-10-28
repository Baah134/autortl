"""Pure fixture invariants; these tests do not compile or simulate RTL."""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
import yaml

from autortl.linter import lint_spec, top_verilog
from autortl.spec import DesignSpec
from autortl.verilog_interface import infer_module

ROOT = Path(__file__).resolve().parents[1] / "curriculum/tier3/dot4_pipeline_build"
CHILDREN = ["dot4_pair01", "dot4_pair23", "dot4_merge"]
FAULTS = ["drop_product", "truncate_pair_carry", "truncate_final_carry",
          "signed_operands", "duplicate_first_input_pair", "duplicate_partial_sum",
          "combinational_merge", "extra_merge_stage", "branch_cycle_misalignment",
          "asynchronous_pair_reset", "merge_reset_ignored", "interedge_input_leak"]


def spec():
    return DesignSpec.load(ROOT / "design_spec.json")


def qualification():
    loader = importlib.util.spec_from_file_location("dot4_fixture_cases", ROOT / "qualification/cases.py")
    module = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(module)
    return module


def shape(ports):
    return [(p.name, p.direction, p.width, p.signed) for p in ports]


def test_typed_build_schema_roundtrip_and_no_qualification_seed():
    meta = yaml.safe_load((ROOT / "meta.yaml").read_text(encoding="utf-8"))
    assert meta["mode"] == "build" and meta["generate_golden"] is True
    assert meta["top"] == "dot4_pipeline"
    assert meta["spec"] == "design_spec.json" and meta["tb"] == "dot4_pipeline_tb.v"
    assert "design" not in meta and "reference" not in json.dumps(meta)
    typed = spec()
    assert lint_spec(typed) == []
    assert DesignSpec.from_json(typed.to_json()).to_json() == typed.to_json()
    assert [m.name for m in typed.modules] == CHILDREN
    assert len({m.name for m in typed.modules}) == 3


def test_exact_unsigned_ports_and_two_connections():
    typed = spec()
    expected = [
        {"clk":1,"rst":1,"a0":8,"b0":8,"a1":8,"b1":8,"pair01_sum":17},
        {"clk":1,"rst":1,"a2":8,"b2":8,"a3":8,"b3":8,"pair23_sum":17},
        {"clk":1,"rst":1,"left_sum":17,"right_sum":17,"dot_result":18},
    ]
    for child, widths in zip(typed.modules, expected):
        assert {p.name:p.width for p in child.ports} == widths
        assert all(p.signed is False and p.protocol == "none" for p in child.ports)
        assert [p.name for p in child.ports if p.direction == "output"] == [list(widths)[-1]]
    assert [(c.src_module,c.src_port,c.dst_module,c.dst_port) for c in typed.connections] == [
        ("dot4_pair01","pair01_sum","dot4_merge","left_sum"),
        ("dot4_pair23","pair23_sum","dot4_merge","right_sum")]
    assert {p.name:p.width for p in typed.external_ports} == {
        "clk":1,"rst":1,"a0":8,"b0":8,"a1":8,"b1":8,"a2":8,"b2":8,"a3":8,"b3":8,"dot_result":18}


def test_known_children_unknown_aggregate_and_unambiguous_bindings():
    typed = spec()
    for child in typed.modules:
        assert child.latency == 1 and child.latency_known is True
        assert child.compare_mode == "fixed_latency"
        assert child.reset.kind == "sync" and child.reset.active_high is True
    wrapper = top_verilog(typed)
    assert wrapper.startswith("`timescale 1ns/1ps\n")
    assert "@latency" not in wrapper
    assert infer_module(wrapper, typed.top_name).latency_known is False
    for name in ("a0","b0","a1","b1","a2","b2","a3","b3"):
        assert wrapper.count(f".{name}({name})") == 1
    assert ".left_sum(w_dot4_pair01_pair01_sum)" in wrapper
    assert ".right_sum(w_dot4_pair23_pair23_sum)" in wrapper


@pytest.mark.parametrize("operands,expected", [
    ((0,0,0,0),0), ((255,255,255,255),130050),
    ((255,255,1,1),65026), ((128,255,0,0),32640),
])
def test_pair_math_boundaries(operands, expected):
    a,b,c,d = operands
    actual = a*b+c*d
    assert actual == expected and actual < 2**17


def test_merge_and_integrated_domains_are_distinct():
    assert 2*(2*255*255) == 260100 < 2**18
    assert 2*((1<<17)-1) == 262142 < 2**18
    typed = spec()
    for child in typed.modules:
        for sample in child.examples:
            inputs = sample.inputs
            if child.name == "dot4_merge":
                assert sample.expected == {"dot_result":inputs["left_sum"]+inputs["right_sum"]}
            else:
                offset = 0 if child.name == "dot4_pair01" else 2
                expected = sum(inputs[f"a{i}"]*inputs[f"b{i}"] for i in (offset,offset+1))
                output = "pair01_sum" if offset == 0 else "pair23_sum"
                assert sample.expected == {output:expected}
            assert sample.after_cycles == 1


def test_case_inventory_uniqueness_and_exact_replacement_targets():
    module = qualification()
    cases = module.case_sources()
    assert list(cases) == ["reference"] + FAULTS
    assert list(module.MUTATIONS) == FAULTS
    assert len({(c["children"],c["wrapper"]) for c in cases.values()}) == 13
    assert cases["reference"]["children"] == (ROOT/"qualification/reference.v").read_text(encoding="utf-8")
    assert cases["reference"]["wrapper"] == top_verilog(spec())
    for name,(target,edits) in module.MUTATIONS.items():
        source = cases["reference"][target]
        for old,new in edits:
            assert source.count(old) == 1
            source = source.replace(old,new,1)
        assert source == cases[name][target]


@pytest.mark.parametrize("name", ["reference"] + FAULTS)
def test_each_case_preserves_child_and_wrapper_interfaces(name):
    typed = spec()
    source = qualification().case_sources()[name]
    for child in typed.modules:
        actual = infer_module(source["children"], child.name)
        assert shape(actual.ports) == shape(child.ports)
        assert actual.latency_known is True and actual.latency == 1
    assert shape(infer_module(source["wrapper"],typed.top_name).ports) == shape(typed.external_ports)


def test_prepared_manifest_preserves_exact_inputs_and_tb(tmp_path):
    module = qualification()
    cases = module.case_sources()
    output = tmp_path / "prepared"
    manifest = module.materialize_cases(output)
    assert manifest["status"] == "prepared_not_simulated"
    assert manifest["top"] == "dot4_pipeline_tb" and len(manifest["cases"]) == 13
    assert json.loads((output/"manifest.json").read_text()) == manifest
    tb = (ROOT/"dot4_pipeline_tb.v").read_bytes()
    for case in manifest["cases"]:
        assert case["expected_verdict"] == ("TEST PASSED" if case["name"] == "reference" else "TEST FAILED")
        assert case["required_failure_kind"] == (None if case["name"] == "reference" else "behavioral_assertion")
        assert {Path(f["path"]).name for f in case["files"]} == {"children.v","dot4_pipeline.v","dot4_pipeline_tb.v"}
        for file in case["files"]:
            path = Path(file["path"])
            assert path.is_relative_to(output)
            assert hashlib.sha256(path.read_bytes()).hexdigest() == file["sha256"]
        assert (output/case["name"]/"dot4_pipeline_tb.v").read_bytes() == tb
        assert (output/case["name"]/"children.v").read_text(encoding="utf-8") == cases[case["name"]]["children"]
        assert (output/case["name"]/"dot4_pipeline.v").read_text(encoding="utf-8") == cases[case["name"]]["wrapper"]
    before = (output/"manifest.json").read_bytes()
    with pytest.raises(FileExistsError):
        module.materialize_cases(output)
    assert (output/"manifest.json").read_bytes() == before
