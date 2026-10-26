import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--attempt',required=True);a=p.parse_args()
ROOT=Path('C:/Users/prince.baah/Downloads/autortl-work');WORK=Path('C:/Users/prince.baah/Documents/Codex/2026-10-15/hey')
STAGE=WORK/'work/signed-fir4-stage';run=ROOT/f'logs/signed-fir4-admission-{a.attempt}'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text(encoding='utf-8'))
plan=read(run/'prelaunch-plan.json');result=read(run/'result.json')
assert result['planned']==28 and 1<=result['executed']<=28 and all(result[k] for k in ('runtime_source_unchanged','stage_unchanged','router_stats_unchanged'))
assert all(sha(STAGE/p)==h for p,h in plan['stage_files'].items())
assert all(sha(ROOT/p)==h for p,h in plan['runtime_source'].items())
assert sha(WORK/'work/admit_signed_fir4.py')==plan['helper_sha256']
review_files=[WORK/'work/signed-fir4-review-correction.json',WORK/'work/signed-fir4-focus-01.txt',
              WORK/'work/signed-fir4-tests-stage/focused-tests-final.txt',
              WORK/'work/signed-fir4-tests-stage/focused-tests-final.json',
              WORK/'work/signed-fir4-tests-stage/tests/test_signed_fir4_fixture.py']
assert all(p.is_file() for p in review_files)
assert (WORK/f'outputs/AutoRTL-signed-fir4-admission-{a.attempt}.txt').is_file()
out=ROOT/f'evidence/2026-10-25/signed-fir4-admission-attempt-{a.attempt}';out.mkdir(parents=True,exist_ok=False)
for source,prefix in ((run,'admission'),(STAGE,'fixture'),(WORK/'work/signed-fir4-pre-review-01','pre-tool-review/original-stage')):
    for p in source.rglob('*'):
        rel=p.relative_to(source)
        if not p.is_file() or p.suffix not in ('.v','.py','.json','.jsonl','.log','.txt','.md','.yaml','.tcl','.xdc') or any(x.lower() in ('xsim.dir','.xil','artifacts','__pycache__') for x in rel.parts):continue
        target=out/prefix/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
for p in (WORK/'work/admit_signed_fir4.py',Path(__file__),WORK/f'outputs/AutoRTL-signed-fir4-admission-{a.attempt}.txt'):
    shutil.copyfile(p,out/p.name)
for p in review_files:
    target=out/'pre-tool-review'/p.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
classification='Qualified independent control plus27 actual behavior assertion faults' if result['qualified'] else 'Not admitted; original strict results preserved before correction'
(out/'README.md').write_text(f'''# Signed stateful FIR4 admission attempt{a.attempt}

{classification}. {result['admitted']}/{result['planned']} cases admitted;
{result['executed']} executed. No model or synthesis calls. See admission/result.json and raw
per-case receipts for exact outcomes; compiler/coverage failures never count as
behavioral kills. Inputs, stage and220 runtime identities stayed unchanged.
Binary simulator builds are excluded; outer archive-manifest defines preserved
files. This attempt is not rewritten after later checker instrumentation fixes.

Pre-tool review preserved the original stage and a real1failed/13passed focused
run that exposed incompatible failure-summary framing. Four reporting edits
fixed that syntax and classified setup coverage separately from internal
checker errors; predicates/stimulus stayed unchanged. The revised frozen
fixture then passed207focused tests before this actual vendor admission.
This selected fault set is not formal equivalence or an arbitrary-model claim.
''',encoding='utf-8')
manifest={p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file()}
(out/'archive-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
assert all(sha(out/p)==h for p,h in manifest.items())
print(json.dumps({'files':len(manifest),'qualified':result['qualified'],'admitted':result['admitted'],'planned':28}))
