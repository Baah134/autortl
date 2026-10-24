import json,runpy,subprocess,sys,time
from pathlib import Path
root=Path('C:/Users/prince.baah/Downloads/autortl-work')
work=Path('C:/Users/prince.baah/Documents/Codex/2026-10-15/hey/work')
identities=runpy.run_path(str(work/'validate_seed_binding_live.py'))['identities']
before=identities()
freeze=work/'proposal-fixes-source-freeze-01.json'
assert not freeze.exists()
freeze.write_text(json.dumps(before,indent=2),encoding='utf-8')
print(json.dumps({'frozen_files':len(before)}),flush=True)
start=time.monotonic()
completed=subprocess.run([sys.executable,'-m','pytest','tests/','-q','-p','no:cacheprovider',
    '--basetemp',str(work/'pytest-proposal-fixes-full-01')],cwd=root)
result={'exit_code':completed.returncode,'elapsed_seconds':time.monotonic()-start,
        'frozen_source_files':len(before),'source_unchanged':before==identities()}
(work/'proposal-fixes-full-result-01.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result),flush=True)
assert result['source_unchanged']
sys.exit(completed.returncode)
