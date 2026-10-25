"""Actual canonical top-first dot4 checker admission; no model calls or canonical source edits."""
import hashlib,json,runpy,sys,time
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8',errors='replace')
ROOT=Path('C:/Users/prince.baah/Downloads/autortl-work')
WORK=Path('C:/Users/prince.baah/Documents/Codex/2026-10-15/hey')
STAGE=ROOT/'curriculum/tier3/dot4_pipeline_build';OUT=ROOT/'logs/dot4-admission-02'
sys.path.insert(0,str(ROOT))
from autortl.config import RunConfig
from autortl.vivado import xsim_run
from autortl.tbqual import assertion_failure_proof
from autortl.contract_context import tool_exit_evidence
from autortl.triage import FailureKind
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
frozen=json.loads((WORK/'work/top-timescale-source-freeze-01.json').read_text())
assert all(sha(ROOT/p)==h for p,h in frozen.items())
assert not OUT.exists()
stage_hash={p.relative_to(STAGE).as_posix():sha(p) for p in STAGE.rglob('*') if p.is_file()}
assert len(stage_hash)==6
cases=runpy.run_path(str(STAGE/'qualification/cases.py'))['materialize_cases'](OUT)
assert len(cases['cases'])==13
binroot='C:/AMDDesignTools/2025.2/Vivado/bin/'
cfg=RunConfig(mode='optimize',top_module='dot4_pipeline',xvlog_bin=binroot+'xvlog.bat',
    xelab_bin=binroot+'xelab.bat',xsim_bin=binroot+'xsim.bat',vivado_bin=binroot+'vivado.bat')
stats=ROOT/'llm/router_stats.jsonl';stats_sha=sha(stats)
(OUT/'prelaunch-plan.json').write_text(json.dumps({'schema_version':1,'stage_files':stage_hash,
    'runtime_source':frozen,'case_manifest_sha256':sha(OUT/'manifest.json'),
    'scope':'Control plus12 actual assertion faults; no synthesis/model;90s per case',
    'model_calls_expected':0,'helper_sha256':sha(Path(__file__))},indent=2),encoding='utf-8')
results=[];start=time.monotonic()
for case in cases['cases']:
    directory=OUT/case['name']
    identities={x['path']:x['sha256'] for x in case['files']}
    assert all(sha(Path(p))==h for p,h in identities.items())
    tick=time.monotonic()
    okay,error,kind=xsim_run([directory/'dot4_pipeline.v',directory/'children.v'],
        directory/'dot4_pipeline_tb.v','dot4_pipeline_tb',cfg,directory,timeout=90)
    proof,detail=assertion_failure_proof(directory)
    exits=tool_exit_evidence(directory)
    exits_ok=exits['schema_valid'] and all(exits['latest_by_tool'].get(t,{}).get('successful') for t in ('xvlog','xelab','xsim'))
    unchanged=all(sha(Path(p))==h for p,h in identities.items())
    accepted=bool(unchanged and exits_ok and kind==FailureKind.DESIGN and
        (okay is True if case['name']=='reference' else okay is False and proof))
    record={'name':case['name'],'admitted':accepted,'simulation_passed':okay,
        'failure_kind':kind.value,'assertion_proof':proof,'proof_reason':detail,'error':error,
        'elapsed_seconds':time.monotonic()-tick,'inputs_unchanged':unchanged,'process_exits':exits}
    results.append(record)
    (directory/'admission-result.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(json.dumps({k:record[k] for k in ('name','admitted','simulation_passed','assertion_proof','elapsed_seconds')}),flush=True)
    if case['name']=='reference' and not accepted:break
qualified=len(results)==13 and all(x['admitted'] for x in results)
assert all(sha(ROOT/p)==h for p,h in frozen.items()) and sha(stats)==stats_sha
assert stage_hash=={p.relative_to(STAGE).as_posix():sha(p) for p in STAGE.rglob('*') if p.is_file()}
result={'qualified':qualified,'planned':13,'executed':len(results),'admitted':sum(x['admitted'] for x in results),
        'elapsed_seconds':time.monotonic()-start,'runtime_source_unchanged':True,'stage_unchanged':True,
        'router_stats_unchanged':True,'model_calls':0,'results':results}
(OUT/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='results'}),flush=True)
assert qualified,'Preserve misses before any checker correction'
