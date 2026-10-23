"""Controlled regenerated-grader experiment; never resume/regrade original FSM."""
import hashlib,json,shutil,sys,time
from pathlib import Path
ROOT=Path('C:/Users/prince.baah/Downloads/autortl-work')
sys.path.insert(0,str(ROOT))
from autortl.config import RunConfig
from autortl.spec import DesignSpec
from autortl.golden import GoldenModel
from autortl.tbgen import generate
from autortl.vivado import xsim_run
from autortl.tbqual import assertion_failure_proof
from autortl.triage import FailureKind
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
run=ROOT/'logs/build-golden-divider-01';out=ROOT/'logs/scoreboard-example-coverage-01'
state=json.loads((run/'state.json').read_text());assert state['phase']=='DONE'
protected={Path(p):h for p,h in state['final_artifacts'].items()}
protected.update({run/name:sha(run/name) for name in ('state.json','runtime.json','config.json','budget.json','run_summary.json')})
assert all(sha(p)==h for p,h in protected.items())
old_runtime=json.loads((run/'runtime.json').read_text())['implementation']
runtime={p:sha(ROOT/p) for p in old_runtime}
assert [p for p,h in old_runtime.items() if runtime[p]!=h]==['autortl/tbgen.py']
spec_path=run/'design_spec.json';spec=DesignSpec.load(spec_path).modules[0]
oracle=run/'modules/iterative_divider_core/golden.py'
old_tb=run/'modules/iterative_divider_core/iterative_divider_core_tb.v'
oracle_receipt=oracle.parent/'golden_attempt_2.log'
oracle_proof=json.loads(oracle_receipt.read_text())
archived=ROOT/'evidence/2026-10-23/generated-divider-attempt-01'
archive_manifest=json.loads((archived/'archive-manifest.json').read_text())
archive_key='build-golden-divider-01/modules/iterative_divider_core/golden.py'
assert oracle_proof['status']=='oracle_qualified'
assert sha(oracle)==oracle_proof['source_sha256']==archive_manifest[archive_key]==sha(archived/archive_key)
assert old_tb in protected
# Completed optimization freezes the rendered TB; qualify the frozen oracle
# separately against its original receipt and immutable published archive.
protected[oracle]=sha(oracle);protected[oracle_receipt]=sha(oracle_receipt)
qualification=ROOT/'logs/divider-qualification-02/results.json'
prior={x['case']:x for x in json.loads(qualification.read_text())}
assert all(x['ok'] for x in prior.values())
excluded={'captured_dividend_truncated_eight','captured_divisor_truncated_eight','hardcoded_eight_iterations'}
selected=[name for name in prior if name not in excluded]
out.mkdir(parents=True,exist_ok=False)
new_tb=generate(spec,GoldenModel(oracle),out/'generated',n_random=100,seed=1234)
stimulus=json.loads((out/'generated/stimulus.json').read_text())['stimulus']
assert {'dividend':255,'divisor':0} in stimulus
cfg=RunConfig.load(run/'config.json');sources=qualification.parent/'divider_cases'
rows=[];started=time.monotonic()
def simulate(label,name,tb):
    work=out/label;work.mkdir()
    source=sources/name/'iterative_divider_core.v'
    assert sha(source)==prior[name]['source_sha256']['iterative_divider_core.v']
    dut=work/'iterative_divider_core.v';local_tb=work/'iterative_divider_core_tb.v'
    shutil.copyfile(source,dut);shutil.copyfile(tb,local_tb)
    passed,error,kind=xsim_run([dut],local_tb,'iterative_divider_core_tb',cfg,work,timeout=60)
    detected,proof=assertion_failure_proof(work) if kind==FailureKind.DESIGN and not passed else (False,'passed' if passed else 'unestablished tool failure')
    raw=(work/'sim_log.txt').read_text(errors='replace') if (work/'sim_log.txt').exists() else ''
    control_ok=passed is True and kind==FailureKind.DESIGN and 'TEST PASSED' in raw and 'FAIL' not in raw
    row={'label':label,'case':name,'passed':passed,'control_ok':control_ok,'failure_kind':kind.value,'assertion_detected':bool(detected),'proof':proof,'error':error[:2000],'source_sha256':sha(dut),'tb_sha256':sha(local_tb)}
    rows.append(row);(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps({k:row[k] for k in ('label','passed','assertion_detected','failure_kind')}),flush=True)
    return row
old_control=simulate('old_control','reference',old_tb)
old_fault=simulate('old_zero_remainder','zero_divisor_remainder_zero',old_tb)
assert old_control['control_ok'] and old_fault['passed'] is True
fresh=[simulate('new_'+name,name,new_tb) for name in selected]
assert fresh[0]['control_ok']
target=next(x for x in fresh if x['case']=='zero_divisor_remainder_zero')
assert target['assertion_detected'] and 'signal=remainder' in target['error']
unestablished=[x['case'] for x in fresh[1:] if not x['passed'] and not x['assertion_detected']]
assert not unestablished,unestablished
assert all(sha(p)==h for p,h in protected.items()),'Original completed run modified'
old_stim=json.loads((run/'modules/iterative_divider_core/stimulus.json').read_text())['stimulus']
result={'ok':True,'original_miss_reproduced':True,'old_and_new_control_passed':True,'unchanged_zero_remainder_fault_now_asserted':True,'new_faults_detected':sum(x['assertion_detected'] for x in fresh[1:]),'applicable_default_width_faults':len(fresh)-1,'remaining_misses':[x['case'] for x in fresh[1:] if x['passed']],'default_width_exclusions':sorted(excluded),'old_stimulus_count':len(old_stim),'new_stimulus_count':len(stimulus),'new_zero_divisor_vectors':[x for x in stimulus if x['divisor']==0],'runtime_changes':['autortl/tbgen.py'],'original_completed_run_protected_hashes_unchanged':len(protected),'original_state_and_budget_unchanged':True,'elapsed_seconds':time.monotonic()-started,'scope':'Regenerated scoreboard payload coverage with frozen original oracle/spec/RTL faults; no model call, original FSM resume, PPA remeasurement or example-timing replay.'}
(out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
(out/'provenance.json').write_text(json.dumps({'oracle_original':str(oracle),'oracle_sha256':sha(oracle),'spec_original':str(spec_path),'spec_sha256':sha(spec_path),'old_tb_sha256':sha(old_tb),'new_tb_sha256':sha(new_tb),'qualification_sha256':sha(qualification),'old_runtime':old_runtime,'measured_runtime':runtime},indent=2)+'\n')
manifest={p.relative_to(out).as_posix():sha(p) for p in sorted(out.rglob('*')) if p.is_file() and not any(x in p.relative_to(out).parts for x in ('xsim.dir','.Xil'))}
(out/'archive-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(result),flush=True)
