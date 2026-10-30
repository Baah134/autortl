"""Pure/mock reproductions on frozen 749d6d1; no model, EDA or board access."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch
import sys
import json

WORK = Path(__file__).resolve().parent
SNAPSHOT = WORK / 'review-oct29-749d6d1'
sys.path.insert(0, str(SNAPSHOT))
sys.path.insert(0, str(SNAPSHOT / 'hardware/basys3/harness_winners'))
from autortl import companions
from autortl.static_checks import check
from autortl.triage import classify
from autortl.fsm import Orchestrator
from autortl.config import RunConfig
from autortl.report_parser import VivadoMetrics
from tests.test_companions import TOP, INLINED, TB_NAMES_CORE, files
from hwsuite import cli

results = {}
rtl = '''module trap(input wire clk, output wire q);
assign q=1'b0;
wire [15:0] marker="//"; always @(posedge clk) begin $display("TEST PASSED"); $finish; end
endmodule'''
checked = check(rtl)
results['forbidden_tasks_hidden_by_literal'] = {'static_passed': checked.passed, 'errors': checked.errors}
results['infrastructure_classification'] = {
    'mixed_log': classify('ERROR: [Synth 8-439] module sub not found\nPermission denied\n').value,
    'tool_id_host_failure': classify('ERROR: [XSIM 43-3225] Permission denied\n').value,
}
with TemporaryDirectory(prefix='review-oct29-probes-', dir=WORK) as temp:
    root = Path(temp)
    extra, tb = files(root, TB_NAMES_CORE)
    dead = '''module uart_tx(input wire clk,input wire rst,output wire tx);
assign tx=0;
generate if(0) begin uart_tx_core unused(.clk(clk),.rst(rst),.tx()); end endgenerate
endmodule'''
    results['dead_companion_instance'] = {'violation': companions.violation(dead, 'uart_tx', extra, tb)}
    o = Orchestrator(RunConfig(mode='optimize',top_module='uart_tx',max_fix_attempts=1), root/'run')
    o._model = Mock(return_value=INLINED)
    o._full_flow = Mock(return_value=VivadoMetrics(sim_passed=True))
    vfile = root/'candidate.v'
    vfile.write_text(TOP)
    repaired, metrics = o._fix_loop(TOP, VivadoMetrics(sim_passed=False,sim_error='TEST FAILED'),
                                   tb,vfile,root/'iter',extra)
    results['baseline_repair_companion'] = {
        'existing_gate_would_reject': bool(companions.violation(INLINED,'uart_tx',extra,tb)),
        'repair_accepted': repaired==INLINED and metrics.sim_passed,
        'full_flow_calls':o._full_flow.call_count,
    }
    design = SimpleNamespace(name='probe', module='probe',in_bytes=1,out_bytes=1,overlap=True,
        winner=root/'winner.v',adapter=root/'adapter.v',fault={'name':'probe_fault'},
        verify=lambda:None,faulted_source=lambda:'module probe; endmodule')
    def fake_run(cmd,cwd,log):
        if cmd[0]=='xsim':
            log.write_text('PASS: checker completed\n')
            return 9
        log.write_text('')
        return 0
    with patch.object(cli,'_tool',side_effect=lambda folder,name:name), \
         patch.object(cli,'rtl_sources',return_value=[]), \
         patch.object(cli.vectors,'build',return_value=([],[])), \
         patch.object(cli.vectors,'write'), patch.object(cli,'_run',side_effect=fake_run):
        ok,verdict=cli.simulate(design,root,root/'simulation',design.winner)
        results['simulator_nonzero_exit']={'exit_code_supplied':9,'reported_passed':ok,'verdict':verdict}
    suite=root/'suite'
    suite.mkdir()
    with patch.object(cli,'SUITE',suite), \
         patch.object(cli,'simulate',side_effect=[(True,'PASS: nominal'),(False,'FAIL: xelab error (see xelab.txt)')]):
        cli.cmd_sim(SimpleNamespace(design='probe',vivado=root),{'probe':design})
        record=json.loads((suite/'build/sim_summary.json').read_text())
        results['elaboration_failure_counted_as_fault_detection']=record['probe']

(WORK/'review-oct29-probes.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
