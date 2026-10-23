"""Post-run sensitivity measurement of the frozen generated default-width grader."""
import argparse,hashlib,json,shutil,sys,time
from pathlib import Path
ROOT=Path('C:/Users/prince.baah/Downloads/autortl-work')
WORK=Path('C:/Users/prince.baah/Documents/Codex/2026-10-15/hey/work')
sys.path.insert(0,str(ROOT))
from autortl.config import RunConfig
from autortl.vivado import xsim_run
from autortl.tbqual import assertion_failure_proof
from autortl.triage import FailureKind
p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args();run=a.run.resolve();out=a.output.resolve()
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
summary=json.loads((run/'run_summary.json').read_text());state=json.loads((run/'state.json').read_text())
assert summary['status']=='done' and state['phase']=='DONE','One vendor queue; wait for model run'
cfg=RunConfig.load(run/'config.json');tb=run/'modules/iterative_divider_core/iterative_divider_core_tb.v'
tb_hash=sha(tb);assert state['final_artifacts'][str(tb)]==tb_hash
qualification=ROOT/'logs/divider-qualification-02/results.json'
qualified={x['case']:x for x in json.loads(qualification.read_text())}
exclusions={name:'Equivalent to the control at default WIDTH=8; independently tested at parameter overrides.' for name in ('captured_dividend_truncated_eight','captured_divisor_truncated_eight','hardcoded_eight_iterations')}
assert len(qualified)==21 and set(exclusions)<=set(qualified)
names=[name for name in qualified if name not in exclusions]
sources=qualification.parent/'divider_cases'
for name in names:
    prior=qualified[name];source=sources/name/'iterative_divider_core.v'
    assert prior['ok'] and prior['source_sha256']['iterative_divider_core.v']==sha(source)
    assert prior['passed'] is True if name=='reference' else prior['assertion_detected'] and not prior['watchdog_or_timeout']
runtime=json.loads((run/'runtime.json').read_text())['implementation']
assert all(sha(ROOT/name)==h for name,h in runtime.items())
out.mkdir(parents=True,exist_ok=False)
(out/'provenance.json').write_text(json.dumps({'qualification':str(qualification),'qualification_sha256':sha(qualification),'completed_state_sha256':sha(run/'state.json'),'config_sha256':sha(run/'config.json'),'runtime_sha256':sha(run/'runtime.json'),'runtime_files':len(runtime),'runtime_matches_build':True,'generated_tb_sha256':tb_hash,'source_launch':json.loads((WORK/'divider-launch-source-01.json').read_text()),'selected_cases':names,'default_width_exclusions':exclusions},indent=2)+'\n')
rows=[];started=time.monotonic()
for name in names:
    work=out/name;work.mkdir();source=sources/name/'iterative_divider_core.v'
    dut=work/'iterative_divider_core.v';local_tb=work/'iterative_divider_core_tb.v'
    shutil.copyfile(source,dut);shutil.copyfile(tb,local_tb)
    assert sha(dut)==qualified[name]['source_sha256']['iterative_divider_core.v'] and sha(local_tb)==tb_hash
    case_start=time.monotonic()
    passed,error,kind=xsim_run([dut],local_tb,'iterative_divider_core_tb',cfg,work,timeout=60)
    detected,reason=assertion_failure_proof(work) if kind==FailureKind.DESIGN and not passed else (False,'passed' if passed else 'unestablished tool failure')
    raw=(work/'sim_log.txt').read_text(errors='replace') if (work/'sim_log.txt').exists() else ''
    control_ok=passed is True and kind==FailureKind.DESIGN and 'TEST PASSED' in raw and 'FAIL' not in raw
    outcome=('control_pass' if control_ok else 'control_failed') if name=='reference' else ('detected' if detected else 'missed' if passed else 'unestablished_failure')
    row={'case':name,'source_original':str(source),'source_sha256':sha(dut),'generated_tb_sha256':sha(local_tb),'passed':passed,'failure_kind':kind.value,'assertion_detected':bool(detected),'proof_reason':reason,'error':error[:2000],'outcome':outcome,'seconds':time.monotonic()-case_start}
    rows.append(row);(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps({k:row[k] for k in ('case','outcome','failure_kind')}),flush=True)
assert sha(tb)==tb_hash
result={'measurement_complete':len(rows)==len(names),'control_passed':rows[0]['outcome']=='control_pass','applicable_default_width_faults':len(names)-1,'detected':sum(x['assertion_detected'] for x in rows[1:]),'missed':[x['case'] for x in rows[1:] if x['outcome']=='missed'],'unestablished':[x['case'] for x in rows if x['outcome'] in ('control_failed','unestablished_failure')],'default_width_exclusions':exclusions,'seconds':time.monotonic()-started,'scope':'Supplemental default WIDTH8 generated-grader measurement against prequalified source faults; no original run regrading or runtime change. Independent exact schedule/parameter/reset checker remains required.'}
result['measurement_valid']=result['measurement_complete'] and result['control_passed'] and not result['unestablished']
(out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
manifest={x.relative_to(out).as_posix():sha(x) for x in sorted(out.rglob('*')) if x.is_file() and not any(v in x.relative_to(out).parts for v in ('xsim.dir','.Xil'))}
(out/'archive-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(result),flush=True)
raise SystemExit(0 if result['measurement_valid'] else 1)
