"""Fresh full tier0 gate for the tested coverage runtime; not new counter work."""
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
sys.path.insert(0, str(ROOT))
from curriculum.runner import _history

sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_text(encoding='utf-8'))
identities = runpy.run_path(str(WORK/'validate_seed_binding_live.py'))['identities']
freeze = WORK/'fir4-coverage-source-freeze-01.json'
source = read(freeze)
tests = read(WORK/'fir4-coverage-full-result-01.json')
assert len(source) == 230 and identities() == source
assert tests['exit_code'] == 0 and tests['source_unchanged'] and tests['source_files'] == 230
assert tests['source_freeze_sha256'] == sha(freeze)
history = _history()
assert not any(record['tier'] > 0 and record['held'] for record in history), 'A higher held tier requires its own gate'
history_path = ROOT/'curriculum/results.jsonl'
history_before = history_path.read_bytes() if history_path.exists() else b''
stats = ROOT/'llm/router_stats.jsonl'
stats_before = stats.read_bytes()
run = ROOT/'logs/contract-campaign-13'
pre = ROOT/'logs/contract-campaign-13-prelaunch.json'
launch = ROOT/'logs/contract-campaign-13-launch-result.json'
assert not run.exists() and not pre.exists() and not launch.exists()
args = [sys.executable, 'run.py', 'bench', '--tier', '0', '--iterations', '1', '--best-of-n', '1',
        '--max-llm-calls', '16', '--max-vivado-minutes', '20', '--max-wall-minutes', '30',
        '--max-infra-retries', '1', '--target-part', 'xc7a35tcpg236-1', '--target-freq-mhz', '100', '--output-dir', str(run)]
for name in ('vivado', 'xvlog', 'xelab', 'xsim'):
    args += ['--'+name, 'C:/AMDDesignTools/2025.2/Vivado/bin/'+name+'.bat']
plan = {'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'runtime_source': source, 'source_freeze_sha256': sha(freeze),
        'full_test_receipt_sha256': sha(WORK/'fir4-coverage-full-result-01.json'),
        'command': args, 'started_utc': datetime.now(timezone.utc).isoformat(),
        'python_version': sys.version, 'python_executable_sha256': sha(Path(sys.executable)), 'helper_sha256': sha(Path(__file__)),
        'router_stats_offset':len(stats_before), 'router_stats_prefix_sha256':hashlib.sha256(stats_before).hexdigest(),
        'history_offset':len(history_before), 'history_prefix_sha256':hashlib.sha256(history_before).hexdigest(),
        'budgets_per_entry': {'iterations':1, 'best_of_n':1, 'model_calls':16, 'tool_minutes':20, 'wall_minutes':30, 'infra_retries':1},
        'no_higher_held_tier':True,
        'scope':'Fresh full tier0 runtime merge gate on230 tested source identities; not a new counter design objective. Ideal zero min/max I/O, no higher held tier.'}
pre.write_text(json.dumps(plan, indent=2), encoding='utf-8')
print(json.dumps({'prelaunch': str(pre), 'source_files':230, 'budgets_per_entry':plan['budgets_per_entry']}), flush=True)
tick = time.monotonic()
code = None
try:
    code = subprocess.call(args, cwd=ROOT)
finally:
    result = {'exit_code':code, 'wall_seconds':time.monotonic()-tick, 'source_unchanged':identities() == source,
              'router_stats_prefix_unchanged':stats.read_bytes()[:len(stats_before)] == stats_before,
              'history_prefix_unchanged':history_path.is_file() and history_path.read_bytes()[:len(history_before)] == history_before,
              'ended_utc':datetime.now(timezone.utc).isoformat()}
    launch.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result), flush=True)
assert result['source_unchanged'] and result['router_stats_prefix_unchanged'] and result['history_prefix_unchanged']
sys.exit(code)
