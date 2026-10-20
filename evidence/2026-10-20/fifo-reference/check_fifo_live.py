"""Supervised FIFO reference qualification, no model calls or implementation."""
import json,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve();sys.path.insert(0,str(root))
from tests.fifo_live_cases import save
from autortl.config import RunConfig
from autortl.vivado import xsim_run
from autortl.triage import FailureKind
out=root/'logs/fifo-reference-01';out.mkdir(parents=True,exist_ok=False)
bins=Path('C:/AMDDesignTools/2025.2/Vivado/bin')
cfg=RunConfig(mode='optimize',**{n+'_bin':str(bins/(n+'.bat')) for n in ('vivado','xvlog','xelab','xsim')})
results=[]
for case in save(out):
 work=out/case['case']
 passed,error,kind=xsim_run([work/'async_fifo.v'],work/'async_fifo_tb.v',case['top'],cfg,work,timeout=90)
 assertion=not passed and kind==FailureKind.DESIGN and (error.startswith('Testbench failures:') or error=='testbench reported failure')
 result={**case,'passed':passed,'error':error,'failure_kind':kind.value,'ok':passed if case['expected_pass'] else assertion}
 results.append(result);(out/'results.json').write_text(json.dumps(results,indent=2));print(json.dumps(result),flush=True)
raise SystemExit(0 if all(r['ok'] for r in results) else 1)
