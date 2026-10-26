import hashlib,json,shutil
from pathlib import Path
R=Path('C:/Users/prince.baah/Downloads/autortl-work')
B=Path('C:/Users/prince.baah/Documents/Codex/2026-10-15/hey');W=B/'work'
RUN=R/'logs/fir4-signed-boundary-comparison-01';OUT=R/'evidence/2026-10-26/fir4-signed-boundary-comparison-01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
plan=read(RUN/'prelaunch-plan.json');result=read(RUN/'result.json')
assert result['passed'] and result['same_golden_reference_mutant'] and result['source228_unchanged']
assert all(sha(R/p)==h for p,h in plan['runtime_source'].items())
assert all(sha(Path(p))==h for p,h in plan['original_identities'].items())
assert not OUT.exists();OUT.mkdir(parents=True)
allowed={'.v','.py','.json','.jsonl','.log','.txt','.rpt','.md','.yaml','.tcl','.xdc','.jou'}
for p in RUN.rglob('*'):
    rel=p.relative_to(RUN)
    if not p.is_file() or p.suffix not in allowed or any(x.lower() in ('xsim.dir','.xil','artifacts','__pycache__') for x in rel.parts):continue
    dest=OUT/'comparison'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
for p,h in plan['runtime_source'].items():
    dest=OUT/'source-snapshot'/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/p,dest);assert sha(dest)==h
S=W/'fir4-signed-corners-stage'
for n in ('focused-tests-result.json','focused-tests.txt','old-regression.txt','original-source227.json','pre-patch.json','tbgen-before.py','tbgen.patch'):
    dest=OUT/'pre-tool-tests'/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(S/n,dest)
for p in (W/'check_fir4_signed_boundary.py',Path(__file__),W/'integrate_fir4_signed_corners.py',W/'fir4-signed-corners-integration.json',B/'outputs/AutoRTL-fir4-signed-boundary-comparison-01.txt'):
    shutil.copyfile(p,OUT/p.name)
(OUT/'README.md').write_text('''# Controlled signed-boundary coverage correction

The original generated FIR grader passed the reference AND missed the signed12
truncation fault. Adding six alternating signed minimum/maximum accepted payloads
preserved the control pass and produced five actual out_data assertions against
the identical faulty RTL. Successful xvlog/xelab/xsim exits are retained.

The generated Python oracle, correct reference and faulty RTL were unchanged.
Original payload corner/example prefix and the exact100 seeded random inputs are
preserved.104 payloads become110; expected range expands from[-1703,1539] to
[-2169,2166]. Expectations are recomputed through the same accepted-history oracle.
No model/synthesis calls or changes to the completed original run/budget/statistics.
This is one targeted sensitivity improvement, not a new full27-fault grader score.

Before the six-line runtime insertion, the new pure regressions produced7failed/
4passed. After it,107focused tests passed7.00seconds. Both original failure and
passing scope, old code, exactpatch, integration mapping and228source snapshot
are retained. Fullregression and fresh runtime gates remain separate work.

See [original generated-grader audit](../signed-fir4-generated-audit-01/README.md)
and [original independently verified design](../generated-signed-fir4-attempt-01/README.md).
''',encoding='utf-8')
manifest={p.relative_to(OUT).as_posix():sha(p) for p in OUT.rglob('*') if p.is_file()}
(OUT/'archive-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
assert all(sha(OUT/p)==h for p,h in manifest.items())
print(json.dumps({'files':len(manifest),'control_passed':True,'same_truncation_now_detected':True,'source_files':len(plan['runtime_source'])}))
