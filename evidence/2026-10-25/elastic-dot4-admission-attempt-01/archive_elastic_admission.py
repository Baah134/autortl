import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--attempt',required=True);a=p.parse_args()
ROOT=Path('C:/Users/prince.baah/Downloads/autortl-work');WORK=Path('C:/Users/prince.baah/Documents/Codex/2026-10-15/hey')
STAGE=WORK/'work/elastic-dot4-stage';run=ROOT/f'logs/elastic-dot4-admission-{a.attempt}'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text(encoding='utf-8'))
plan=read(run/'prelaunch-plan.json');result=read(run/'result.json')
assert result['executed']==result['planned']==19 and all(result[k] for k in ('runtime_source_unchanged','stage_unchanged','router_stats_unchanged'))
assert all(sha(STAGE/p)==h for p,h in plan['stage_files'].items())
assert all(sha(ROOT/p)==h for p,h in plan['runtime_source'].items())
assert sha(WORK/'work/admit_elastic_dot4.py')==plan['helper_sha256']
out=ROOT/f'evidence/2026-10-25/elastic-dot4-admission-attempt-{a.attempt}';out.mkdir(parents=True,exist_ok=False)
for source,prefix in ((run,'admission'),(STAGE,'fixture')):
    for p in source.rglob('*'):
        rel=p.relative_to(source)
        if not p.is_file() or p.suffix not in ('.v','.py','.json','.jsonl','.log','.txt','.md','.yaml','.tcl','.xdc') or any(x.lower() in ('xsim.dir','.xil','artifacts','__pycache__') for x in rel.parts):continue
        target=out/prefix/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
for p in (WORK/'work/admit_elastic_dot4.py',Path(__file__),WORK/f'outputs/AutoRTL-elastic-dot4-admission-{a.attempt}.txt'):
    shutil.copyfile(p,out/p.name)
classification='Qualified independent control plus18 actual behavior assertion faults' if result['qualified'] else 'Not admitted; original strict results preserved before correction'
(out/'README.md').write_text(f'''# Elastic dot-product admission attempt{a.attempt}

{classification}. {result['admitted']}/{result['planned']} cases admitted;
all19 executed. No model or synthesis calls. See admission/result.json and raw
per-case receipts for exact outcomes; compiler/coverage failures never count as
behavioral kills. Inputs, stage and211 runtime identities stayed unchanged.
Binary simulator builds are excluded; outer archive-manifest defines preserved
files. This attempt is not rewritten after later checker instrumentation fixes.
''',encoding='utf-8')
manifest={p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file()}
(out/'archive-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
assert all(sha(out/p)==h for p,h in manifest.items())
print(json.dumps({'files':len(manifest),'qualified':result['qualified'],'admitted':result['admitted'],'planned':19}))
