"""Preserve measured grader detections and misses before any runtime correction."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path('C:/Users/prince.baah/Downloads/autortl-work')
BASE=Path('C:/Users/prince.baah/Documents/Codex/2026-10-15/hey');WORK=BASE/'work'
RUN=ROOT/'logs/signed-fir4-generated-audit-01'
OUT=ROOT/'evidence/2026-10-26/signed-fir4-generated-audit-01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
result=read(RUN/'result.json');plan=read(RUN/'prelaunch-plan.json')
assert all(result['integrity'].values())
assert all(sha(ROOT/p)==h for p,h in plan['runtime_source'].items())
assert all(sha(Path(p))==h for p,h in result['original_identities'].items())
assert not OUT.exists();OUT.mkdir(parents=True)
allowed={'.v','.sv','.py','.json','.jsonl','.log','.txt','.rpt','.md','.yaml','.tcl','.xdc','.jou'}
for p in RUN.rglob('*'):
    rel=p.relative_to(RUN)
    if not p.is_file() or p.suffix not in allowed or any(x.lower() in ('xsim.dir','.xil','artifacts','__pycache__') for x in rel.parts):continue
    dest=OUT/'audit'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
for p in (WORK/'audit_signed_fir4_generated.py',Path(__file__),BASE/'outputs/AutoRTL-signed-fir4-generated-audit-01.txt'):
    shutil.copyfile(p,OUT/p.name)
(OUT/'README.md').write_text(f'''# Frozen generated signed FIR grader audit

Status: **{result['status']}**. Reference passed: **{result['control_passed']}**.
Generated unit grader detected **{result['detected']}/27** named faults;
**{result['missed']} misses**, **{result['ungraded']} ungraded/not executed**.
The independent admitted checker detected the same27faults on identical RTL.

Misses: {', '.join(result['missed_names']) or 'none'}.

All27 planned faults remain in the denominator. Only actual assertions with
successful compilation/elaboration/simulation process receipts count as detections;
compile errors and watchdogs do not. Raw per-case outcomes are retained.
Diagnostic wall time {result['elapsed_seconds']:.3f} seconds, actual tool-process
time {result['actual_tool_seconds']:.3f} seconds; zero model/synthesis calls.
The original generated experiment, its fileset/budget/router records and227source
identities stayed unchanged. This audit does not regrade that experiment.

See [original generated design](../generated-signed-fir4-attempt-01/README.md)
and [independent admission](../../2026-10-25/signed-fir4-admission-attempt-01/README.md).
These are selected simulation-fault sensitivities, not formal equivalence or
an arbitrary-model reliability comparison. Original grader/stimulus/golden
identities and all outcomes are frozen before any later correction.
''',encoding='utf-8')
manifest={p.relative_to(OUT).as_posix():sha(p) for p in OUT.rglob('*') if p.is_file()}
(OUT/'archive-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
assert all(sha(OUT/p)==h for p,h in manifest.items())
print(json.dumps({'files':len(manifest),'status':result['status'],'detected':result['detected'],'missed':result['missed'],'ungraded':result['ungraded']}))
