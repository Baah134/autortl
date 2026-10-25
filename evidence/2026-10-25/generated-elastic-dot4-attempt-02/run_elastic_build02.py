import hashlib,json,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path('C:/Users/prince.baah/Downloads/autortl-work')
BASE=Path('C:/Users/prince.baah/Documents/Codex/2026-10-15/hey');WORK=BASE/'work'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
source=read(WORK/'elastic-fixes-source-freeze-01.json')
assert len(source)==220 and all(sha(ROOT/p)==h for p,h in source.items())
tests=read(WORK/'elastic-fixes-full-result-01.json');assert tests['exit_code']==0 and tests['source_unchanged']
archive=ROOT/'evidence/2026-10-25/elastic-harness-fixes-01'
assert all(sha(archive/p)==h for p,h in read(archive/'archive-manifest.json').items())
old=read(ROOT/'logs/build-elastic-dot4-01-prelaunch.json')
fixture=ROOT/'curriculum/tier3/elastic_dot4_build'
spec=fixture/'design_spec.json';tb=fixture/'elastic_dot4_tb.v'
assert sha(spec)==old['spec_sha256'] and sha(tb)==old['tb_sha256']
admission=Path(old['admission_archive'])
assert sha(admission/'archive-manifest.json')==old['admission_manifest_sha256']
assert all(sha(admission/p)==h for p,h in read(admission/'archive-manifest.json').items())
run=ROOT/'logs/build-elastic-dot4-02';assert not run.exists()
pre=ROOT/'logs/build-elastic-dot4-02-prelaunch.json';assert not pre.exists()
stats=ROOT/'llm/router_stats.jsonl';before=stats.read_bytes()
args=[sys.executable,'run.py','build','--spec',str(spec),'--tb',str(tb),'--top','elastic_dot4','--generate-golden',
      '--objective','minimize_luts','--target-part','xc7a35tcpg236-1','--target-freq-mhz','100',
      '--iterations','3','--best-of-n','1','--max-llm-calls','16','--max-vivado-minutes','25',
      '--max-wall-minutes','35','--max-infra-retries','1','--output-dir',str(run)]
for name in ('vivado','xvlog','xelab','xsim'):args+=['--'+name,'C:/AMDDesignTools/2025.2/Vivado/bin/'+name+'.bat']
plan=dict(old,runtime_source=source,git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
          spec_path=str(spec),tb_path=str(tb),fixture_hashes={p.relative_to(fixture).as_posix():sha(p) for p in fixture.rglob('*') if p.is_file()},
          previous_failed_run_preserved=True,command=args,started_utc=datetime.now(timezone.utc).isoformat(),
          router_stats_offset=len(before),router_stats_prefix_sha256=hashlib.sha256(before).hexdigest(),
          harness_fix_archive=str(archive),harness_fix_manifest_sha256=sha(archive/'archive-manifest.json'))
pre.write_text(json.dumps(plan,indent=2),encoding='utf-8')
print(json.dumps({'prelaunch':str(pre),'source_files':len(source),'same_original_spec_and_TB':True,'budget':plan['budgets']}),flush=True)
tick=time.monotonic();code=subprocess.call(args,cwd=ROOT)
result={'exit_code':code,'cli_wall_seconds':time.monotonic()-tick,'source_unchanged':all(sha(ROOT/p)==h for p,h in source.items()),
        'stats_prefix_unchanged':stats.read_bytes()[:len(before)]==before,'ended_utc':datetime.now(timezone.utc).isoformat()}
(ROOT/'logs/build-elastic-dot4-02-launch-result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result),flush=True);assert result['source_unchanged'] and result['stats_prefix_unchanged'];sys.exit(code)
