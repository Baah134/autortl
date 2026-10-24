"""Supplemental same-runtime quota recovery; retain the original blocked trial."""
import hashlib,json,os,re,runpy,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path('C:/Users/prince.baah/Downloads/autortl-work')
WORK=Path('C:/Users/prince.baah/Documents/Codex/2026-10-15/hey')
RUN=ROOT/'logs/seed-binding-live-01'
helper=runpy.run_path(str(WORK/'work/validate_seed_binding_live.py'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
plan=read(RUN/'prelaunch-plan.json')
assert helper['identities']()==plan['runtime_source']
assert sha(WORK/'work/validate_seed_binding_live.py')==plan['helper_sha256']
assert read(RUN/'run_summary.json')['error_code']=='CODEX_QUOTA'
assert read(RUN/'state.json')['phase']=='MODEL_BLOCKED'
assert read(RUN/'validation-result.json')['status']=='model_blocked'
old_result_sha=sha(RUN/'validation-result.json')
budget_before=read(RUN/'budget.json');config_before=read(RUN/'config.json')
assert budget_before['llm_calls']==1
archive=ROOT/'evidence/2026-10-24/seed-binding-quota-block-01'
assert not archive.exists()
archive.mkdir(parents=True)
allowed={'.v','.sv','.py','.json','.jsonl','.log','.txt','.rpt','.md','.yaml','.xdc','.tcl'}
for path in sorted(RUN.rglob('*')):
    rel=path.relative_to(RUN)
    if not path.is_file() or path.suffix not in allowed or any(s.lower() in ('artifacts','xsim.dir','.xil') for s in rel.parts):continue
    dest=archive/'run'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
for path in (WORK/'work/validate_seed_binding_live.py',Path(__file__),WORK/'outputs/AutoRTL-seed-binding-live-01.txt'):
    shutil.copyfile(path,archive/path.name)
manifest={p.relative_to(archive).as_posix():sha(p) for p in archive.rglob('*') if p.is_file()}
(archive/'archive-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
assert all(sha(archive/p)==h for p,h in manifest.items())
recovery=RUN/'quota-recovery';recovery.mkdir(exist_ok=False)
for name in ('budget.json','config.json','runtime.json','state.json','run_summary.json','validation-result.json'):
    shutil.copyfile(RUN/name,recovery/('before-'+name))
stats=ROOT/'llm/router_stats.jsonl';before_stats=stats.read_bytes()
print(json.dumps({'blocked_archive_files':len(manifest),'budget_before':budget_before,'action':'same-runtime CLI resume, no budget reset'}),flush=True)
start=time.monotonic()
process=subprocess.run([sys.executable,'-u','run.py','resume','--run',str(RUN)],cwd=ROOT,
    stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
(recovery/'resume-console.txt').write_text(process.stdout,encoding='utf-8')
print(process.stdout,flush=True)
elapsed=time.monotonic()-start
after_stats=stats.read_bytes();assert after_stats.startswith(before_stats)
(recovery/'new-router-stats.jsonl').write_bytes(after_stats[len(before_stats):])
budget_after=read(RUN/'budget.json')
assert read(RUN/'config.json')==config_before
assert budget_after['llm_calls']>=budget_before['llm_calls']
assert budget_after['vivado_seconds']>=budget_before['vivado_seconds']
assert sha(RUN/'validation-result.json')==old_result_sha
audit=helper['audit_bindings'](RUN,helper['text_sha'](Path(plan['seed_path']).read_text(encoding='utf-8')))
(recovery/'binding-audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
summary=read(RUN/'run_summary.json')
independent={'passed':False,'attempted':False}
independent_start=time.monotonic()
if summary['status']=='done':
    sys.path.insert(0,str(ROOT))
    from autortl.config import RunConfig
    from autortl.vivado import xsim_run
    from autortl.triage import FailureKind
    from autortl.contract_context import tool_exit_evidence
    cfg=RunConfig.load(RUN/'config.json')
    saved=RUN/'iterative_divider_core_best.v'
    assert sha(saved)==read(RUN/'state.json')['best_sha256']
    directory=recovery/'independent';directory.mkdir()
    copied=directory/'winner.v';copied.write_bytes(saved.read_bytes())
    tb=directory/'tb.v';tb.write_bytes(Path(plan['testbench_path']).read_bytes())
    immutable={str(p):sha(p) for p in (saved,copied,tb)}
    okay,error,kind=xsim_run([copied],tb,'iterative_divider_core_tb',cfg,directory,timeout=90)
    raw=(directory/'sim_log.txt').read_text(errors='replace')
    exits=tool_exit_evidence(directory)
    exit_ok=exits['schema_valid'] and all(exits['latest_by_tool'].get(t,{}).get('successful') for t in ('xvlog','xelab','xsim'))
    unchanged=all(sha(Path(p))==h for p,h in immutable.items())
    independent={'attempted':True,'passed':bool(okay and kind==FailureKind.DESIGN and exit_ok and unchanged
        and sha(saved)==sha(copied) and re.search(r'(?m)^\s*TEST PASSED\s*$',raw)
        and not re.search(r'FAIL|watchdog|timeout|timed\s+out',raw,re.I)),
        'error':error,'process_exits':exits,'identities':immutable}
    (directory/'result.json').write_text(json.dumps(independent,indent=2),encoding='utf-8')
result={'scope':'Supplemental same-runtime recovery; original quota-blocked validation row retained, original total token usage unknown',
        'status':summary['status'],'cli_exit':process.returncode,'budget_before':budget_before,'budget_after':budget_after,
        'original_blocked_result_unchanged':sha(RUN/'validation-result.json')==old_result_sha,'no_budget_reset':True,
        'runtime_source_unchanged':helper['identities']()==plan['runtime_source'],
        'binding_audit':{k:audit[k] for k in ('binding_invariant_passed','corrected_path_exercised','changed_seed_refreshes_exercised','unbound_generated_inputs')},
        'independent':independent,'resume_seconds':elapsed,'independent_seconds':time.monotonic()-independent_start,
        'best_metrics':summary.get('best_metrics'),'baseline_metrics':summary.get('baseline_metrics')}
result['passed']=summary['status']=='done' and process.returncode==0 and audit['passed'] and independent['passed'] and result['runtime_source_unchanged']
(recovery/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result),flush=True)
assert result['passed'],'Retain failed or inconclusive recovery; never reset'
