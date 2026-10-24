import hashlib,json,shutil,subprocess
from pathlib import Path
ROOT=Path('C:/Users/prince.baah/Downloads/autortl-work')
WORK=Path('C:/Users/prince.baah/Documents/Codex/2026-10-15/hey')
STAGE=WORK/'work/dot4-fixture-stage';RUN=ROOT/'logs/dot4-admission-01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=json.loads((RUN/'prelaunch-plan.json').read_text());result=json.loads((RUN/'result.json').read_text())
assert result['qualified'] and result['admitted']==result['executed']==13
assert all(sha(STAGE/p)==h for p,h in plan['stage_files'].items())
assert all(sha(ROOT/p)==h for p,h in plan['runtime_source'].items())
out=ROOT/'evidence/2026-10-24/dot4-admission-01';out.mkdir(parents=True,exist_ok=False)
allowed={'.v','.json','.jsonl','.py','.log','.txt','.rpt','.md','.yaml','.xdc','.tcl'}
for source,prefix in ((RUN,'admission'),(STAGE,'fixture')):
    for p in source.rglob('*'):
        rel=p.relative_to(source)
        if not p.is_file() or p.suffix not in allowed or any(x.lower() in ('artifacts','xsim.dir','.xil') for x in rel.parts):continue
        target=out/prefix/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
for p in (WORK/'work/admit_dot4.py',Path(__file__),WORK/'outputs/AutoRTL-dot4-admission-01.txt'):
    shutil.copyfile(p,out/p.name)
(out/'README.md').write_text('''# Three-module dot-product checker admission

Control PASS; all12 intended compiling behavioral faults produced actual
assertion failures.13/13 admitted in70.219seconds, no model calls or synthesis.
Sources and independent testbench stayed frozen; runtime203 hashes unchanged.
See admission/result.json for process exits and each named case.

The fixture/README is the original pre-admission proposal; the actual admission
result in this archive supersedes its historical not-yet-simulated status.
Reference children were used only to qualify the checker, never a generated
seed. This does not establish formal correctness or exhaustive fault coverage.
''',encoding='utf-8')
manifest={p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file()}
(out/'archive-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
assert all(sha(out/p)==h for p,h in manifest.items())
assert not (ROOT/'logs/build-dot4-01').exists()
build_plan={'schema_version':1,'task':'Fresh3child dot4 build: generated per-module Python goldens/RTL, mechanical wiring, admitted independent top TB',
    'runtime_source':plan['runtime_source'],'fixture_hashes':plan['stage_files'],
    'spec_path':str(STAGE/'design_spec.json'),'spec_sha256':sha(STAGE/'design_spec.json'),
    'tb_path':str(STAGE/'dot4_pipeline_tb.v'),'tb_sha256':sha(STAGE/'dot4_pipeline_tb.v'),
    'admission_archive':str(out),'admission_manifest_sha256':sha(out/'archive-manifest.json'),
    'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    'budgets':{'iterations':1,'best_of_n':1,'max_llm_calls':16,'max_tool_minutes':25,'max_wall_minutes':35,'infra_retries':1},
    'reference_is_not_a_generation_input':True,'model':'codex.default; actual identity unknown',
    'limits':'Initial composition/verification experiment; children frozen during top optimization, no arithmetic PPA gain promised',
    'after_run':'Independent exact winner plus frozen generated children; source/constraints/report binding and actual DONE child/spec integrity probes'}
target=ROOT/'logs/build-dot4-01-prelaunch.json';assert not target.exists()
target.write_text(json.dumps(build_plan,indent=2),encoding='utf-8')
print(json.dumps({'admission_files':len(manifest),'qualified':'13/13','build_predeclared':str(target)}))
