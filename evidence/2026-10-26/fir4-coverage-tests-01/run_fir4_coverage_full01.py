"""Freeze the reviewed coverage batch and run its complete pure regression once."""
import hashlib
import json
import runpy
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('C:/Users/prince.baah/Downloads/autortl-work')
WORK = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
identities = runpy.run_path(str(WORK/'validate_seed_binding_live.py'))['identities']
frozen = identities()
freeze = WORK/'fir4-coverage-source-freeze-01.json'
result_path = WORK/'fir4-coverage-full-result-01.json'
base = WORK/'pytest-fir4-coverage-full-01'
assert len(frozen) == 230
assert frozen == json.loads((WORK/'fir4-driver-integration.json').read_text(encoding='utf-8'))['staged_source']
assert not freeze.exists() and not result_path.exists() and not base.exists()
freeze.write_text(json.dumps(frozen, indent=2), encoding='utf-8')
command = [sys.executable, '-m', 'pytest', 'tests/', '-q', '-p', 'no:cacheprovider', '--basetemp', str(base)]
started = datetime.now(timezone.utc).isoformat()
print(json.dumps({'frozen_files': len(frozen), 'command': command, 'started_utc': started}), flush=True)
tick = time.monotonic()
code = None
try:
    code = subprocess.call(command, cwd=ROOT)
finally:
    result = {'exit_code': code, 'elapsed_seconds': time.monotonic()-tick,
              'source_files': len(frozen), 'source_unchanged': identities() == frozen,
              'source_freeze_sha256': hashlib.sha256(freeze.read_bytes()).hexdigest(),
              'command': command, 'started_utc': started,
              'ended_utc': datetime.now(timezone.utc).isoformat()}
    result_path.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result), flush=True)
assert result['source_unchanged']
sys.exit(code)
