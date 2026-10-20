from pathlib import Path
import pytest
from autortl.verilog_interface import infer_module, integer
from autortl.static_checks import check
from autortl.spec import ModuleSpec, Port

ROOT = Path(__file__).resolve().parents[1]


def test_real_parameterized_counter_and_grouped_mux_ports():
    counter = infer_module((ROOT / "curriculum/tier0/counter/counter.v").read_text(), "counter")
    assert {p.name: p.width for p in counter.ports}["load_val"] == 32
    mux = infer_module((ROOT / "curriculum/tier0/mux4/mux4.v").read_text(), "mux4")
    assert {p.name for p in mux.ports} == {"clk", "rst", "a", "b", "c", "d", "sel", "y"}
    assert [p.width for p in mux.ports if p.name in "abcd"] == [8, 8, 8, 8]


def test_nonansi_signed_and_parameter_expressions():
    src = "module m #(parameter W=8, N=2)(a,b,y); input signed [W-1:0] a,b; output [W+N-1:0] y; endmodule"
    ports = infer_module(src, "m").ports
    assert [(p.name, p.direction, p.width) for p in ports] == [("a", "input", 8), ("b", "input", 8), ("y", "output", 10)]


@pytest.mark.parametrize("expr, expected", [("$clog2(16)", 4), ("8'hff", 255), ("W-1", 7), ("(3<<2)+1", 13)])
def test_safe_integer_expressions(expr, expected):
    assert integer(expr, {"W": 8}) == expected


@pytest.mark.parametrize("expr", ["__import__('os')", "(1).__class__", "1<<99999", "unknown", "8'bxxxx", "1/0"])
def test_unsupported_integer_expressions_rejected(expr):
    with pytest.raises(ValueError):
        integer(expr, {})


def test_static_width_direction_extra_and_internal_name_cheats_fail():
    contract = ModuleSpec("m", "test", [Port("x", "input", 8), Port("y", "output", 8)])
    for source in [
        "module m(input x,output [7:0] y); endmodule",
        "module m(output [7:0] x,y); endmodule",
        "module m(input [7:0] x,output [7:0] y,z); endmodule",
        "module m(input [7:0] z,output [7:0] y); wire [7:0] x; endmodule",
    ]:
        assert not check(source, contract).passed


def test_default_first_comb_and_identifier_substrings_are_valid():
    contract = ModuleSpec("m", "test", [Port("x", "input", 1), Port("y", "output", 1)])
    source = "module m(input x,output reg y); wire weekend; always @(*) begin y=0; if(x) y=1; end endmodule"
    assert check(source, contract).passed


@pytest.mark.parametrize("source", ["module m(input [X:0] a); endmodule", "module m(a); endmodule", "module m(input a[0:3]); endmodule"])
def test_unsupported_interfaces_fail_closed(source):
    with pytest.raises(ValueError):
        infer_module(source, "m")


@pytest.mark.parametrize("annotation,known,cycles", [("", False, 0), ("// @latency 0\n", True, 0), ("// @latency 2\n", True, 2)])
def test_inferred_latency_distinguishes_absent_annotation_from_zero(annotation, known, cycles):
    source = annotation + "module m(input clk,input a,output reg y); always @(posedge clk) y<=a; endmodule"
    contract = infer_module(source, "m")
    assert contract.latency_known is known and contract.latency == cycles
    # Numeric metadata records a declaration; it does not analyze the RTL's cycles.
    assert contract.interface_signature is not None
