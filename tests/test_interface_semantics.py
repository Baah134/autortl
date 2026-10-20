"""Regression cases for optimization interfaces, independent of RTL bodies."""
import json
import pytest
from autortl.spec import DesignSpec, ModuleSpec, Port, port_declaration
from autortl.verilog_interface import infer_module
from autortl.static_checks import check

BASE = "module m #(parameter integer W=8, LIMIT=17)(input signed [W-1:0] x, output [0:W-1] y); assign y=x; endmodule"

@pytest.mark.parametrize("candidate", [
    BASE.replace("LIMIT=17", "LIMIT=18"),
    BASE.replace(", LIMIT=17", ""),
    BASE.replace(", LIMIT=17", "").replace("assign y", "localparam LIMIT=17; assign y"),
    BASE.replace("input signed", "input unsigned"),
    BASE.replace("[W-1:0]", "[7:0]"),
    BASE.replace("[0:W-1]", "[W-1:0]"),
])
def test_six_interface_semantic_bypasses_rejected(candidate):
    assert not check(candidate, infer_module(BASE, "m")).passed


def test_formatting_grouping_and_internal_constants_are_not_interface_changes():
    original="module m #(parameter integer W=8, N=W+1)(input signed [W-1:0] a,b, output [N-1:0] y); endmodule"
    candidate="module m #(parameter integer W = 8, parameter integer N = W + 1)(input signed [ W - 1 : 0 ] a, input signed [W-1:0] b, output [N-1:0] y); localparam SCRATCH=999; endmodule"
    assert check(candidate, infer_module(original,"m")).passed


def test_interface_keeps_transitive_local_dependencies_and_public_default_dependencies():
    source="module m #(parameter W=8, N=W+1)(x); localparam A=W+1, B=A+1, UNUSED=7; input [B-1:0] x; endmodule"
    contract=infer_module(source,"m")
    assert contract.parameters == {"W":8,"N":9}
    assert check(source.replace("UNUSED=7","UNUSED=99"),contract).passed
    assert not check(source.replace("A=W+1","A=9"),contract).passed
    assert not check(source.replace("N=W+1","N=9"),contract).passed


def test_parameter_type_and_order_are_contractual():
    source="module m #(parameter integer A=1, parameter B=2)(input x); endmodule"
    contract=infer_module(source,"m")
    assert not check(source.replace("parameter integer A=1, parameter B=2", "parameter B=2, parameter integer A=1"),contract).passed
    assert not check(source.replace("integer A", "int A"),contract).passed


def test_grouped_port_signedness_int_defaults_and_unsigned_override():
    m=infer_module("module m(input signed [3:0] a,b, output integer c,d, input int unsigned e,f); endmodule","m")
    assert [(p.name,p.width,p.signed) for p in m.ports] == [("a",4,True),("b",4,True),("c",32,True),("d",32,True),("e",32,False),("f",32,False)]


def test_multiple_packed_dimensions_preserve_shape_and_orientation():
    source="module m(input signed [1:0][0:3] a); endmodule"
    contract=infer_module(source,"m")
    p=contract.ports[0]
    assert p.width == 8 and p.packed_dimensions == [[1,0],[0,3]]
    assert not check(source.replace("[1:0][0:3]","[7:0]"),contract).passed
    assert port_declaration(p, "reg") == "reg signed [1:0][0:3] a"
    assert port_declaration(p, include_direction=True, name="renamed") == "input wire signed [1:0][0:3] renamed"


def test_signature_json_roundtrip_and_hash_sensitivity():
    m=infer_module(BASE,"m")
    d=DesignSpec("m",[m])
    copied=DesignSpec.from_json(d.to_json()).modules[0]
    assert copied == m and copied.contract_hash() == m.contract_hash()
    changed=infer_module(BASE.replace("[W-1:0]","[7:0]"),"m")
    assert changed.contract_hash() != m.contract_hash()


