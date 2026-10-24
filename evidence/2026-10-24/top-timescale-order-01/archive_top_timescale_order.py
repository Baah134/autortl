import hashlib,json,shutil
from pathlib import Path
ROOT=Path('C:/Users/prince.baah/Downloads/autortl-work')
WORK=Path('C:/Users/prince.baah/Documents/Codex/2026-10-15/hey')
run=ROOT/'logs/dot4-timescale-order-01';out=ROOT/'evidence/2026-10-24/top-timescale-order-01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result=json.loads((run/'result.json').read_text());assert result['passed'] and result['model_calls']==0
assert result['staged_linter_sha256']==sha(WORK/'work/top-timescale-stage/autortl/linter.py')
out.mkdir(parents=True,exist_ok=False)
for p in run.rglob('*'):
    rel=p.relative_to(run)
    if not p.is_file() or p.suffix not in ('.v','.json','.log','.txt') or any(x.lower() in ('xsim.dir','.xil','artifacts') for x in rel.parts):continue
    dest=out/'experiment'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
for name in ('autortl/linter.py','tests/test_wrapper_latency.py','tests/test_top_timescale.py'):
    dest=out/'proposed-source'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(WORK/'work/top-timescale-stage'/name,dest)
for p in (WORK/'work/check_dot4_timescale_order.py',Path(__file__),WORK/'work/top-timescale-stage.patch',
          WORK/'work/top-timescale-stage-report.json',WORK/'outputs/AutoRTL-dot4-timescale-order-01.txt'):
    shutil.copyfile(p,out/p.name)
for p in (WORK/'work').glob('*timescale*test*.txt'):shutil.copyfile(p,out/p.name)
(out/'README.md').write_text('''# Controlled mechanical-top timescale correction

Same three generated child sources and admitted685-cycle checker in both cases;
top compiled first in both. Original wrapper reproduces XSIM43-4099. Adding only
the deterministic timescale directive passes. No model calls, source/child/TB
changes or severity suppression. Canonical source stayed unchanged during this
experiment; proposed-source contains the staged patch, not yet integrated.
''',encoding='utf-8')
manifest={p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file()}
(out/'archive-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
assert all(sha(out/p)==h for p,h in manifest.items())
print(json.dumps({'archive':str(out),'files':len(manifest),'before':'XSIM43-4099','after':'685 checks PASS','models':0}))
