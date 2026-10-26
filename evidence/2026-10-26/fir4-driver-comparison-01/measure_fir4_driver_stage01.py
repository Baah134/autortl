"""Serial legal-driver controls, bad-driver probe and full frozen FIR fault audit."""
import hashlib,json,re,runpy,shutil,subprocess,sys,time,traceback
from pathlib import Path
R=Path('C:/Users/prince.baah/Downloads/autortl-work');W=Path(__file__).resolve().parent
S=W/'fir4-driver-stage';OLD=R/'logs/build-signed-fir4-01'
OUT=R/'logs/fir4-driver-comparison-01';sys.path.insert(0,str(S));sys.dont_write_bytecode=True
import autortl
from autortl import tbgen
from autortl.config import RunConfig
from autortl.golden import GoldenModel
from autortl.spec import DesignSpec
from autortl.vivado import xsim_run
from autortl.contract_context import tool_exit_evidence
from autortl.triage import FailureKind
from scripts.check_build_tbs import verdict
from tests import scoreboard_driver_live_cases as live
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.write_text(json.dumps(v,indent=2),encoding='utf-8')
def sources(root):
    found={}
    for name in ('autortl','llm','tests','curriculum','scripts','data','.claude'):
        for p in (root/name).rglob('*'):
            if p.is_file() and p.suffix in ('.py','.v','.sv','.json','.yaml','.md') and '__pycache__' not in p.parts:
                found[p.relative_to(root).as_posix()]=sha(p)
    found['run.py']=sha(root/'run.py');return found
assert Path(autortl.__file__).resolve().is_relative_to(S)
focus=read(S/'focused-tests-result.json');assert focus['exit_code']==0 and focus['passed']==117
assert sha(S/'focused-tests.txt')==focus['focused_log_sha256']
assert sha(S/'old-driver-regression.txt')==focus['pre_patch']['old_log_sha256']
canonical=sources(R);staged=sources(S);assert len(canonical)==228 and len(staged)==230
assert canonical==read(S/'original-source228.json')
assert {p for p in canonical if canonical[p]!=staged[p]}=={'autortl/tbgen.py'}
assert set(staged)-set(canonical)==set(focus['new_files'])
assert all(sha(S/p)==h for p,h in focus['new_files'].items())
assert sha(S/'autortl/tbgen.py')==focus['changes']['autortl/tbgen.py']['staged_sha256']
old_audit=R/'evidence/2026-10-26/signed-fir4-generated-audit-01'
signed=R/'evidence/2026-10-26/fir4-signed-boundary-comparison-01'
for archive in (old_audit,signed):assert all(sha(archive/p)==h for p,h in read(archive/'archive-manifest.json').items())
protected=read(old_audit/'audit/prelaunch-plan.json')['original_identities']
assert all(sha(Path(p))==h for p,h in protected.items())
oldfiles={str(p.relative_to(OLD)) for p in OLD.rglob('*') if p.is_file()}
assert not OUT.exists();OUT.mkdir(parents=True)
controls=live.save(OUT/'controls');assert len(controls)==5
base=next(row for row in controls if row['name']=='prolonged_block')
probe=OUT/'producer_probe';probe.mkdir()
probe_source=probe/'dut.v';shutil.copyfile(base['source_paths'][0],probe_source)
probe_tb=probe/'tb.v';text=Path(base['tb_path']).read_text(encoding='utf-8')
anchor='if (!_autortl_input_stalled) begin';assert text.count(anchor)==1
replacement="#0; if (!(in_valid === 1'b1 && in_ready === 1'b0)) begin"
probe_tb.write_bytes(text.replace(anchor,replacement,1).encode('utf-8'))
probe_row={**base,'source_paths':[str(probe_source)],'tb_path':str(probe_tb),
           'files':{str(p):sha(p) for p in (probe_source,probe_tb)}}
