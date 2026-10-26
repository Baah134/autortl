"""Archive only an actual passing frozen coverage-runtime full regression."""
import hashlib
import json
import re
import runpy
import shutil
from pathlib import Path

ROOT = Path('C:/Users/prince.baah/Downloads/autortl-work')
WORK = Path(__file__).resolve().parent
OUT = ROOT/'evidence/2026-10-26/fir4-coverage-tests-01'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_text(encoding='utf-8'))
identities = runpy.run_path(str(WORK/'validate_seed_binding_live.py'))['identities']
freeze = WORK/'fir4-coverage-source-freeze-01.json'
source = read(freeze)
receipt = WORK/'fir4-coverage-full-result-01.json'
result = read(receipt)
assert not OUT.exists(), 'Never overwrite a full-suite evidence archive'
assert len(source) == 230 and identities() == source
assert result['exit_code'] == 0 and result['source_unchanged'] and result['source_files'] == 230
assert result['source_freeze_sha256'] == sha(freeze)
raw = WORK.parent/'outputs/AutoRTL-fir4-coverage-full-01.txt'
text = raw.read_text(encoding='utf-8')
summaries = re.findall(r'(?m)^\s*(\d+) passed(?:, [^\r\n]*?)? in (\d+(?:\.\d+)?)s(?: \([^\r\n]*\))?\s*$', text)
assert len(summaries) == 1, 'Require exactly one actual successful pytest summary'
count,seconds = int(summaries[0][0]),float(summaries[0][1])
assert count > 0 and seconds > 0
links = {}
for name in ('fir4-driver-comparison-01','fir4-signed-boundary-comparison-01','signed-fir4-generated-audit-01'):
    archive = ROOT/'evidence/2026-10-26'/name
    manifest = read(archive/'archive-manifest.json')
    assert all(sha(archive/path) == digest for path,digest in manifest.items())
    links[name] = {'path':archive.relative_to(ROOT).as_posix(),
                   'manifest_sha256':sha(archive/'archive-manifest.json'), 'verified_files':len(manifest)}
required = [WORK/'run_fir4_coverage_full01.py', Path(__file__), freeze, receipt, raw,
            WORK/'fir4-driver-integration.json', WORK/'fir4-signed-corners-integration.json',
            WORK/'fir4-driver-independent-review.json', WORK/'fir4-driver-prepatch-command-addendum.json']
assert all(path.is_file() for path in required)
OUT.mkdir(parents=True, exist_ok=False)
for relative,digest in source.items():
    target = OUT/'source-snapshot'/relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT/relative, target)
    assert sha(target) == digest
for path in required:
    shutil.copyfile(path, OUT/path.name)
stage_files = {
    'fir4-signed-corners-stage': ('focused-tests-result.json','focused-tests.txt','old-regression.txt',
                                 'pre-patch.json','tbgen.patch'),
    'fir4-driver-stage': ('focused-tests-result.json','focused-tests.txt','old-driver-regression.txt',
                         'pre-patch-regression.json','tbgen.patch'),
}
for directory,names in stage_files.items():
    stage = WORK/directory
    focus = read(stage/'focused-tests-result.json')
    assert focus['exit_code'] == 0 and sha(stage/'focused-tests.txt') == focus['focused_log_sha256']
    for name in names:
        target = OUT/'focused-stage-evidence'/directory/name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(stage/name, target)
summary = {'exit_code':0, 'passed':count, 'pytest_seconds':seconds,
           'actual_launch_elapsed_seconds':result['elapsed_seconds'], 'source_files':230,
           'source_unchanged':True, 'source_freeze_sha256':sha(freeze), 'full_raw_log_sha256':sha(raw),
           'related_evidence':links, 'command':result['command'],
           'scope':'Full pure regression for signed payload and legal scoreboard driver coverage corrections; no new hardware/PPA or model-strength claim.'}
(OUT/'result.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
(OUT/'README.md').write_text(f'''# FIR coverage-runtime full regression01

Actual complete regression: **{count} tests passed in {seconds:.2f} seconds**.
The launch receipt records {result['elapsed_seconds']:.3f} seconds of actual
wall time. All230 source identities remained unchanged; the retained source
snapshot matches the exact freeze bound by the passing launch receipt.

This batch covers signed temporal extrema and legal scoreboard bubbles,
invalid payload noise and sync-only off-edge reset pulses. Focused passing
tests and original failing regressions are retained alongside integration
receipts. Related-evidence manifest hashes link the separate old generated
grader audit, signed-boundary comparison and full driver comparison without
rewriting those outcomes. See result.json for measured counts and references.

These are software regressions, not a new FPGA result. Fresh generated build02
and the full tier0 runtime gate require their own actual results. No formal,
general reset-coverage, board-validation or weaker-model claim follows.
''', encoding='utf-8')
manifest = {path.relative_to(OUT).as_posix():sha(path) for path in OUT.rglob('*') if path.is_file()}
(OUT/'archive-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
assert all(sha(OUT/path) == digest for path,digest in manifest.items())
assert identities() == source
print(json.dumps({'archive':str(OUT), 'files':len(manifest), 'passed':count,
                  'pytest_seconds':seconds, 'source_files':230}))
