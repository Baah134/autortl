import argparse,hashlib,json,re,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--attempt',required=True);a=p.parse_args()
root=Path('C:/Users/prince.baah/Downloads/autortl-work')
base=Path('C:/Users/prince.baah/Documents/Codex/2026-10-15/hey')
work=base/'work';attempt=a.attempt
freeze=work/f'proposal-fixes-source-freeze-{attempt}.json'
result=work/f'proposal-fixes-full-result-{attempt}.json'
log=base/f'outputs/AutoRTL-proposal-fixes-full-{attempt}.txt'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
frozen=json.loads(freeze.read_text())
r=json.loads(result.read_text());assert r['source_unchanged']
assert all(sha(root/p)==h for p,h in frozen.items())
text=log.read_text(encoding='utf-8-sig',errors='replace')
counts=re.findall(r'(?:(\d+) failed, )?(\d+) passed in ([\d.]+)s',text)
assert len(counts)==1
failed,passed,seconds=counts[0]
r.update({'failed':int(failed or 0),'passed':int(passed),'pytest_seconds':float(seconds)})
assert (r['exit_code']==0)==(r['failed']==0)
out=root/f'evidence/2026-10-23/proposal-fixes-tests-{attempt}'
out.mkdir(parents=True,exist_ok=False)
for p in (freeze,result,log,work/'proposal-fixes-integration-receipt.json',work/'test_proposal_fixes.py'):
    shutil.copyfile(p,out/p.name)
for p in (base/'outputs/AutoRTL-proposal-budget-focused-01.txt',work/'check_seed_audit_synthetic.py',
          work/'seed-audit-synthetic-result.json',work/'validate_seed_binding_live.py',Path(__file__)):
    if p.is_file():shutil.copyfile(p,out/p.name)
for name in frozen:
    dest=out/'source-snapshot'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/name,dest)
    assert sha(dest)==frozen[name]
(out/'result.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
manifest={p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file()}
(out/'archive-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
assert all(sha(out/p)==h for p,h in manifest.items())
print(json.dumps({'archive':str(out),'files':len(manifest),'failed':r['failed'],'passed':r['passed'],'source_unchanged':True}))
