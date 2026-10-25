import hashlib,json,subprocess
from pathlib import Path
ROOT=Path('C:/Users/prince.baah/Downloads/autortl-work');WORK=Path('C:/Users/prince.baah/Documents/Codex/2026-10-15/hey')
STAGE=WORK/'work/elastic-dot4-stage';admission=ROOT/'evidence/2026-10-25/elastic-dot4-admission-attempt-02'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((admission/'archive-manifest.json').read_text());assert all(sha(admission/p)==h for p,h in manifest.items())
result=json.loads((admission/'admission/result.json').read_text());assert result['qualified'] and result['admitted']==19
plan=json.loads((admission/'admission/prelaunch-plan.json').read_text())
assert all(sha(STAGE/p)==h for p,h in plan['stage_files'].items())
assert all(sha(ROOT/p)==h for p,h in plan['runtime_source'].items())
assert not (ROOT/'logs/build-elastic-dot4-01').exists()
target=ROOT/'logs/build-elastic-dot4-01-prelaunch.json';assert not target.exists()
target.write_text(json.dumps({'schema_version':1,'task':'Fresh elastic arithmetic pipeline:2slots/capacity2,readyvalid,age2,generatedgolden+RTL and independentlyadmittedTB',
    'runtime_source':plan['runtime_source'],'fixture_hashes':plan['stage_files'],
    'spec_path':str(STAGE/'design_spec.json'),'spec_sha256':sha(STAGE/'design_spec.json'),
    'tb_path':str(STAGE/'elastic_dot4_tb.v'),'tb_sha256':sha(STAGE/'elastic_dot4_tb.v'),
    'admission_archive':str(admission),'admission_manifest_sha256':sha(admission/'archive-manifest.json'),
    'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    'budgets':{'iterations':3,'best_of_n':1,'model_calls':16,'tool_minutes':25,'wall_minutes':35,'infra_retries':1},
    'reference_is_not_a_generation_input':True,'model':'codex.default; actual identity unknown',
    'after_run':'Independent exacttop+frozenchild; actualDONE source/spec/binding probes; allfailures retained'},indent=2),encoding='utf-8')
print(json.dumps({'prelaunch':str(target),'admitted':'19/19','runtime_files':len(plan['runtime_source'])}))
