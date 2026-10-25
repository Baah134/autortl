"""Frozen independent elastic pipeline qualification; no model or synthesis calls."""
import argparse,hashlib,json,re,runpy,sys,time
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8',errors='replace')
parser=argparse.ArgumentParser();parser.add_argument('--attempt',default='01');args=parser.parse_args()
assert args.attempt.isdigit() and len(args.attempt)==2
ROOT=Path('C:/Users/prince.baah/Downloads/autortl-work')
WORK=Path('C:/Users/prince.baah/Documents/Codex/2026-10-15/hey')
STAGE=WORK/'work/elastic-dot4-stage';OUT=ROOT/f'logs/elastic-dot4-admission-{args.attempt}'
sys.path.insert(0,str(ROOT))
from autortl.config import RunConfig
from autortl.vivado import xsim_run
from autortl.tbqual import assertion_failure_proof
from autortl.contract_context import tool_exit_evidence
from autortl.triage import FailureKind
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
identities=runpy.run_path(str(WORK/'work/validate_seed_binding_live.py'))['identities']
frozen=json.loads((WORK/'work/top-timescale-source-freeze-01.json').read_text())
assert identities()==frozen and len(frozen)==211
stage_hash={p.relative_to(STAGE).as_posix():sha(p) for p in STAGE.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
assert len(stage_hash)==7 and not OUT.exists()
cases=runpy.run_path(str(STAGE/'qualification/cases.py'))['materialize_cases'](OUT)
assert len(cases['cases'])==19 and cases['cases'][0]['name']=='reference'
binroot='C:/AMDDesignTools/2025.2/Vivado/bin/'
cfg=RunConfig(mode='optimize',top_module='elastic_dot4',xvlog_bin=binroot+'xvlog.bat',
    xelab_bin=binroot+'xelab.bat',xsim_bin=binroot+'xsim.bat',vivado_bin=binroot+'vivado.bat')
stats=ROOT/'llm/router_stats.jsonl';stats_sha=sha(stats)
(OUT/'prelaunch-plan.json').write_text(json.dumps({'schema_version':1,'stage_files':stage_hash,'runtime_source':frozen,
    'case_manifest_sha256':sha(OUT/'manifest.json'),'helper_sha256':sha(Path(__file__)),
    'scope':'Control plus18 actual compiling behavioral faults; top first;90s each; no models/synthesis',
    'kill_requirement':'Actual BEHAVIOR_FAIL plus successful compile/elaboration/simulation exits; coverage-only failure is not a kill'},indent=2),encoding='utf-8')
rows=[];start=time.monotonic()
for case in cases['cases']:
    directory=OUT/case['name'];inputs={x['path']:x['sha256'] for x in case['files']}
    assert all(sha(Path(p))==h for p,h in inputs.items())
    tick=time.monotonic()
    okay,error,kind=xsim_run([directory/'elastic_dot4.v',directory/'children.v'],directory/'elastic_dot4_tb.v',
                            'elastic_dot4_tb',cfg,directory,timeout=90)
    seconds=time.monotonic()-tick;exits=tool_exit_evidence(directory)
    exit_ok=exits['schema_valid'] and all(exits['latest_by_tool'].get(t,{}).get('successful') for t in ('xvlog','xelab','xsim'))
    raw=(directory/'sim_log.txt').read_text(encoding='utf-8',errors='replace') if (directory/'sim_log.txt').exists() else ''
    markers=re.findall(r'(?m)^BEHAVIOR_FAIL rule=.+$',raw)
    proof,detail=assertion_failure_proof(directory)
    unchanged=all(sha(Path(p))==h for p,h in inputs.items())
    if case['name']=='reference':
        accepted=bool(okay and kind==FailureKind.DESIGN and exit_ok and unchanged and
            re.search(r'(?m)^TEST PASSED\s*$',raw) and not re.search(r'BEHAVIOR_FAIL|CHECKER_FAIL|COVERAGE_FAIL|TEST FAILED|watchdog|timed\s+out',raw,re.I))
    else:
        accepted=bool(not okay and kind==FailureKind.DESIGN and exit_ok and unchanged and proof and markers
                      and not re.search(r'watchdog|timed\s+out',raw,re.I))
    row={'name':case['name'],'admitted':accepted,'simulation_passed':okay,'failure_kind':kind.value,
         'behavioral_assertions':markers,'assertion_proof':proof,'proof_reason':detail,
         'coverage_failure_present':'COVERAGE_FAIL' in raw,'checker_failure_present':'CHECKER_FAIL' in raw,
         'error':error,'elapsed_seconds':seconds,'inputs_unchanged':unchanged,'process_exits':exits}
    rows.append(row);(directory/'admission-result.json').write_text(json.dumps(row,indent=2),encoding='utf-8')
    print(json.dumps({k:row[k] for k in ('name','admitted','simulation_passed','failure_kind','elapsed_seconds')}
                     |{'behavioral_assertion_count':len(markers)}),flush=True)
    if case['name']=='reference' and not accepted:break
assert identities()==frozen and sha(stats)==stats_sha
assert stage_hash=={p.relative_to(STAGE).as_posix():sha(p) for p in STAGE.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
qualified=len(rows)==19 and all(r['admitted'] for r in rows)
result={'qualified':qualified,'planned':19,'executed':len(rows),'admitted':sum(r['admitted'] for r in rows),
        'elapsed_seconds':time.monotonic()-start,'runtime_source_unchanged':True,'stage_unchanged':True,
        'router_stats_unchanged':True,'model_calls':0,'results':rows}
(OUT/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='results'}),flush=True)
assert qualified,'Preserve all inputs/misses before any correction; never reset an attempt'
