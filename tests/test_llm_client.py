import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from llm.client import extract_verilog, declared_latency


def test_extract_prefers_module_block():
    resp = """Here is the tb context:
```text
load = 1; @(posedge clk);
```
And the fix:
```verilog
module counter (input clk); endmodule
```"""
    out = extract_verilog(resp)
    assert out.startswith("module counter")


def test_extract_skips_nonmodule_fence():
    resp = "```verilog\nload = 1;\n```\n```verilog\nmodule m; endmodule\n```"
    assert "module m" in extract_verilog(resp)


def test_extract_strips_think_tags():
    resp = "<think>module fake; endmodule</think>\n```verilog\nmodule real_m; endmodule\n```"
    assert "real_m" in extract_verilog(resp)


def test_raw_module_fallback():
    assert "endmodule" in extract_verilog("module bare; wire x; endmodule")


def test_declared_latency():
    assert declared_latency("// @latency 3\nmodule m; endmodule") == 3
    assert declared_latency("module m; endmodule") is None
