import hashlib,json,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path('C:/Users/prince.baah/Downloads/autortl-work');WORK=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
source=read(WORK/'signed-fir4-source-freeze-01.json');assert len(source)==227 and all(sha(ROOT/p)==h for p,h in source.items())
tests=read(WORK/'signed-fir4-full-result-01.json');assert tests['exit_code']==0 and tests['source_unchanged']
admission=ROOT/'evidence/2026-10-25/signed-fir4-admission-attempt-01'
assert all(sha(admission/p)==h for p,h in read(admission/'archive-manifest.json').items())
result=read(admission/'admission/result.json');assert result['qualified'] and result['admitted']==result['planned']==28
old=read(admission/'admission/prelaunch-plan.json');fixture=ROOT/'curriculum/tier3/signed_fir4_build'
spec=fixture/'design_spec.json';tb=fixture/'signed_fir4_tb.v'
assert sha(spec)==old['stage_files']['design_spec.json'] and sha(tb)==old['stage_files']['signed_fir4_tb.v']
runtime=read(ROOT/'logs/build-elastic-dot4-02/runtime.json')['implementation']
assert all(sha(ROOT/p)==h for p,h in runtime.items())
run=ROOT/'logs/build-signed-fir4-01';pre=ROOT/'logs/build-signed-fir4-01-prelaunch.json';assert not run.exists() and not pre.exists()
stats=ROOT/'llm/router_stats.jsonl';before=stats.read_bytes()
args=[sys.executable,'run.py','build','--spec',str(spec),'--tb',str(tb),'--top','signed_fir4','--generate-golden',
      '--objective','minimize_luts','--target-part','xc7a35tcpg236-1','--target-freq-mhz','100',
      '--iterations','3','--best-of-n','1','--max-llm-calls','16','--max-vivado-minutes','25',
      '--max-wall-minutes','35','--max-infra-retries','1','--output-dir',str(run)]
for name in ('vivado','xvlog','xelab','xsim'):args+=['--'+name,'C:/AMDDesignTools/2025.2/Vivado/bin/'+name+'.bat']
plan={'runtime_source':source,'runtime_implementation_unchanged_from_elastic02':runtime,
      'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
      'fixture_hashes':{p.relative_to(fixture).as_posix():sha(p) for p in fixture.rglob('*') if p.is_file()},
      'spec_path':str(spec),'spec_sha256':sha(spec),'tb_path':str(tb),'tb_sha256':sha(tb),
      'admission_archive':str(admission),'admission_manifest_sha256':sha(admission/'archive-manifest.json'),
      'budgets':{'iterations':3,'best_of_n':1,'model_calls':16,'tool_minutes':25,'wall_minutes':35,'infra_retries':1},
      'command':args,'started_utc':datetime.now(timezone.utc).isoformat(),'reference_is_not_a_generation_input':True,
      'router_stats_offset':len(before),'router_stats_prefix_sha256':hashlib.sha256(before).hexdigest(),
      'model':'codex.default; actual identity unobserved',
      'scope':'Signed accepted-history FIR4, three elastic slots, latency3; no runtime changes or counter rerun'}
pre.write_text(json.dumps(plan,indent=2),encoding='utf-8')
print(json.dumps({'prelaunch':str(pre),'source_files':len(source),'qualified':'28/28','budgets':plan['budgets']}),flush=True)
tick=time.monotonic();code=subprocess.call(args,cwd=ROOT)
result={'exit_code':code,'cli_wall_seconds':time.monotonic()-tick,'source_unchanged':all(sha(ROOT/p)==h for p,h in source.items()),
        'stats_prefix_unchanged':stats.read_bytes()[:len(before)]==before,'ended_utc':datetime.now(timezone.utc).isoformat()}
(ROOT/'logs/build-signed-fir4-01-launch-result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result),flush=True);assert result['source_unchanged'] and result['stats_prefix_unchanged'];sys.exit(code)
