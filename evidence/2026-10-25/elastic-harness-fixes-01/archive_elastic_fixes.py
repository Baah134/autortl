import hashlib,json,re,shutil
from pathlib import Path
ROOT=Path('C:/Users/prince.baah/Downloads/autortl-work')
BASE=Path('C:/Users/prince.baah/Documents/Codex/2026-10-15/hey');WORK=BASE/'work'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
frozen=read(WORK/'elastic-fixes-source-freeze-01.json')
result=read(WORK/'elastic-fixes-full-result-01.json')
assert result['exit_code']==0 and result['source_unchanged']
assert len(frozen)==220 and all(sha(ROOT/p)==h for p,h in frozen.items())
raw=BASE/'outputs/AutoRTL-elastic-fixes-full-01.txt'
matches=re.findall(r'(\d+) passed in ([\d.]+)s',raw.read_text(encoding='utf-8-sig'))
assert len(matches)==1
result.update(passed=int(matches[0][0]),pytest_seconds=float(matches[0][1]))
assert result['passed']>1366
out=ROOT/'evidence/2026-10-25/elastic-harness-fixes-01';out.mkdir(parents=True,exist_ok=False)
for name,digest in frozen.items():
    dest=out/'source-snapshot'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
    assert sha(dest)==digest
files=[raw,WORK/'elastic-fixes-source-freeze-01.json',WORK/'elastic-fixes-full-result-01.json',WORK/'elastic-fixes-integration.json',
       WORK/'test_elastic_fixes.py',WORK/'integrate_elastic_fixes.py',Path(__file__),
       WORK/'golden-prompt-stage.patch',WORK/'golden-prompt-stage-report.json',WORK/'golden-prompt-focus-03.txt',
       WORK/'budget-final-stage.patch',WORK/'budget-final-stage-audit.json',WORK/'budget-final-focused-02.txt',
       WORK/'elastic-dot4-tests-stage/focused-tests.txt']
for p in files:shutil.copyfile(p,out/p.name)
(out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
(out/'README.md').write_text(f'''# Oracle API and active-exit budget fixes

Full frozen regression: {result['passed']} passed in {result['pytest_seconds']} seconds;
all 220 source identities unchanged. Separate focused checks: prompt 7,
budget/resume 44, elastic fixture/verification 122 tests passed.

The prompt now supplies valid Python and documents the unchanged restricted
worker policy. Active dispatch exits persist final wall time without extra
model/tool charges; existing DONE reuse and preflight guards do not rewrite it.
Tests cover clean failures, provider/budget stops, raised exceptions and graceful
interruption. This does not establish atomic charging after a hard process kill.

The fixture spec and TB match the separately archived 19/19 actual Vivado
checker qualification. The original failed generated build and assertion-prefix
attempt are preserved separately. This suite does not establish generated RTL
success or PPA gain. A fresh full tier0 gate remains before main integration.
''',encoding='utf-8')
manifest={p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file()}
(out/'archive-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
assert all(sha(out/p)==h for p,h in manifest.items())
print(json.dumps(dict(files=len(manifest),**result)))
