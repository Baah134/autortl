from autortl.spec import DesignSpec, ModuleSpec, Port, Connection
from autortl.linter import lint_spec, stub_verilog, top_verilog


def two_module_spec(width_b=8, proto_b="none", clk_b="clk"):
    a = ModuleSpec(name="src", behavior="produces data",
                   ports=[Port("clk", "input", 1), Port("rst", "input", 1),
                          Port("dout", "output", 8)])
    b = ModuleSpec(name="dst", behavior="consumes data",
                   ports=[Port("clk", "input", 1), Port("rst", "input", 1),
                          Port("din", "input", width_b, clock_domain=clk_b,
                               protocol=proto_b)],
                   clock_domains=["clk", clk_b] if clk_b != "clk" else ["clk"])
    return DesignSpec(top_name="top", modules=[a, b],
                      connections=[Connection("src", "dout", "dst", "din")],
                      external_ports=[Port("clk", "input", 1),
                                      Port("rst", "input", 1)])


def test_clean_spec_lints_clean():
    assert lint_spec(two_module_spec()) == []


def test_width_mismatch_caught():
    errs = lint_spec(two_module_spec(width_b=16))
    assert any("width mismatch" in e for e in errs)


def test_protocol_mismatch_caught():
    errs = lint_spec(two_module_spec(proto_b="valid_ready"))
    assert any("protocol mismatch" in e for e in errs)


def test_cdc_without_module_caught():
    errs = lint_spec(two_module_spec(clk_b="rd_clk"))
    assert any("clock-domain crossing" in e for e in errs)


def test_dangling_input_caught():
    spec = two_module_spec()
    spec.connections = []       # nothing drives dst.din now
    errs = lint_spec(spec)
    assert any("dangling input" in e for e in errs)


def test_stub_and_top_are_verilog():
    spec = two_module_spec()
    s = stub_verilog(spec.modules[0])
    assert "module src" in s and "endmodule" in s
    t = top_verilog(spec)
    assert "module top" in t and "u_src" in t and "u_dst" in t
    assert "w_src_dout" in t
