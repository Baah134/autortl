"""Supported signed/packed interface shape survives deterministic generation."""
from unittest.mock import Mock
import pytest
from autortl import roles
from autortl.linter import lint_spec, stub_verilog, top_verilog
from autortl.spec import DesignSpec, ModuleSpec, Port, Connection
from autortl.tbgen import generate_fixed_latency_tb
from autortl.verilog_interface import infer_module


def signed_module():
    return ModuleSpec("signed_copy", "signed bit pattern identity", [
        Port("a", "input", 8, signed=True, packed_dimensions=[[0,7]]),
        Port("y", "output", 8, signed=True, packed_dimensions=[[0,7]])], parameters={"LIMIT":100})


def test_signed_stub_preserves_public_parameters_and_shape():
    module = signed_module()
    source = stub_verilog(module)
    assert "parameter LIMIT = 100" in source
    assert "input wire signed [0:7] a" in source
    assert "output wire signed [0:7] y" in source
    actual = infer_module(source, module.name)
    assert actual.parameters == module.parameters
    assert all(p.signed and p.packed_dimensions == [[0,7]] for p in actual.ports)


def test_signed_top_and_connection_types():
    src = ModuleSpec("producer", "source", [Port("a","input",8,signed=True), Port("v","output",8,signed=True)], parameters={"LIMIT":100})
    dst = ModuleSpec("consumer", "sink", [Port("v","input",8,signed=True), Port("y","output",8,signed=True)])
    design = DesignSpec("top", [src,dst], [Connection("producer","v","consumer","v")], [Port("a","input",8,signed=True), Port("y","output",8,signed=True)])
    assert lint_spec(design) == []
    text = top_verilog(design)
    assert "input wire signed [7:0] a" in text
    assert "output wire signed [7:0] y" in text
    assert "wire signed [7:0] w_producer_v;" in text
    assert ".LIMIT(100)" in text
    dst.ports[0].signed = False
    assert any("signed" in e for e in lint_spec(design))
    dst.ports[0].signed = True
    dst.ports[0].packed_dimensions = [[0,7]]
    assert any("packed" in e for e in lint_spec(design))


def test_external_binding_signed_and_packed_shape():
    module = signed_module()
    ports = [Port("a","input",8,signed=True,packed_dimensions=[[0,7]]), Port("y","output",8,signed=True,packed_dimensions=[[0,7]])]
    design = DesignSpec("top", [module], external_ports=ports)
    assert lint_spec(design) == []
    ports[0].signed = False
    assert any("external binding mismatch" in e for e in lint_spec(design))
    ports[0].signed = True
    ports[0].packed_dimensions = [[7,0]]
    assert any("external binding mismatch" in e for e in lint_spec(design))


def test_signed_tb_keeps_shape_and_masked_bit_patterns():
    module = signed_module()
    text = generate_fixed_latency_tb(module, [{"a":128},{"a":255}], [{"y":128},{"y":255}])
    assert "reg signed [0:7] a;" in text
    assert "wire signed [0:7] y;" in text
    assert "8'd255" in text and ".LIMIT(100)" in text
    with pytest.raises(ValueError, match="masked"):
        generate_fixed_latency_tb(module, [{"a":-1}], [{"y":-1}])


def test_generator_prompt_exposes_signed_parameter_and_signature(monkeypatch):
    call = Mock(return_value="```verilog\nmodule signed_copy; endmodule\n```")
    monkeypatch.setattr(roles, "ask", call)
    module = signed_module()
    module.interface_signature = {"audit_marker":"parameter expression source"}
    roles.Generator().generate(module, "source", "instruction", "mutation", None)
    prompt = call.call_args.args[1]
    assert "input wire signed [0:7] a" in prompt
    assert '\"LIMIT\": 100' in prompt
    assert "audit_marker" in prompt and "parameter expression source" in prompt


def test_inferred_stub_retains_symbolic_public_and_local_dependencies():
    source = """module m #(parameter integer W=8, N=W+1)(a,y);
localparam L=N+1;
input signed [L-1:0] a;
output signed [L-1:0] y;
assign y=a;
endmodule"""
    contract = infer_module(source, "m")
    stub = stub_verilog(contract)
    actual = infer_module(stub, "m")
    assert actual.interface_signature == contract.interface_signature
    assert actual.parameters == {"W":8,"N":9}
    assert "localparam L = N + 1;" in stub
    assert "[L - 1:0]" in stub
    assert "parameter integer W = 8;" in stub


def test_multidimensional_signed_tb_and_stub_keep_all_packed_dimensions():
    module = ModuleSpec("packed_copy", "packed bit pattern identity", [
        Port("a","input",8,signed=True,packed_dimensions=[[1,0],[0,3]]),
        Port("y","output",8,signed=True,packed_dimensions=[[1,0],[0,3]])])
    assert "input wire signed [1:0][0:3] a" in stub_verilog(module)
    text = generate_fixed_latency_tb(module, [{"a":255}], [{"y":255}])
    assert "reg signed [1:0][0:3] a;" in text
    assert "reg signed [1:0][0:3] _autortl_stim_a [0:0];" in text


def test_golden_prompt_keeps_signed_values_as_masked_bit_patterns(monkeypatch):
    call = Mock(return_value="```python\ndef init(): return {}\n```")
    monkeypatch.setattr(roles, "ask", call)
    roles.Generator().golden_model(signed_module(), None)
    prompt = call.call_args.args[1]
    assert "input wire signed [0:7] a" in prompt
    assert "masked nonnegative bit patterns" in prompt
    assert "two's-complement" in prompt
    assert '\"LIMIT\": 100' in prompt
