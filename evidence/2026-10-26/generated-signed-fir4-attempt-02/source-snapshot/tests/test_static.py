from autortl.static_checks import check
from autortl.spec import ModuleSpec, Port

CONTRACT = ModuleSpec(name="foo", behavior="x",
                      ports=[Port("clk", "input", 1), Port("rst", "input", 1),
                             Port("y", "output", 8)])

GOOD = """
module foo (input wire clk, input wire rst, output reg [7:0] y);
    always @(posedge clk) begin
        if (rst) y <= 8'd0;
        else y <= y + 8'd1;
    end
endmodule
"""

def test_good_module_passes():
    r = check(GOOD, CONTRACT)
    assert r.passed, r.errors


def test_not_verilog_fails():
    r = check("load = 1; @(posedge clk);")
    assert not r.passed


def test_initial_block_flagged():
    r = check(GOOD.replace("endmodule", "initial y = 0;\nendmodule"), CONTRACT)
    assert any("initial" in e for e in r.errors)


def test_wrong_module_name_flagged():
    r = check(GOOD.replace("module foo", "module bar"), CONTRACT)
    assert any("name mismatch" in e for e in r.errors)


def test_missing_port_flagged():
    bad = GOOD.replace("input wire rst, ", "")
    bad = bad.replace("if (rst) y <= 8'd0;\n        else ", "")
    r = check(bad, CONTRACT)
    assert any("rst" in e for e in r.errors)


def test_latch_heuristic_fires():
    latchy = """
module foo (input wire clk, input wire rst, output reg [7:0] y);
    always @(*) begin
        if (rst) y = 8'd0;
    end
endmodule
"""
    r = check(latchy, CONTRACT)
    assert any("latch" in e for e in r.errors)
