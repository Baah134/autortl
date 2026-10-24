"""Finish evidence checks after the observer's console encoding error; no optimization rerun."""
import hashlib,json,re,runpy,subprocess,sys,time
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8',errors='replace')
ROOT=Path('C:/Users/prince.baah/Downloads/autortl-work')
WORK=Path('C:/Users/prince.baah/Documents/Codex/2026-10-15/hey')
RUN=ROOT/'logs/seed-binding-live-01';out=RUN/'quota-recovery'
assert not (out/'result.json').exists()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
h=runpy.run_path(str(WORK/'work/validate_seed_binding_live.py'))
plan=read(RUN/'prelaunch-plan.json');summary=read(RUN/'run_summary.json')
assert summary['status']=='done' and read(RUN/'state.json')['phase']=='DONE'
assert h['identities']()==plan['runtime_source']
assert sha(Path(plan['seed_path']))==plan['seed_sha256'] and sha(Path(plan['testbench_path']))==plan['testbench_sha256']
assert (out/'before-validation-result.json').read_bytes()==(RUN/'validation-result.json').read_bytes()
assert read(RUN/'config.json')==read(out/'before-config.json')
before=read(out/'before-budget.json');after=read(RUN/'budget.json')
assert all(after[k]>=before[k] for k in ('llm_calls','vivado_seconds','elapsed'))
stats=ROOT/'llm/router_stats.jsonl';data=stats.read_bytes()
original=(RUN/'validation-router-stats.jsonl').read_bytes()
assert original and data.count(original)==1
new=data[data.index(original)+len(original):]
records=[json.loads(line) for line in new.splitlines() if line.strip()]
assert len(records)==after['llm_calls']-before['llm_calls']
(out/'new-router-stats.jsonl').write_bytes(new)
# Establish an actual completed-run CLI exit independently of the observer error.
process=subprocess.run([sys.executable,'-u','run.py','resume','--run',str(RUN)],cwd=ROOT,
    stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
(out/'completed-cli-reuse.txt').write_text(process.stdout,encoding='utf-8')
assert process.returncode==0 and stats.read_bytes()==data and read(RUN/'budget.json')==after
audit=h['audit_bindings'](RUN,h['text_sha'](Path(plan['seed_path']).read_text(encoding='utf-8')))
(out/'binding-audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
assert audit['passed']
sys.path.insert(0,str(ROOT))
from autortl.config import RunConfig
from autortl.vivado import xsim_run
from autortl.triage import FailureKind
from autortl.contract_context import tool_exit_evidence
cfg=RunConfig.load(RUN/'config.json')
directory=out/'independent';directory.mkdir(exist_ok=False)
saved=RUN/'iterative_divider_core_best.v';assert sha(saved)==read(RUN/'state.json')['best_sha256']
copied=directory/'winner.v';copied.write_bytes(saved.read_bytes())
tb=directory/'tb.v';tb.write_bytes(Path(plan['testbench_path']).read_bytes())
immutable={str(p):sha(p) for p in (saved,copied,tb)}
start=time.monotonic()
okay,error,kind=xsim_run([copied],tb,'iterative_divider_core_tb',cfg,directory,timeout=90)
seconds=time.monotonic()-start
raw=(directory/'sim_log.txt').read_text(errors='replace');exits=tool_exit_evidence(directory)
exit_ok=exits['schema_valid'] and all(exits['latest_by_tool'].get(t,{}).get('successful') for t in ('xvlog','xelab','xsim'))
independent={'passed':bool(okay and kind==FailureKind.DESIGN and exit_ok and sha(saved)==sha(copied)
    and all(sha(Path(p))==v for p,v in immutable.items()) and re.search(r'(?m)^\s*TEST PASSED\s*$',raw)
    and not re.search(r'FAIL|watchdog|timeout|timed\s+out',raw,re.I)),
    'identities':immutable,'process_exits':exits,'error':error}
(directory/'result.json').write_text(json.dumps(independent,indent=2),encoding='utf-8')
names=('input_tokens','cached_input_tokens','output_tokens')
usage={k:sum((r.get('metadata',{}).get('usage') or {}).get(k,0) for r in records)
       if all(type((r.get('metadata',{}).get('usage') or {}).get(k)) is int for r in records) else None for k in names}
result={'scope':'Supplemental same-runtime quota recovery; original blocked result retained; observer print failed after optimization completed',
    'status':summary['status'],'initial_optimization_cli_exit':None,'completed_cli_reuse_exit':process.returncode,
    'observer_error':'UnicodeEncodeError printing captured output; original resume-console retained',
    'resume_seconds':None,'budget_before':before,'budget_after':after,'no_budget_reset':True,
    'original_blocked_result_unchanged':True,'runtime_source_unchanged':h['identities']()==plan['runtime_source'],
    'binding_audit':{k:audit[k] for k in ('binding_invariant_passed','corrected_path_exercised','changed_seed_refreshes_exercised','unbound_generated_inputs')},
    'independent':independent,'independent_seconds':seconds,'new_calls_reported_usage':usage,
    'original_failed_call_usage_known':False,'total_usage':None,
    'best_metrics':summary['best_metrics'],'baseline_metrics':summary['baseline_metrics']}
result['passed']=audit['passed'] and independent['passed'] and result['runtime_source_unchanged']
(out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='independent'}),flush=True)
assert result['passed']
