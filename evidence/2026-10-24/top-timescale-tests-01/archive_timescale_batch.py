import hashlib,json,re,shutil
from pathlib import Path
ROOT=Path('C:/Users/prince.baah/Downloads/autortl-work')
WORK=Path('C:/Users/prince.baah/Documents/Codex/2026-10-15/hey')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
frozen=read(WORK/'work/top-timescale-source-freeze-01.json')
result=read(WORK/'work/top-timescale-full-result-01.json')
assert result['exit_code']==0 and result['source_unchanged']
assert all(sha(ROOT/p)==h for p,h in frozen.items())
raw=WORK/'outputs/AutoRTL-top-timescale-full-01.txt'
matches=re.findall(r'(\d+) passed in ([\d.]+)s',raw.read_text(encoding='utf-8-sig'))
assert len(matches)==1
result.update({'passed':int(matches[0][0]),'pytest_seconds':float(matches[0][1])})
admission=ROOT/'logs/dot4-admission-02';qualified=read(admission/'result.json')
assert qualified['qualified'] and qualified['admitted']==qualified['executed']==13
assert read(admission/'prelaunch-plan.json')['runtime_source']==frozen
assert all(qualified[k] for k in ('runtime_source_unchanged','stage_unchanged','router_stats_unchanged'))
controlled=read(ROOT/'logs/dot4-timescale-order-01/result.json')
assert sha(ROOT/'autortl/linter.py')==controlled['staged_linter_sha256']
out=ROOT/'evidence/2026-10-24/top-timescale-tests-01';out.mkdir(parents=True,exist_ok=False)
for name in frozen:
    dest=out/'source-snapshot'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
    assert sha(dest)==frozen[name]
for p in admission.rglob('*'):
    rel=p.relative_to(admission)
    if not p.is_file() or p.suffix not in ('.v','.json','.jsonl','.log','.txt','.md','.yaml','.tcl') or any(x.lower() in ('artifacts','xsim.dir','.xil') for x in rel.parts):continue
    dest=out/'canonical-top-first-admission'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
for p in (raw,WORK/'work/top-timescale-source-freeze-01.json',WORK/'work/top-timescale-full-result-01.json',
          WORK/'work/dot4-timescale-integration.json',WORK/'work/test_top_timescale_batch.py',
          WORK/'work/admit_dot4_canonical.py',Path(__file__),WORK/'outputs/AutoRTL-dot4-admission-02.txt',
          WORK/'work/top-timescale-stage.patch',WORK/'work/top-timescale-stage-report.json',
          WORK/'work/dot4-fixture-tests-stage/focused-tests.txt'):
    shutil.copyfile(p,out/p.name)
for p in (WORK/'work').glob('top-timescale-focused-*.txt'):
    shutil.copyfile(p,out/p.name)
(out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
(out/'README.md').write_text(f'''# Deterministic wrapper fix and complex fixture regression

Full regression: {result['passed']} passed in {result['pytest_seconds']}seconds;
all{len(frozen)} frozen identities unchanged. Canonical dot4 checker admission:
controlPASS plus12 actual assertion faults,13/13, with top compiled FIRST.
No model calls during admission. The deployed linter bytes match the staged
function from the archived controlled before/after timescale experiment.

Fixture/reference is qualification material, not a generation seed. This change
does not regrade the archived completed complex design under a new runtime.
Original failure/results remain in generated-dot4-attempt-01. A fresh fulltier0
merge gate remains required before main integration of this runtime change.
''',encoding='utf-8')
manifest={p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file()}
(out/'archive-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
assert all(sha(out/p)==h for p,h in manifest.items())
print(json.dumps({'files':len(manifest),'tests':result['passed'],'seconds':result['pytest_seconds'],
                  'source_files':len(frozen),'source_unchanged':True,'canonical_admission':'13/13 top-first'}))
