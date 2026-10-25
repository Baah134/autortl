import hashlib,json,shutil,subprocess
from pathlib import Path
ROOT=Path('C:/Users/prince.baah/Downloads/autortl-work');WORK=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
previous='ab0269a5362cff9cc302698338399de4b9d50fea'
assert git('rev-parse','HEAD')==git('rev-parse','main')==previous
remote={x.split()[1]:x.split()[0] for x in git('ls-remote','origin','refs/heads/main','refs/heads/codex/contract-context').splitlines()}
assert len(remote)==2 and set(remote.values())=={previous}
frozen=json.loads((WORK/'elastic-fixes-source-freeze-01.json').read_text());assert all(sha(ROOT/p)==h for p,h in frozen.items())
missing=json.loads((WORK/'elastic-publication-missing-01.json').read_text())['missing'];assert len(missing)==11
script=WORK/'verify_elastic_publication.py';text=script.read_text(encoding='utf-8')
text=text.replace("'evidence/2026-10-25/contract-campaign-12']","'evidence/2026-10-25/contract-campaign-12', 'evidence/2026-10-25/publication-check-01']")
assert "'evidence/2026-10-25/publication-check-01']" in text
script.write_text(text,encoding='utf-8')
out=ROOT/'evidence/2026-10-25/publication-check-01';out.mkdir(parents=True,exist_ok=False)
for src,name in [(WORK.parent/'outputs/AutoRTL-elastic-published-blobs-failed-01.txt','failed-committed-blob-audit.txt'),
                 (WORK/'elastic-publication-missing-01.json','missing-manifest-blobs.json'),
                 (WORK/'gitignore-before-journal-fix.txt','gitignore-before.txt'),
                 (ROOT/'.gitignore','gitignore-after.txt'),(WORK/'journal-ignore-policy-checks.json','git-ignore-policy-checks.json'),
                 (script,'verify_committed_archives.py'),(Path(__file__),'close_elastic_publication_gap.py')]:shutil.copyfile(src,out/name)
(out/'README.md').write_text('''# Committed evidence publication gap and permanent correction

The initial ab0269a milestone passed all RTL/runtime gates, but its postpush
Git-blob audit failed: eleven locally present XSIM .jou journals were omitted
by Git ignore rules. All local archive hashes were valid. The original failure,
missing paths and before/after rules are retained; no historical manifest was
deleted or regenerated to conceal the omission.

The permanent rule permits .jou only under evidence, matching the existing .log
exception. Four actual Git checks establish archived journals/logs are included
while live journals/logs remain ignored. Runtime/test/spec/TB bytes and all 220
tested source identities are unchanged; the 1,415 tests, elastic run and full
tier0 gate are not regraded or repeated for this packaging-only correction.

verify_committed_archives.py audits all seven named new archive manifests against
raw committed blobs. ROOT identifies the canonical checkout; adjust that path
when running the audit on another clone. The development publication taxonomy
and permanent procedure are in docs/PUBLICATION.md. A successful audit after
the correction is required before the final publication checkpoint.
''',encoding='utf-8')
manifest={p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file()}
(out/'archive-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
paths=['.gitignore','START_HERE.md','docs/PUBLICATION.md','docs/PROGRESS.md','docs/SESSION_HANDOFF.md',out.relative_to(ROOT).as_posix(),*missing]
subprocess.run(['git','diff','--check'],cwd=ROOT,check=True,capture_output=True)
subprocess.run(['git','add','--',*paths],cwd=ROOT,check=True,capture_output=True)
assert all(p in paths or p.startswith(out.relative_to(ROOT).as_posix()+'/') for p in git('diff','--cached','--name-only').splitlines())
subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True,capture_output=True)
result=subprocess.run(['git','commit','-m','Preserve manifested Vivado journals in published evidence'],cwd=ROOT,check=True,capture_output=True,text=True)
head=git('rev-parse','HEAD');assert all(sha(ROOT/p)==h for p,h in frozen.items())
print(json.dumps({'packaging_commit':head,'new_archive_files':len(manifest),'missing_journals_added':11,'source220_unchanged':True}),flush=True)
subprocess.run(['git','push','--atomic','origin','HEAD:refs/heads/main','HEAD:refs/heads/codex/contract-context'],cwd=ROOT,check=True)
remote={x.split()[1]:x.split()[0] for x in git('ls-remote','origin','refs/heads/main','refs/heads/codex/contract-context').splitlines()}
assert len(remote)==2 and set(remote.values())=={head}
subprocess.run(['git','update-ref','refs/heads/main',head,previous],cwd=ROOT,check=True)
receipt={'integration_commit':head,'initial_incomplete_publication':previous,'remote_heads':remote,
         'source220_unchanged':True,'all_gates_complete':True,'status':git('status','--short')}
assert not receipt['status']
(WORK/'elastic-integration-publication.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt),flush=True)
