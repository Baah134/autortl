"""Model-written RTL may not use constructs that evade the simulation gate.

Taxonomy: candidate_rtl_evades_simulation_gate (whole-harness review). Each
attack below passed the static check before this gate existed.
"""
import pytest

from autortl.spec import ModuleSpec, Port
from autortl.static_checks import check, rtl_safety_violations

HEADER = "module acc(input clk, input rst, input [7:0] a, output reg [7:0] y);\n"

ATTACKS = {
    "prints its own verdict": HEADER + 'always @(posedge clk) begin $display("TEST PASSED"); $finish; end\n'
                                       "always @(posedge clk) y <= 0;\nendmodule",
    "different design for synthesis": HEADER + "`ifdef SYNTHESIS\nalways @(posedge clk) y <= 0;\n`else\n"
                                               "always @(posedge clk) y <= y + a;\n`endif\nendmodule",
    "translate_off": HEADER + "always @(posedge clk) y <= 0;\n// synthesis translate_off\n"
                              "always @(posedge clk) y <= y + a;\n// synthesis translate_on\nendmodule",
    "pragma block comment": HEADER + "/* pragma translate_off */ always @(posedge clk) y <= a; /* pragma translate_on */\nendmodule",
    "reads the testbench": HEADER + "always @(posedge clk) y <= acc_tb._autortl_exp_y[acc_tb._autortl_index];\nendmodule",
    "writes a file": HEADER + 'integer f; always @(posedge clk) begin f = $fopen("../../autortl/x.py", "w"); '
                              '$fdisplay(f, "x"); end\nendmodule',
    "includes a file": '`include "C:/Users/secret.txt"\n' + HEADER + "endmodule",
    "macro": "`define W 8\n" + HEADER + "always @(posedge clk) y <= `W;\nendmodule",
    "force": HEADER + "always @(posedge clk) force y = 8'd1;\nendmodule",
    "defparam": HEADER + "defparam u.W = 3;\nendmodule",
    "escaped decoy header": "`ifdef NEVER\nmodule acc(input clk, input rst, input [7:0] a, output reg [7:0] y);\n`else\n"
                            "module \\acc (input clk, input rst, input [7:0] a, output reg [15:0] y, input [3:0] extra);\n"
                            "`endif\nendmodule",
}


@pytest.mark.parametrize("name", sorted(ATTACKS))
def test_attacks_are_rejected(name):
    assert rtl_safety_violations(ATTACKS[name]), name


def test_attacks_fail_the_static_check_with_a_contract():
    contract = ModuleSpec(name="acc", behavior="", ports=[
        Port("clk", "input", 1), Port("rst", "input", 1), Port("a", "input", 8), Port("y", "output", 8)], latency=1)
    for name, source in ATTACKS.items():
        assert not check(source, contract).passed, name


LEGITIMATE = """`timescale 1ns/1ps
// optimized for synthesis: the adder maps onto a carry chain
(* use_dsp = "no" *)
module top #(parameter W = 8, parameter D = $clog2(W)) (input clk, input rst, input [W-1:0] a, output reg [W-1:0] y);
    wire signed [W:0] s = $signed({1'b0, a}) + 9'sd1;
    wire [W-1:0] r = 8'hA5 ^ a;
    reg [D:0] n;
    child #(.W(W)) u_child (.clk(clk), .in(a), .out());
    genvar i;
    generate for (i = 0; i < 2; i = i + 1) begin : g
        wire t = a[i];
    end endgenerate
    always @(posedge clk) if (rst) y <= {W{1'b0}}; else y <= s[W-1:0] + $unsigned(r) + $bits(a);
endmodule"""


def test_ordinary_rtl_is_untouched():
    assert rtl_safety_violations(LEGITIMATE) == []
