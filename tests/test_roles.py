"""Latency guidance follows actual declared knowledge rather than inferred zero."""
from unittest.mock import Mock
import pytest
from autortl import roles
from autortl.spec import ModuleSpec, Port
from autortl.verilog_interface import infer_module

SOURCE = "module m(input clk,input a,output reg y); always @(posedge clk) y<=a; endmodule"


def test_generator_unknown_latency_preserves_registered_cycles_without_invented_header(monkeypatch):
    call = Mock(return_value="```verilog\n" + SOURCE + "\n```")
    monkeypatch.setattr(roles, "ask", call)
    module = infer_module(SOURCE, "m")
    generated = roles.Generator().generate(module, SOURCE, "preserve behavior", "logic only", None)
    prompt = call.call_args.args[1]
    assert "Latency: UNKNOWN" in prompt
    assert "registered outputs" in prompt and "Do not invent an @latency header" in prompt
    assert "@latency 0" not in prompt
    assert "@latency" not in generated
    assert "When numeric latency is UNKNOWN" in call.call_args.kwargs["system"]


@pytest.mark.parametrize("latency", [0, 3])
def test_generator_known_latency_requires_exact_numeric_header(monkeypatch, latency):
    call = Mock(return_value="```verilog\n// @latency " + str(latency) + "\n" + SOURCE + "\n```")
    monkeypatch.setattr(roles, "ask", call)
    module = ModuleSpec("m", "fixed behavior", [Port("clk", "input", 1), Port("a", "input", 1), Port("y", "output", 1)], latency=latency)
    generated = roles.Generator().generate(module, SOURCE, "preserve behavior", "logic only", None)
    prompt = call.call_args.args[1]
    assert f"Latency: {latency} cycles (fixed numeric contract)" in prompt
    assert f"Include a '// @latency {latency}' header" in prompt
    assert f"// @latency {latency}" in generated
