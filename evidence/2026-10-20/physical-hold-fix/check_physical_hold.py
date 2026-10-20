"""Supervised exercise of physical hold-fix command; no model calls."""
import hashlib,json,sys,subprocess
from pathlib import Path
root=Path(sys.argv[1]).resolve();sys.path.insert(0,str(root))
from autortl.config import RunConfig
from autortl.vivado import xsim_run,run_synthesis,full_metrics
from autortl.report_parser import VivadoMetrics,parse_timing
from autortl.metrics_gate import validate
out=root/'logs/physical-hold-fix-01';out.mkdir(parents=True,exist_ok=False)
entry=root/'curriculum/tier0/mux4'
for name in ('mux4.v','mux4_tb.v'):(out/name).write_bytes((entry/name).read_bytes())
bins=Path('C:/AMDDesignTools/2025.2/Vivado/bin')
cfg=RunConfig(mode='optimize',top_module='mux4',**{n+'_bin':str(bins/(n+'.bat')) for n in ('vivado','xvlog','xelab','xsim')})
passed,error,kind=xsim_run([out/'mux4.v'],out/'mux4_tb.v','mux4_tb',cfg,out,timeout=90)
result={'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'simulation':{'passed':passed,'error':error,'kind':kind.value}}
if passed:
 ok,error,kind=run_synthesis([out/'mux4.v'],'mux4',cfg,out,hold_fix=True,timeout=300)
 result['implementation']={'passed':ok,'error':error,'kind':kind.value}
 if ok:
  before=VivadoMetrics();parse_timing(out/'timing.rpt',before)
  m=full_metrics(out);validate(m,synthesis_ran=True)
  result.update(preplace_timing={'wns_ns':before.wns_ns,'whs_ns':before.whs_ns},routed_metrics=m.to_dict())
  passed=m.sim_passed and m.timing_met
 else:passed=False
result['ok']=passed
result['scope']='Supervised source-preserving physical command validation, not an autonomous Doctor run or isolated causal proof of hold_fix benefit.'
(out/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2),flush=True)
raise SystemExit(0 if passed else 1)
