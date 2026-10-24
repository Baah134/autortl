"""Only complete direct typed wrappers inherit a numeric latency declaration."""
import copy
from pathlib import Path

import pytest
from autortl.linter import lint_spec, top_verilog, write_stub_project
from autortl.spec import DesignSpec, ModuleSpec, Port, Connection
from autortl.verilog_interface import infer_module


def fixture(latency=1, mode="fixed_latency"):
    ports=[Port("clk","input",1),Port("rst","input",1),Port("a","input",8),Port("y","output",8)]
    child=ModuleSpec("core","preserve exact cycle behavior",ports,latency=latency,compare_mode=mode)
    return DesignSpec("top",[child],external_ports=copy.deepcopy(ports))


@pytest.mark.parametrize("latency",[0,1,3])
def test_known_transparent_wrapper_inherits_numeric_contract(latency):
    spec=fixture(latency)
    assert lint_spec(spec)==[]
    text=top_verilog(spec)
    assert text.startswith(f"// @latency {latency}\n")
    top=infer_module(text,"top")
    assert top.latency_known is True and top.latency==latency
    assert "not measured timing" in text
    assert "always" not in text and "assign" not in text
    assert "core u_core" in text


def test_scoreboard_inherits_minimum_age_without_claiming_fixed_stall_delay():
    spec=fixture(1,"scoreboard")
    for name,direction in (("in_valid","input"),("in_ready","output"),("out_valid","output"),("out_ready","input")):
        port=Port(name,direction,1,protocol="valid_ready")
        spec.modules[0].ports.append(port)
        spec.external_ports.append(copy.deepcopy(port))
    text=top_verilog(spec)
    assert "// @latency 1" in text and "minimum accepted-transfer age" in text
    assert "fixed logical latency" not in text


def test_parameter_defaults_are_bound_without_exposing_or_inventing_top_parameters():
    spec=fixture(3)
    spec.modules[0].parameters={"WIDTH":8,"DEPTH":3}
    text=top_verilog(spec)
    assert "// @latency 3" in text
    assert ".WIDTH(8)" in text and ".DEPTH(3)" in text
    top=infer_module(text,"top")
    assert top.parameters=={} and top.latency_known is True


def test_reordered_exact_named_ports_remain_transparent():
    spec=fixture()
    spec.external_ports.reverse()
    assert "// @latency 1" in top_verilog(spec)


@pytest.mark.parametrize("known",[False,0,1,"true",None])
def test_unknown_or_nonboolean_latency_knowledge_never_inherits(known):
    spec=fixture()
    spec.modules[0].latency_known=known
    assert infer_module(top_verilog(spec),"top").latency_known is False


@pytest.mark.parametrize("latency",[True,False,"1",None,-1,1025])
def test_invalid_numeric_latency_never_becomes_a_header(latency):
    spec=fixture(latency)
    assert "@latency" not in top_verilog(spec)


def test_multiple_children_do_not_invent_graph_aggregate_latency():
    spec=fixture(3)
    other=copy.deepcopy(spec.modules[0]);other.name="other"
    other.ports=[p for p in other.ports if p.direction=="input"]
    spec.modules.append(other)
    assert infer_module(top_verilog(spec),"top").latency_known is False


def test_self_wire_is_not_a_transparent_single_child():
    spec=fixture()
    spec.connections=[Connection("core","y","core","a")]
    assert "@latency" not in top_verilog(spec)


@pytest.mark.parametrize("missing",["a","y"])
def test_missing_external_child_port_does_not_inherit(missing):
    spec=fixture()
    spec.external_ports=[p for p in spec.external_ports if p.name!=missing]
    assert "@latency" not in top_verilog(spec)


@pytest.mark.parametrize("field,value",[("width",4),("signed",True),("protocol","level"),
    ("clock_domain","other"),("packed_dimensions",[[0,7]])])
def test_mismatched_supported_port_metadata_does_not_inherit(field,value):
    spec=fixture()
    setattr(spec.external_ports[-1],field,value)
    assert "@latency" not in top_verilog(spec)


def test_invalid_contract_and_extra_or_duplicate_ports_do_not_inherit():
    for change in ("behavior","extra","duplicate"):
        spec=fixture()
        if change=="behavior":spec.modules[0].behavior=""
        elif change=="extra":spec.external_ports.append(Port("extra","input",1))
        else:spec.external_ports.append(copy.deepcopy(spec.external_ports[-1]))
        assert "@latency" not in top_verilog(spec)


def test_symbolic_fifo_signature_and_default_wrapper_inherit_known_age():
    root=Path(__file__).resolve().parents[1]
    spec=DesignSpec.load(root / "curriculum/tier2/sync_fifo_build/design_spec.json")
    assert lint_spec(spec)==[]
    text=top_verilog(spec)
    assert "// @latency 1" in text and "minimum accepted-transfer age" in text
    assert ".WIDTH(8)" in text and ".DEPTH(3)" in text
    assert infer_module(text,"sync_fifo").latency_known is True


@pytest.mark.parametrize("change",["parameter","shape"])
def test_contradictory_symbolic_signature_does_not_authorize_inheritance(change):
    root=Path(__file__).resolve().parents[1]
    spec=DesignSpec.load(root / "curriculum/tier2/sync_fifo_build/design_spec.json")
    if change=="parameter":spec.modules[0].parameters["WIDTH"]=16
    else:
        for record in spec.modules[0].interface_signature["ports"]:
            if record["name"]=="in_data":record["dimensions"]=[["3","0"]]
    assert "@latency" not in top_verilog(spec)


def test_implicit_and_explicit_same_packed_shape_can_inherit():
    spec=fixture()
    spec.external_ports[-1].packed_dimensions=[[7,0]]
    assert "// @latency 1" in top_verilog(spec)


def test_project_writer_emits_inherited_top_as_utf8(tmp_path):
    files=write_stub_project(fixture(3),tmp_path)
    top=next(p for p in files if p.name=="top.v")
    assert top.read_text(encoding="utf-8").startswith("// @latency 3\n")