assert sha(probe_source)==sha(Path(base['source_paths'][0]))
module=DesignSpec.load(S/'curriculum/tier3/signed_fir4_build/design_spec.json').modules[0]
goldenpath=OUT/'golden.py';shutil.copyfile(OLD/'modules/signed_fir4_core/golden.py',goldenpath)
golden=GoldenModel(goldenpath);golden.work_parent=OUT
fir_tb=tbgen.generate(module,golden,OUT/'generated',n_random=100,seed=1234)
assert (OUT/'generated/stimulus.json').read_bytes()==(signed/'comparison/generated/stimulus.json').read_bytes()
variants=runpy.run_path(str(S/'curriculum/tier3/signed_fir4_build/qualification/cases.py'))['case_sources']()
assert len(variants)==28 and next(iter(variants))=='reference'
variant_hash={n:hashlib.sha256(v.encode('utf-8')).hexdigest() for n,v in variants.items()}
for n,h in variant_hash.items():assert sha(old_audit/f'audit/{n}/children.v')==h
cfg=RunConfig.load(OLD/'config.json')
plan={'canonical_source':canonical,'staged_source':staged,'stage_focus_receipt_sha256':sha(S/'focused-tests-result.json'),
      'original_identities':protected,'original_file_set':sorted(oldfiles),'helper_sha256':sha(Path(__file__)),
      'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),
      'python_version':sys.version,'python_executable_sha256':sha(Path(sys.executable)),
      'same_golden_sha256':sha(goldenpath),'signed_only_stimulus_sha256':sha(signed/'comparison/generated/stimulus.json'),
      'new_stimulus_sha256':sha(OUT/'generated/stimulus.json'),'new_FIR_TB_sha256':sha(fir_tb),
      'case_child_sha256':variant_hash,'planned_nominal_controls':5,'planned_fir_faults':27,
      'producer_probe':{'change':replacement,'replaces':anchor,'same_DUT':True,'not_a_DUT_mutant':True},
      'scope':'Typed-safe driver scheduling only; same signed-only110payloads/expected arrays and frozen oldoracle/reference/all27faults. No models/synthesis or originalrun regrade.'}
write(OUT/'prelaunch-plan.json',plan)
def invariants():
    return sources(R)==canonical and sources(S)==staged and all(sha(Path(p))==h for p,h in protected.items()) and oldfiles=={str(p.relative_to(OLD)) for p in OLD.rglob('*') if p.is_file()}
def simulate(directory,source_paths,tb,top,expected_control,input_hashes):
    tick=time.monotonic();okay,error,kind=xsim_run([Path(p) for p in source_paths],Path(tb),top,cfg,directory,timeout=90)
    exits=tool_exit_evidence(directory);raw=(directory/'sim_log.txt').read_text(encoding='utf-8',errors='replace') if (directory/'sim_log.txt').exists() else ''
    actual=exits['schema_valid'] and all(exits['latest_by_tool'].get(t,{}).get('successful') for t in ('xvlog','xelab','xsim'))
    inputs_ok=all(sha(Path(p))==h for p,h in input_hashes.items())
    strict=verdict(expected_control,okay,error,kind,raw)
    row={'simulation_passed':okay,'error':error,'kind':kind.value,'process_exits':exits,'actual_exits':bool(actual),
         'input_hashes':input_hashes,'inputs_unchanged':inputs_ok,'strict_verdict':strict,'elapsed_seconds':time.monotonic()-tick,
         'assertions':re.findall(r'(?m)^\s*FAIL\b[^\n]*',raw)}
    row['valid_verdict']=bool(actual and inputs_ok and kind==FailureKind.DESIGN and strict['ok'])
    assert invariants(),'Protected source/originalrun drift'
    return row,raw
