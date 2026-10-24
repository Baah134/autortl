"""Actual Verilog semantics for the reproduced pre-fix dedupe collision."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path('C:/Users/prince.baah/Downloads/autortl-work')
sys.path.insert(0,str(ROOT))
from autortl.cache import code_hash
from autortl.bestofn import Candidate,dedupe
from autortl.config import RunConfig
from autortl.vivado import xsim_run
from autortl.contract_context import tool_exit_evidence
from autortl.triage import FailureKind
out=ROOT/'logs/exact-dedupe-collision-01'
assert not out.exists()
sources=['module m(output [15:0] y); assign y = "//A"; endmodule',
         'module m(output [15:0] y); assign y = "//B"; endmodule']
assert code_hash(sources[0])==code_hash(sources[1])
survivors=dedupe([Candidate(sources[0],'standard'),Candidate(sources[1],'narrow')])
assert len(survivors)==1, 'This reproducer must run before the dedupe hotfix'
binroot='C:/AMDDesignTools/2025.2/Vivado/bin/'
cfg=RunConfig(mode='optimize',top_module='m',vivado_bin=binroot+'vivado.bat',xvlog_bin=binroot+'xvlog.bat',xelab_bin=binroot+'xelab.bat',xsim_bin=binroot+'xsim.bat')
out.mkdir(parents=True,exist_ok=False)
results=[]
for name,source,expected in zip(('A','B'),sources,('2f41','2f42')):
    directory=out/name;directory.mkdir()
    v=directory/'m.v';v.write_text(source,encoding='utf-8')
    tb=directory/'m_tb.v'
    tb.write_text('module m_tb; wire [15:0] y; m dut(y); initial begin #1; '+
        f'if (y !== 16\'h{expected}) $fatal(1,"Wrong literal value"); '+
        '$display("OBSERVED=%h",y); $display("TEST PASSED"); $finish; end endmodule',encoding='utf-8')
    immutable={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (v,tb)}
    okay,error,kind=xsim_run([v],tb,'m_tb',cfg,directory,timeout=90)
    raw=(directory/'sim_log.txt').read_text(errors='replace')
    exits=tool_exit_evidence(directory)
    assert okay and kind==FailureKind.DESIGN and 'TEST PASSED' in raw and f'OBSERVED={expected}' in raw
    assert exits['schema_valid'] and all(exits['latest_by_tool'][t]['successful'] for t in ('xvlog','xelab','xsim'))
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in immutable.items())
    results.append({'name':name,'source':source,'expected_observed_hex':expected,'actual_simulation_passed':True,'inputs':immutable,'process_exits':exits})
report={'scope':'Actual compiling Verilog sources with different observable values collide under pre-fix normalization; no model call or synthesis',
        'normalized_hashes':[code_hash(s) for s in sources],'pre_fix_survivors':len(survivors),'different_observable_values':True,'simulations':results}
(out/'result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'ok':True,'normalized_hash':code_hash(sources[0]),'pre_fix_survivors':len(survivors),'actual_observed_hex':['2f41','2f42']}),flush=True)
