"""Measure a frozen generated grader against prequalified named marker faults.

Standalone supervised experiment; no runtime changes, reference seeding or
retroactive alteration of the original build qualification.
"""
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT=Path('C:/Users/prince.baah/Downloads/autortl-work')
sys.path.insert(0,str(ROOT))
from autortl.config import RunConfig
from autortl.vivado import xsim_run
from autortl.tbqual import assertion_failure_proof
from autortl.triage import FailureKind

p=argparse.ArgumentParser()
p.add_argument('--run',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
run=a.run.resolve(); out=a.output.resolve()
summary=json.loads((run/'run_summary.json').read_text())
assert summary['status']=='done', 'Wait for original build to finish; one vendor queue'
cfg=RunConfig.load(run/'config.json')
tb=run/'modules/packet_fifo_core/packet_fifo_core_tb.v'
names=('reference','last_stuck_zero','last_stuck_one','current_input_last_bypass',
       'unaccepted_tag_write','displaced_tag_read','tag_only_stall_drift')
sources=ROOT/'logs/packet-fifo-qualification-01/packet_cases'
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
original_tb_hash=sha(tb)
qualification=ROOT/'logs/packet-fifo-qualification-01/results.json'
qualified={x['case']:x for x in json.loads(qualification.read_text())}
for name in names:
    prior=qualified[name]
    assert prior['ok'] and prior['source_sha256']['packet_fifo_core.v']==sha(sources/name/'packet_fifo_core.v'), 'Prequalified source drift: '+name
    assert (prior['passed'] is True) if name=='reference' else (prior['assertion_detected'] and not prior['watchdog_or_timeout']), 'Original qualification did not establish requested case'
state=json.loads((run/'state.json').read_text())
assert state['phase']=='DONE'
final=state['final_artifacts']
assert str(tb) in final and final[str(tb)]==original_tb_hash, 'Generated grader differs from original completed build identity'
runtime=json.loads((run/'runtime.json').read_text())['implementation']
assert all(sha(ROOT/path)==identity for path,identity in runtime.items()), 'Measured runtime source drift'
out.mkdir(parents=True,exist_ok=False)
(out/'provenance.json').write_text(json.dumps({'original_qualification':str(qualification),'original_qualification_sha256':sha(qualification),
    'original_completed_state_sha256':sha(run/'state.json'),'original_config_sha256':sha(run/'config.json'),
    'original_runtime_sha256':sha(run/'runtime.json'),'runtime_files':len(runtime),'runtime_matches_original_build':True,
    'launch_source':json.loads(Path('C:/Users/prince.baah/Documents/Codex/2026-10-15/hey/work/packet-launch-source-01.json').read_text()),
    'generated_tb_sha256':original_tb_hash,'selected_cases':list(names)},indent=2)+'\n')
rows=[]
for name in names:
    work=out/name; work.mkdir()
    source=sources/name/'packet_fifo_core.v'
    dut=work/'packet_fifo_core.v'; local_tb=work/'packet_fifo_core_tb.v'
    shutil.copyfile(source,dut); shutil.copyfile(tb,local_tb)
    assert sha(dut)==sha(source) and sha(local_tb)==original_tb_hash
    passed,error,kind=xsim_run([dut],local_tb,'packet_fifo_core_tb',cfg,work,timeout=60)
    detected,reason=assertion_failure_proof(work) if kind==FailureKind.DESIGN and not passed else (False,'control or mutant passed' if passed else 'infrastructure/compilation issue')
    raw=(work/'sim_log.txt').read_text(errors='replace') if (work/'sim_log.txt').is_file() else ''
    control_ok=(passed is True and kind==FailureKind.DESIGN and 'TEST PASSED' in raw and 'FAIL' not in raw)
    row={'case':name,'source_original':str(source),'source_sha256':sha(dut),
         'generated_tb_sha256':sha(local_tb),'passed':passed,'failure_kind':kind.value,
         'assertion_detected':bool(detected),'proof_reason':reason,'error':error[:2000],
         'outcome':('control_pass' if control_ok else 'control_failed') if name=='reference' else ('detected' if detected else 'missed' if passed else 'unestablished_failure')}
    rows.append(row)
    (out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps({k:row[k] for k in ('case','outcome','failure_kind')}),flush=True)
assert sha(tb)==original_tb_hash
result={'measurement_complete':len(rows)==7,'control_passed':rows[0]['outcome']=='control_pass',
        'named_marker_faults':6,'detected':sum(x['assertion_detected'] for x in rows[1:]),
        'missed':[x['case'] for x in rows[1:] if x['outcome']=='missed'],
        'unestablished':[x['case'] for x in rows if x['outcome'] in ('control_failed','unestablished_failure')],
        'scope':'Default WIDTH8 DEPTH3 generated transaction grader; independent six-configuration temporal grader results are separate. No original build regrading or runtime modification.',
        'generated_tb_original':str(tb),'generated_tb_sha256':original_tb_hash}
result['measurement_valid']=result['measurement_complete'] and result['control_passed'] and not result['unestablished']
(out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
manifest={f.relative_to(out).as_posix():sha(f) for f in sorted(out.rglob('*')) if f.is_file() and not any(x in f.relative_to(out).parts for x in ('xsim.dir','.Xil'))}
(out/'archive-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(result),flush=True)
raise SystemExit(0 if result['control_passed'] and not result['unestablished'] else 1)
