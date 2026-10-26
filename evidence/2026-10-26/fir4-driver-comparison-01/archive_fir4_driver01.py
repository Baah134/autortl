"""Preserve completed/incomplete driver comparison before canonical integration."""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path('C:/Users/prince.baah/Downloads/autortl-work')
WORK = Path(__file__).resolve().parent
STAGE = WORK/'fir4-driver-stage'
RUN = ROOT/'logs/fir4-driver-comparison-01'
OUT = ROOT/'evidence/2026-10-26/fir4-driver-comparison-01'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_text(encoding='utf-8'))


def sources(root):
    result = {}
    for name in ('autortl', 'llm', 'tests', 'curriculum', 'scripts', 'data', '.claude'):
        for path in (root/name).rglob('*'):
            if path.is_file() and path.suffix in ('.py','.v','.sv','.json','.yaml','.md') and '__pycache__' not in path.parts:
                result[path.relative_to(root).as_posix()] = sha(path)
    result['run.py'] = sha(root/'run.py')
    return result


assert not OUT.exists(), 'Never overwrite an archived attempt'
plan = read(RUN/'prelaunch-plan.json')
result = read(RUN/'result.json')  # Written only after the measurement loop ends.
assert result['status'] in ('completed', 'incomplete')
assert result['canonical228_stage230_originalrun_budget_stats_unchanged']
assert result['payload_expected_arrays_unchanged_from_signed_only']
assert result['model_calls'] == result['synthesis_calls'] == 0
assert sources(ROOT) == plan['canonical_source'] and len(plan['canonical_source']) == 228
assert sources(STAGE) == plan['staged_source'] and len(plan['staged_source']) == 230
assert all(sha(Path(path)) == digest for path,digest in plan['original_identities'].items())
old = ROOT/'logs/build-signed-fir4-01'
assert set(plan['original_file_set']) == {str(path.relative_to(old)) for path in old.rglob('*') if path.is_file()}
assert sha(WORK/'measure_fir4_driver_stage01.py') == plan['helper_sha256']
focus = read(STAGE/'focused-tests-result.json')
assert focus['exit_code'] == 0 and focus['passed'] == 117
assert sha(STAGE/'focused-tests-result.json') == plan['stage_focus_receipt_sha256']
assert sha(STAGE/'focused-tests.txt') == focus['focused_log_sha256']
assert sha(STAGE/'old-driver-regression.txt') == focus['pre_patch']['old_log_sha256']
assert read(STAGE/'original-source228.json') == plan['canonical_source']
assert sha(STAGE/'tbgen-before.py') == plan['canonical_source']['autortl/tbgen.py']
assert sha(STAGE/'tbgen.patch') == focus['patch_sha256']
review = read(WORK/'fir4-driver-independent-review.json')
assert review['stage_focus_receipt_sha256'] == plan['stage_focus_receipt_sha256']
addendum = read(WORK/'fir4-driver-prepatch-command-addendum.json')
assert addendum['original_receipt_sha256'] == sha(STAGE/'pre-patch-regression.json')
assert addendum['old_log_sha256'] == sha(STAGE/'old-driver-regression.txt')
assert result['planned_faults'] == 27 and result['nominal_controls'] == len(result['controls'])
assert result['nominal_controls_passed'] == sum(row['passed'] for row in result['controls'])
assert result['executed_faults'] == max(0, len(result['audit'])-1)
for grade in ('detected','missed'):
    assert result[grade] == sum(row['grade'] == grade for row in result['audit'][1:])
assert result['detected'] + result['missed'] + result['ungraded'] == 27
raw = WORK.parent/'outputs/AutoRTL-fir4-driver-comparison-01.txt'
assert raw.is_file() and raw.stat().st_size > 0
OUT.mkdir(parents=True, exist_ok=False)
allowed = {'.v','.sv','.py','.json','.jsonl','.log','.txt','.rpt','.md','.yaml','.tcl','.xdc','.jou'}
excluded = {'artifacts','xsim.dir','.xil','__pycache__'}
for path in RUN.rglob('*'):
    relative = path.relative_to(RUN)
    if not path.is_file() or path.suffix.lower() not in allowed or any(part.lower() in excluded for part in relative.parts):
        continue
    target = OUT/'comparison'/relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, target)
for relative,digest in plan['staged_source'].items():
    target = OUT/'staged-source-snapshot'/relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(STAGE/relative, target)
    assert sha(target) == digest
for name in ('focused-tests-result.json','focused-tests.txt','old-driver-regression.txt','original-source228.json',
             'pre-patch-regression.json','tbgen-before.py','tbgen.patch'):
    target = OUT/'stage-review'/name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(STAGE/name, target)
for path in (WORK/'measure_fir4_driver_stage01.py', Path(__file__), raw,
             WORK/'fir4-driver-independent-review.json', WORK/'fir4-driver-prepatch-command-addendum.json'):
    shutil.copyfile(path, OUT/path.name)
summary = {key:value for key,value in result.items() if key not in ('controls','producer_probe','audit')}
summary['staged_source_files'] = 230
summary['canonical_source_files_before_driver_integration'] = 228
(OUT/'result.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
text = f'''# Generated scoreboard driver comparison01

Actual measurement status: **{result['status']}**. The frozen FIR reference
{'passed' if result['reference_passed'] else 'did not pass'};
**{result['detected']}/27** named faults detected, **{result['missed']}** missed,
**{result['ungraded']}** ungraded or unexecuted. All27 remain in the denominator.
See comparison/result.json and individual raw logs/process receipts.

The five nominal traffic controls are separate: **{result['nominal_controls_passed']}/5**
passed their required coverage. The deliberately bad producer-driver probe
{'was detected' if result['bad_driver_probe_detected'] else 'was not established as detected'};
it is not an RTL mutant and is not added to the27-fault score.

The old generated FIR oracle, reference and all fault sources were frozen.
The110 signed-only payload/expected arrays stayed byte-identical; only generated
driver scheduling changed. Source snapshots retain230 staged files, while the
canonical228-file source and original build artifacts/budget/router statistics
stayed unchanged. No models or synthesis were invoked. Actual measured wall
time was {result['elapsed_seconds']:.3f} seconds.

The driver exercises legal bubbles with changing invalid payloads and synchronous
off-edge reset pulses, while preserving blocked offers. It does not add an
occupied rising-edge reset policy or require ports to remain invariant while
reset is asserted. Async-reset contracts receive no unmodelled pulses.
Selected fault sensitivity is not formal equivalence or a model-strength claim.
No resource, power or timing improvement follows from this verification audit.

The original4-failed/6-passed pre-patch log and117-test focused result are
preserved. The command addendum transparently supplies the omitted original
basetemp argument; it does not rewrite the original receipt. Binary simulator
builds are omitted; archive-manifest.json defines the retained raw artifacts.
'''
(OUT/'README.md').write_text(text, encoding='utf-8')
manifest = {path.relative_to(OUT).as_posix():sha(path) for path in OUT.rglob('*') if path.is_file()}
(OUT/'archive-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
assert all(sha(OUT/path) == digest for path,digest in manifest.items())
assert sources(ROOT) == plan['canonical_source'] and sources(STAGE) == plan['staged_source']
assert all(sha(Path(path)) == digest for path,digest in plan['original_identities'].items())
print(json.dumps({'archive':str(OUT), 'files':len(manifest), 'status':result['status'],
                  'detected':result['detected'], 'missed':result['missed'], 'ungraded':result['ungraded']}))
