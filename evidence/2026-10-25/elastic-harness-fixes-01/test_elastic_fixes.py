import json,runpy,subprocess,sys,time
from pathlib import Path
ROOT=Path('C:/Users/prince.baah/Downloads/autortl-work');WORK=Path('C:/Users/prince.baah/Documents/Codex/2026-10-15/hey/work')
identities=runpy.run_path(str(WORK/'validate_seed_binding_live.py'))['identities']
frozen=identities();target=WORK/'elastic-fixes-source-freeze-01.json';assert not target.exists()
target.write_text(json.dumps(frozen,indent=2),encoding='utf-8')
print(json.dumps({'frozen_files':len(frozen),'stage':'valid oracle API/subset and active-exit budget checkpoint; elastic fixture'}),flush=True)
tick=time.monotonic();process=subprocess.run([sys.executable,'-m','pytest','tests/','-q','-p','no:cacheprovider',
    '--basetemp',str(WORK/'pytest-elastic-fixes-full-01')],cwd=ROOT)
result={'exit_code':process.returncode,'elapsed_seconds':time.monotonic()-tick,'source_files':len(frozen),'source_unchanged':frozen==identities()}
(WORK/'elastic-fixes-full-result-01.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result),flush=True);assert result['source_unchanged'];sys.exit(process.returncode)