rows=[];control_rows=[];probe_result=None;fatal=None;start=time.monotonic()
try:
    for control in controls:
        directory=Path(control['tb_path']).parent
        row,raw=simulate(directory,control['source_paths'],control['tb_path'],control['top'],True,control['files'])
        coverage=live.coverage_verdict(raw,control);row.update({'name':control['name'],'coverage':coverage,'passed':row['valid_verdict'] and coverage['ok']})
        write(directory/'result.json',row);control_rows.append(row);write(OUT/'control-results.json',control_rows)
        print(json.dumps({'control':control['name'],'passed':row['passed'],'coverage':coverage}),flush=True)
        assert row['passed'],'Preserve failed legal control before correction'
    row,raw=simulate(probe,probe_row['source_paths'],probe_tb,probe_row['top'],False,probe_row['files'])
    coverage=live.coverage_verdict(raw,probe_row)
    qualified=bool(row['valid_verdict'] and coverage['counts'].get('producer_errors',0)>0 and coverage['counts'].get('timing_errors',-1)==0 and 'FAIL DRIVER producer changed blocked offer' in raw)
    probe_result={**row,'coverage':coverage,'bad_driver_detected':qualified,'not_a_DUT_fault':True}
    write(probe/'result.json',probe_result);print(json.dumps({'bad_driver_probe_detected':qualified,'producer_errors':coverage['counts'].get('producer_errors')}),flush=True)
    assert qualified,'Producer monitor must detect the predeclared bad-driver probe'
    for name,text in variants.items():
        directory=OUT/'audit'/name;directory.mkdir(parents=True)
        child=directory/'children.v';child.write_bytes(text.encode('utf-8'));tb=directory/fir_tb.name;shutil.copyfile(fir_tb,tb)
        hashes={str(p):sha(p) for p in (child,tb)}
        row,raw=simulate(directory,[str(child)],tb,'signed_fir4_core_tb',name=='reference',hashes)
        clean=verdict(True,row['simulation_passed'],row['error'],FailureKind(row['kind']),raw)['ok']
        grade=('control_passed' if row['valid_verdict'] else 'control_failed') if name=='reference' else ('detected' if row['valid_verdict'] else ('missed' if row['actual_exits'] and clean else 'ungraded'))
        row.update({'name':name,'grade':grade});rows.append(row);write(directory/'result.json',row);write(OUT/'audit-results.json',rows)
        print(json.dumps({'fault':name,'grade':grade,'assertions':len(row['assertions'])}),flush=True)
        if name=='reference':assert grade=='control_passed','Reference must pass before grading mutants'
except BaseException:fatal=traceback.format_exc();(OUT/'fatal.txt').write_text(fatal,encoding='utf-8')
names={k:[r['name'] for r in rows[1:] if r['grade']==k] for k in ('detected','missed','ungraded')}
intact=invariants()
complete=len(control_rows)==5 and all(r['passed'] for r in control_rows) and probe_result and probe_result['bad_driver_detected'] and len(rows)==28 and rows[0]['grade']=='control_passed' and not names['ungraded'] and not fatal and intact
result={'status':'completed' if complete else 'incomplete','nominal_controls':len(control_rows),'nominal_controls_passed':sum(r['passed'] for r in control_rows),
        'bad_driver_probe_detected':bool(probe_result and probe_result['bad_driver_detected']),'reference_passed':bool(rows and rows[0]['grade']=='control_passed'),
        'planned_faults':27,'executed_faults':max(0,len(rows)-1),'detected':len(names['detected']),'missed':len(names['missed']),
        'ungraded':len(names['ungraded'])+27-max(0,len(rows)-1),'detected_names':names['detected'],'missed_names':names['missed'],'ungraded_names':names['ungraded'],
        'canonical228_stage230_originalrun_budget_stats_unchanged':intact,'payload_expected_arrays_unchanged_from_signed_only':True,
        'model_calls':0,'synthesis_calls':0,'elapsed_seconds':time.monotonic()-start,'fatal':fatal,
        'controls':control_rows,'producer_probe':probe_result,'audit':rows}
write(OUT/'result.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('controls','producer_probe','audit')}),flush=True)
assert complete,'Preserve all original results before any correction'