def test_legacy_unsigned_spec_uses_width_and_sensible_default_ranges():
    p=Port("x","input",8)
    assert p.signed is False and p.packed_dimensions is None
    assert port_declaration(p)=="wire [7:0] x"
    assert port_declaration(Port("b","output",1),include_direction=True)=="output wire b"
    contract=ModuleSpec("m","unsigned legacy",[p])
    assert check("module m(input [7:0] x); endmodule",contract).passed
    assert not check("module m(input signed [7:0] x); endmodule",contract).passed


@pytest.mark.parametrize("dimensions", [[[7,0]], [[0,7]], [[1,0],[3,0]]])
def test_port_dimensions_json_shape_valid(dimensions):
    assert Port("x","input",8,packed_dimensions=dimensions).validate()==[]


@pytest.mark.parametrize("dimensions", [[], [[7]], [[True,0]], [[3,0]], "[7:0]"])
def test_bad_dimensions_rejected(dimensions):
    assert Port("x","input",8,packed_dimensions=dimensions).validate()


def test_invalid_signature_rejected_actionably():
    m=ModuleSpec("m","test",[Port("x","input",1)],interface_signature={"version":999})
    assert any("signature" in e for e in m.validate())


def test_comments_act_as_whitespace_in_interface_declarations():
    original="module m #(parameter W=8)(input signed [W-1:0] a); endmodule"
    candidate="module/*gap*/m #(parameter/*gap*/W=8)(input/*gap*/signed [W/*gap*/-1:0] a); endmodule"
    assert check(candidate,infer_module(original,"m")).passed


def test_packed_signed_parameter_defaults_are_resolved_with_type():
    m=infer_module("module m #(parameter signed [7:0] A=8'hff, parameter integer B=32'hffffffff)(input x); endmodule","m")
    assert m.parameters=={"A":-1,"B":-1}


@pytest.mark.parametrize("expression",["1; initial begin end", "__import__('os')", "x.y", "[1,2]"])
def test_untrusted_signature_expressions_cannot_inject_verilog(expression):
    m=infer_module(BASE,"m")
    m.interface_signature["parameters"][0]["default"]=expression
    assert any("signature" in e for e in m.validate())


def test_signed_sized_literals_and_truncation_in_public_defaults():
    m=infer_module("module m #(parameter A=8'shff, B=4'h1f)(input x); endmodule","m")
    assert m.parameters=={"A":-1,"B":15}


@pytest.mark.parametrize("declaration",["wire signed [7:0] x", "reg [0:7] x", "reg [3:0][1:0] x"])
def test_ambiguous_nonansi_port_redeclarations_fail_actionably(declaration):
    with pytest.raises(ValueError,match="non-ANSI.*redeclaration"):
        infer_module(f"module m(x); input [7:0] x; {declaration}; endmodule","m")


def test_signedness_and_orientation_change_contract_hash():
    base=ModuleSpec("m","test",[Port("a","input",8)])
    signed=ModuleSpec("m","test",[Port("a","input",8,signed=True)])
    ascending=ModuleSpec("m","test",[Port("a","input",8,packed_dimensions=[[0,7]])])
    assert len({m.contract_hash() for m in (base,signed,ascending)})==3


@pytest.mark.parametrize("storage",["reg","wire","logic"])
def test_compatible_nonansi_net_variable_redeclarations_preserve_interface(storage):
    plain="module m #(parameter W=8)(x,y); input signed [W-1:0] x; output signed [W-1:0] y; endmodule"
    repeated=plain.replace("endmodule",f"{storage} signed [W-1:0] y; reg [23:0] scratch; endmodule")
    assert infer_module(repeated,"m").interface_signature==infer_module(plain,"m").interface_signature
    assert check(repeated,infer_module(plain,"m")).passed


def test_nonansi_scalar_plus_vector_redeclaration_does_not_silently_merge():
    with pytest.raises(ValueError,match="non-ANSI.*redeclaration"):
        infer_module("module m(y); output y; reg [7:0] y; endmodule","m")


def test_nonansi_same_resolved_width_different_symbolic_bounds_rejected():
    with pytest.raises(ValueError,match="non-ANSI.*redeclaration"):
        infer_module("module m #(parameter W=8)(y); output [W-1:0] y; reg [7:0] y; endmodule","m")
