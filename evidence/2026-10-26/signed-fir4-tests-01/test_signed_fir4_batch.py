import json,runpy,subprocess,sys,time
from pathlib import Path
ROOT=Path('C:/Users/prince.baah/Downloads/autortl-work');WORK=Path(__file__).resolve().parent
identities=runpy.run_path(str(WORK/'validate_seed_binding_live.py'))['identities']
frozen=identities();target=WORK/'signed-fir4-source-freeze-01.json'
assert len(frozen)==227 and not target.exists()
target.write_text(json.dumps(frozen,indent=2),encoding='utf-8')
print(json.dumps({'frozen_files':len(frozen),'scope':'Qualified signed-stateful FIR4 fixture/tests only; runtime implementation unchanged'}),flush=True)
tick=time.monotonic();code=subprocess.call([sys.executable,'-m','pytest','tests/','-q','-p','no:cacheprovider',
    '--basetemp',str(WORK/'pytest-signed-fir4-full-01')],cwd=ROOT)
result={'exit_code':code,'elapsed_seconds':time.monotonic()-tick,'source_files':len(frozen),'source_unchanged':identities()==frozen}
(WORK/'signed-fir4-full-result-01.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result),flush=True);assert result['source_unchanged'];sys.exit(code)
