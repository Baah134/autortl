import hashlib,json,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path('C:/Users/prince.baah/Downloads/autortl-work');WORK=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
frozen=json.loads((WORK/'elastic-fixes-source-freeze-01.json').read_text())
assert len(frozen)==220 and all(sha(ROOT/p)==h for p,h in frozen.items())
assert json.loads((WORK/'elastic-fixes-full-result-01.json').read_text())['exit_code']==0
run=ROOT/'logs/contract-campaign-12';assert not run.exists()
plan=ROOT/'logs/contract-campaign-12-prelaunch.json';assert not plan.exists()
args=[sys.executable,'run.py','bench','--tier','0','--iterations','1','--best-of-n','1',
      '--max-llm-calls','16','--max-vivado-minutes','20','--max-wall-minutes','30',
      '--max-infra-retries','1','--target-part','xc7a35tcpg236-1','--target-freq-mhz','100','--output-dir',str(run)]
for name in ('vivado','xvlog','xelab','xsim'):args+=['--'+name,'C:/AMDDesignTools/2025.2/Vivado/bin/'+name+'.bat']
plan.write_text(json.dumps({'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    'runtime_source':frozen,'command':args,'started_utc':datetime.now(timezone.utc).isoformat(),
    'scope':'Fresh full tier0 runtime merge gate; not a new counter design objective; no higher held tier'},indent=2),encoding='utf-8')
print('Launching fresh full tier0 merge gate on frozen220source; original budgets',flush=True)
tick=time.monotonic();code=subprocess.call(args,cwd=ROOT)
result={'exit_code':code,'wall_seconds':time.monotonic()-tick,'source_unchanged':all(sha(ROOT/p)==h for p,h in frozen.items())}
(ROOT/'logs/contract-campaign-12-launch-result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result),flush=True);assert result['source_unchanged'];sys.exit(code)
