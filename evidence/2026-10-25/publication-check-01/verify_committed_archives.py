"""Verify the committed archive blobs, not just working-copy files."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path('C:/Users/prince.baah/Downloads/autortl-work')
names=['evidence/2026-10-25/elastic-dot4-admission-attempt-01', 'evidence/2026-10-25/elastic-dot4-admission-attempt-02', 'evidence/2026-10-25/generated-elastic-dot4-attempt-01', 'evidence/2026-10-25/elastic-harness-fixes-01', 'evidence/2026-10-25/generated-elastic-dot4-attempt-02', 'evidence/2026-10-25/contract-campaign-12', 'evidence/2026-10-25/publication-check-01']
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
process=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
counts={}
try:
    for name in names:
        manifest=json.loads((ROOT/name/'archive-manifest.json').read_text())
        for relative,expected in manifest.items():
            path=name+'/'+relative
            process.stdin.write((head+':'+path+'\n').encode('utf-8'));process.stdin.flush()
            fields=process.stdout.readline().rstrip(b'\n').split()
            assert len(fields)==3 and fields[1]==b'blob',(path,fields)
            size=int(fields[2]);data=process.stdout.read(size);assert len(data)==size
            assert process.stdout.read(1)==b'\n'
            assert hashlib.sha256(data).hexdigest()==expected,'Committed archive blob changed: '+path
        counts[name]=len(manifest)
finally:
    process.stdin.close();process.stdout.close();process.wait(timeout=10)
assert process.returncode==0
print(json.dumps({'commit':head,'committed_archive_blobs_verified':sum(counts.values()),'archives':counts}))
