"""Controlled same-oracle/reference/mutant comparison, separate from old run."""
import hashlib,json,re,runpy,shutil,sys,time
from pathlib import Path
R=Path('C:/Users/prince.baah/Downloads/autortl-work');W=Path(__file__).resolve().parent
OLD=R/'logs/build-signed-fir4-01';AUDIT=R/'evidence/2026-10-26/signed-fir4-generated-audit-01'
OUT=R/'logs/fir4-signed-boundary-comparison-01';sys.path.insert(0,str(R))
from autortl import tbgen
from autortl.golden import GoldenModel
from autortl.spec import DesignSpec
from autortl.config import RunConfig
from autortl.vivado import xsim_run
from autortl.contract_context import tool_exit_evidence
from scripts.check_build_tbs import verdict
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
identities=runpy.run_path(str(W/'validate_seed_binding_live.py'))['identities']
source=identities();assert len(source)==228
assert all(sha(AUDIT/p)==h for p,h in read(AUDIT/'archive-manifest.json').items())
oldrows={v['name']:v for v in read(AUDIT/'audit/result.json')['results']}
assert oldrows['reference']['grade']=='control_passed' and oldrows['truncate12']['grade']=='missed'
before=read(AUDIT/'audit/prelaunch-plan.json')['original_identities']
assert all(sha(Path(p))==h for p,h in before.items())
oldfiles={str(p.relative_to(OLD)) for p in OLD.rglob('*') if p.is_file()}
assert not OUT.exists();OUT.mkdir(parents=True)
module=DesignSpec.load(R/'curriculum/tier3/signed_fir4_build/design_spec.json').modules[0]
original=OLD/'modules/signed_fir4_core';goldenpath=OUT/'golden.py';shutil.copyfile(original/'golden.py',goldenpath)
golden=GoldenModel(goldenpath);golden.work_parent=OUT
tb=tbgen.generate(module,golden,OUT/'generated',n_random=100,seed=1234)
oldstim=read(original/'stimulus.json');newstim=read(OUT/'generated/stimulus.json')
oldn=len(oldstim['stimulus']);assert oldn==104 and len(newstim['stimulus'])==oldn+6
assert newstim['stimulus'][:oldn-100]==oldstim['stimulus'][:-100]
assert newstim['stimulus'][-100:]==oldstim['stimulus'][-100:]
signed=lambda rows:[r['out_data']-8192 if r['out_data']>=4096 else r['out_data'] for r in rows]
values=signed(newstim['expected']);assert -2169 in values and 2166 in values
variants=runpy.run_path(str(R/'curriculum/tier3/signed_fir4_build/qualification/cases.py'))['case_sources']()
plan={'runtime_source':source,'same_golden_sha256':sha(goldenpath),'old_generated_TB_sha256':sha(original/'signed_fir4_core_tb.v'),
      'new_generated_TB_sha256':sha(tb),'old_stimulus_sha256':sha(original/'stimulus.json'),'new_stimulus_sha256':sha(OUT/'generated/stimulus.json'),
      'old_reference':oldrows['reference'],'old_truncate12':oldrows['truncate12'],'original_identities':before,
      'scope':'Only signed accepted payload burst changed; same frozen generated oracle and exact reference/truncate12 RTL; no model/synthesis calls or original-run regrade'}
(OUT/'prelaunch-plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
cfg=RunConfig.load(OLD/'config.json');rows=[];tick=time.monotonic()
for name in ('reference','truncate12'):
    directory=OUT/name;directory.mkdir();child=directory/'children.v';child.write_bytes(variants[name].encode('utf-8'))
    assert sha(child)==sha(AUDIT/f'audit/{name}/children.v')
    copied=directory/tb.name;shutil.copyfile(tb,copied);inputs={str(p):sha(p) for p in (child,copied)}
    okay,error,kind=xsim_run([child],copied,'signed_fir4_core_tb',cfg,directory,timeout=90)
    exits=tool_exit_evidence(directory);raw=(directory/'sim_log.txt').read_text(encoding='utf-8',errors='replace')
    actual_exits=exits['schema_valid'] and all(exits['latest_by_tool'].get(k,{}).get('successful') for k in ('xvlog','xelab','xsim'))
    strict=verdict(name=='reference',okay,error,kind,raw)
    row={'name':name,'passed_expected_verdict':bool(strict['ok'] and actual_exits),'simulation_passed':okay,'error':error,'kind':kind.value,
         'actual_tool_exits':actual_exits,'process_exits':exits,'verdict':strict,'inputs':inputs,
         'assertions':re.findall(r'(?m)^\s*FAIL\b[^\n]*',raw)}
    rows.append(row);(directory/'result.json').write_text(json.dumps(row,indent=2),encoding='utf-8')
    assert all(sha(Path(p))==h for p,h in inputs.items())
    print(json.dumps({k:v for k,v in row.items() if k in ('name','passed_expected_verdict','simulation_passed','error')}),flush=True)
assert identities()==source and all(sha(Path(p))==h for p,h in before.items())
assert oldfiles=={str(p.relative_to(OLD)) for p in OLD.rglob('*') if p.is_file()}
result={'passed':all(r['passed_expected_verdict'] for r in rows),'old_reference_passed':True,'old_truncate12_missed':True,
        'new_reference_passed':rows[0]['simulation_passed'],'new_truncate12_detected':rows[1]['passed_expected_verdict'],
        'same_golden_reference_mutant':True,'original_run_budget_stats_files_unchanged':True,'source228_unchanged':True,
        'old_payloads':104,'new_payloads':110,'old_expected_min':min(signed(oldstim['expected'])),'old_expected_max':max(signed(oldstim['expected'])),
        'new_expected_min':min(values),'new_expected_max':max(values),'original_prefix_and_random_input_tail_preserved':True,
        'model_calls':0,'synthesis_calls':0,'elapsed_seconds':time.monotonic()-tick,'results':rows}
(OUT/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='results'}),flush=True);assert result['passed']
