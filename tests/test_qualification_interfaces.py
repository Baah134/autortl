"""Fallback qualification must sabotage behavior while preserving declarations."""
from pathlib import Path
from autortl import fsm
from autortl.config import RunConfig
from autortl.triage import FailureKind
from autortl.verilog_interface import infer_module

SOURCE = '''module m #(parameter W=8, parameter LIMIT=10)(
 input clk, input signed [W-1:0] a, output reg signed [0:W-1] y);
 localparam INTERNAL=W;
 always @(posedge clk) y <= a;
endmodule'''


def test_fallback_mutant_preserves_symbolic_signed_interface(tmp_path, monkeypatch):
    o = fsm.Orchestrator(RunConfig(mode='build', top_module='m'), tmp_path/'run')
    monkeypatch.setattr(fsm, 'mutate', lambda source: None)
    sources = {}
    def tool(name, files, tb, top, cfg, directory):
        sources[directory.name] = files[0].read_text()
        if directory.name == 'control':
            return True, '', FailureKind.DESIGN
        return False, 'Testbench failures:\nFAIL stuck zero', FailureKind.DESIGN
    monkeypatch.setattr(o, '_tool', tool)
    tb = tmp_path/'m_tb.v';tb.write_text('// controlled test fixture')
    assert o._qualify_source(SOURCE, tb, 'm', tmp_path)[0]
    reference,mutant = infer_module(SOURCE,'m'),infer_module(sources['mutant'],'m')
    assert mutant.interface_signature == reference.interface_signature
    assert mutant.parameters == reference.parameters
    assert mutant.ports[-1].signed is True
    assert mutant.ports[-1].packed_dimensions == [[0,7]]
    assert 'assign y = 0;' in sources['mutant']
