"""Independent exact top/three children check plus restored actual DONE probes."""
import hashlib,json,os,re,shutil,subprocess,sys,time
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8',errors='replace')
ROOT=Path('C:/Users/prince.baah/Downloads/autortl-work')
WORK=Path('C:/Users/prince.baah/Documents/Codex/2026-10-15/hey')
RUN=ROOT/'logs/build-dot4-01';OUT=ROOT/'logs/build-dot4-01-verification'
sys.path.insert(0,str(ROOT))
from autortl.config import RunConfig
from autortl.vivado import xsim_run
from autortl.contract_context import tool_exit_evidence
from autortl.triage import FailureKind
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
plan=read(ROOT/'logs/build-dot4-01-prelaunch.json');summary=read(RUN/'run_summary.json');state=read(RUN/'state.json')
assert summary['status']=='done' and state['phase']=='DONE'
assert all(sha(ROOT/p)==h for p,h in plan['runtime_source'].items())
inputs=read(RUN/'inputs.json');assert sha(Path(inputs['testbench_path']['path']))==plan['tb_sha256']
children=[RUN/'modules'/name/(name+'.v') for name in ('dot4_pair01','dot4_pair23','dot4_merge')]
assert all(state['final_artifacts'].get(str(p.resolve()))==sha(p) for p in children)
saved=RUN/'dot4_pipeline_best.v';assert sha(saved)==state['best_sha256']
measured=Path(summary['best_artifact_dir'])/'dot4_pipeline.v'
assert measured.read_bytes().replace(b'\r\n',b'\n')==saved.read_bytes().replace(b'\r\n',b'\n')
OUT.mkdir(parents=True,exist_ok=False);ind=OUT/'independent';ind.mkdir()
copied=[]
for p in [saved,*children]:
    dest=ind/p.name;shutil.copyfile(p,dest);assert sha(dest)==sha(p);copied.append(dest)
tb=ind/'dot4_pipeline_tb.v';shutil.copyfile(inputs['testbench_path']['path'],tb)
immutable={str(p):sha(p) for p in [saved,*children,*copied,tb]}
cfg=RunConfig.load(RUN/'config.json');tick=time.monotonic()
okay,error,kind=xsim_run(copied,tb,'dot4_pipeline_tb',cfg,ind,timeout=90)
seconds=time.monotonic()-tick;raw=(ind/'sim_log.txt').read_text(errors='replace');exits=tool_exit_evidence(ind)
assert okay and kind==FailureKind.DESIGN and exits['schema_valid']
assert all(exits['latest_by_tool'].get(t,{}).get('successful') for t in ('xvlog','xelab','xsim'))
assert re.search(r'(?m)^\s*TEST PASSED\s*$',raw) and not re.search(r'FAIL|watchdog|timeout',raw,re.I)
assert 'COVERAGE checked=685 holds=684 resets=5 pulses=1' in raw
assert all(sha(Path(p))==h for p,h in immutable.items())
(ind/'result.json').write_text(json.dumps({'passed':True,'seconds':seconds,'identities':immutable,'process_exits':exits},indent=2),encoding='utf-8')
paths={Path(p) for p in state['final_artifacts']}
paths.update(RUN/n for n in ('state.json','runtime.json','config.json','budget.json','run_summary.json','inputs.json','plan.md','events.jsonl','designs.jsonl','progress.md','dot4_pipeline_best.v'))
paths.update(RUN.glob('journal/*/started.json'));paths.update(RUN.glob('journal/*/completed.json'))
paths.update(Path(v['path']) for v in inputs.values());paths.add(ROOT/'llm/router_stats.jsonl')
before={str(p):sha(p) for p in paths};files={str(p.relative_to(RUN)) for p in RUN.rglob('*') if p.is_file()}
def invoke(name):
    process=subprocess.run([sys.executable,'-u','run.py','resume','--run',str(RUN)],cwd=ROOT,
        env={**os.environ,'PYTHONIOENCODING':'utf-8','PYTHONDONTWRITEBYTECODE':'1'},
        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',timeout=60)
    (OUT/(name+'.txt')).write_text(process.stdout,encoding='utf-8')
    return process.returncode
codes={'nominal':invoke('nominal')};assert codes['nominal']==0
assert all(sha(Path(p))==h for p,h in before.items())
probes=[*(('child_'+p.parent.name,p) for p in children),('resolved_spec',RUN/'design_spec.json'),
        ('plan_binding',RUN/'iter_001/proposal_plan_binding.json'),('proposal_input',RUN/'iter_001/proposal_input.json'),
        ('proposal_outcome',RUN/'iter_001/proposal_outcome.json'),('saved_winner',saved)]
for name,p in probes:
    assert p==saved or str(p.resolve()) in state['final_artifacts']
    data=p.read_bytes()
    try:
        p.write_bytes(data+b'\n ');codes[name]=invoke(name);assert codes[name]!=0
    finally:p.write_bytes(data)
    assert all(sha(Path(p))==h for p,h in before.items())
assert files=={str(p.relative_to(RUN)) for p in RUN.rglob('*') if p.is_file()}
assert all(sha(ROOT/p)==h for p,h in plan['runtime_source'].items())
result={'passed':True,'independent_exact_top_and_three_children':True,'independent_seconds':seconds,
    'checked_cycles':685,'protected_identities':len(before),'all_restored_unchanged':True,
    'budget_stats_and_file_set_unchanged':True,'no_new_model_or_optimization_tool_charges':True,
    'cli_exit_codes':codes,'best_metrics':summary['best_metrics'],'baseline_metrics':summary['baseline_metrics'],
    'budget':read(RUN/'budget.json'),'runtime_source_unchanged':True,'identities':before,
    'scope':'Actual DONE reuse/restored tamper and independent simulation; not arbitrary in-flight crash or formal proof'}
(OUT/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
manifest={p.relative_to(OUT).as_posix():sha(p) for p in OUT.rglob('*') if p.is_file() and 'xsim.dir' not in p.parts and '.Xil' not in p.parts}
(OUT/'archive-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='identities'}),flush=True)
