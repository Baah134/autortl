"""Preserve the full regression and exact source; refuses an existing archive."""
import hashlib,json,re,shutil
from pathlib import Path
ROOT=Path('C:/Users/prince.baah/Downloads/autortl-work')
BASE=Path('C:/Users/prince.baah/Documents/Codex/2026-10-15/hey');WORK=BASE/'work'
OUT=ROOT/'evidence/2026-10-26/signed-fir4-tests-01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
source=read(WORK/'signed-fir4-source-freeze-01.json')
result=read(WORK/'signed-fir4-full-result-01.json')
raw=BASE/'outputs/AutoRTL-signed-fir4-full-01.txt'
assert result['exit_code']==0 and result['source_unchanged'] and len(source)==227
assert all(sha(ROOT/p)==h for p,h in source.items())
match=re.search(r'(\d+) passed in ([\d.]+)s',raw.read_text(encoding='utf-8'))
assert match, 'Missing actual pytest verdict'
runtime=read(ROOT/'logs/build-elastic-dot4-02/runtime.json')['implementation']
assert all(sha(ROOT/p)==h for p,h in runtime.items())
assert not OUT.exists();OUT.mkdir(parents=True)
for p,h in source.items():
    dest=OUT/'source-snapshot'/p;dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(ROOT/p,dest);assert sha(dest)==h
for p in (raw,WORK/'signed-fir4-full-result-01.json',WORK/'signed-fir4-source-freeze-01.json',
          WORK/'signed-fir4-integration.json',WORK/'signed-fir4-independent-review.json',WORK/'test_signed_fir4_batch.py',Path(__file__),
          WORK/'signed-fir4-tests-stage/focused-tests-final.json',WORK/'signed-fir4-tests-stage/focused-tests-final.txt'):
    shutil.copyfile(p,OUT/p.name)
result.update({'pytest_passed':int(match[1]),'pytest_seconds':float(match[2]),'runtime_implementation_unchanged':runtime})
(OUT/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
(OUT/'README.md').write_text(f'''# Signed FIR4 regression

**{match[1]} tests passed in {match[2]} seconds.** All227 frozen source files
remained unchanged. This change adds a qualified signed stateful FIR4 curriculum
fixture and tests; the56 runtime implementation files are byte-identical to the
previous elastic milestone. This is new-design coverage, without a new runtime
feature or repeated counter optimization objective.

The control and all27 compiling behavioral faults passed admission before
integration. See [admission evidence](../../2026-10-25/signed-fir4-admission-attempt-01/README.md).
Focused207 passing tests and the earlier failed verdict-framing test are retained
with admission. This archive retains the full regression, integration mapping
and exact tested source. No generated FIR design or PPA result is established
by these tests alone.
''',encoding='utf-8')
manifest={p.relative_to(OUT).as_posix():sha(p) for p in OUT.rglob('*') if p.is_file()}
(OUT/'archive-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
assert all(sha(OUT/p)==h for p,h in manifest.items())
print(json.dumps({'archive':str(OUT),'files':len(manifest),'passed':int(match[1]),'pytest_seconds':float(match[2])}))
