"""Launch a new FIR build on the tested coverage runtime; never resume build01."""
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
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_text(encoding='utf-8'))
identities = runpy.run_path(str(WORK/'validate_seed_binding_live.py'))['identities']
freeze = WORK/'fir4-coverage-source-freeze-01.json'
source = read(freeze)
tests = read(WORK/'fir4-coverage-full-result-01.json')
assert len(source) == 230 and identities() == source
assert tests['exit_code'] == 0 and tests['source_unchanged'] and tests['source_files'] == 230
assert tests['source_freeze_sha256'] == sha(freeze)
admission = ROOT/'evidence/2026-10-25/signed-fir4-admission-attempt-01'
manifest = read(admission/'archive-manifest.json')
assert all(sha(admission/path) == digest for path, digest in manifest.items())
qualified = read(admission/'admission/result.json')
assert qualified['qualified'] and qualified['admitted'] == qualified['executed'] == qualified['planned'] == 28
old_plan = read(admission/'admission/prelaunch-plan.json')
fixture = ROOT/'curriculum/tier3/signed_fir4_build'
spec = fixture/'design_spec.json'
tb = fixture/'signed_fir4_tb.v'
assert sha(spec) == old_plan['stage_files']['design_spec.json']
assert sha(tb) == old_plan['stage_files']['signed_fir4_tb.v']
old_runtime = read(ROOT/'logs/build-signed-fir4-01/runtime.json')['implementation']
runtime = {path: sha(ROOT/path) for path in old_runtime}
changed = {path: {'old': digest, 'new': runtime[path]} for path, digest in old_runtime.items() if runtime[path] != digest}
assert set(changed) == {'autortl/tbgen.py', 'data/taxonomy.yaml'}, changed
run = ROOT/'logs/build-signed-fir4-02'
pre = ROOT/'logs/build-signed-fir4-02-prelaunch.json'
launch = ROOT/'logs/build-signed-fir4-02-launch-result.json'
assert not run.exists() and not pre.exists() and not launch.exists()
stats = ROOT/'llm/router_stats.jsonl'
before = stats.read_bytes()
args = [sys.executable, 'run.py', 'build', '--spec', str(spec), '--tb', str(tb), '--top', 'signed_fir4',
        '--generate-golden', '--objective', 'minimize_luts', '--target-part', 'xc7a35tcpg236-1',
        '--target-freq-mhz', '100', '--iterations', '3', '--best-of-n', '1', '--max-llm-calls', '16',
        '--max-vivado-minutes', '25', '--max-wall-minutes', '35', '--max-infra-retries', '1', '--output-dir', str(run)]
for name in ('vivado', 'xvlog', 'xelab', 'xsim'):
    args += ['--'+name, 'C:/AMDDesignTools/2025.2/Vivado/bin/'+name+'.bat']
plan = {'runtime_source': source, 'runtime_implementation_from_build01': old_runtime,
        'runtime_implementation': runtime, 'runtime_diff_from_build01': changed,
        'source_freeze_sha256': sha(freeze), 'full_test_receipt_sha256': sha(WORK/'fir4-coverage-full-result-01.json'),
        'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'fixture_hashes': {path.relative_to(fixture).as_posix(): sha(path) for path in fixture.rglob('*')
                           if path.is_file() and '__pycache__' not in path.parts},
        'spec_path': str(spec), 'spec_sha256': sha(spec), 'tb_path': str(tb), 'tb_sha256': sha(tb),
        'admission_archive': str(admission), 'admission_manifest_sha256': sha(admission/'archive-manifest.json'),
        'budgets': {'iterations':3, 'best_of_n':1, 'model_calls':16, 'tool_minutes':25, 'wall_minutes':35, 'infra_retries':1},
        'command': args, 'started_utc': datetime.now(timezone.utc).isoformat(),
        'python_version': sys.version, 'python_executable_sha256': sha(Path(sys.executable)), 'helper_sha256': sha(Path(__file__)),
        'reference_is_not_a_generation_input': True, 'router_stats_offset': len(before),
        'router_stats_prefix_sha256': hashlib.sha256(before).hexdigest(),
        'model': 'codex.default; actual identity unobserved',
        'scope': 'Fresh build02 on tested coverage runtime; same admitted FIR spec/TB and original budgets. Ideal zero min/max I/O; no reference seed or old-run regrade.'}
pre.write_text(json.dumps(plan, indent=2), encoding='utf-8')
print(json.dumps({'prelaunch': str(pre), 'source_files':230, 'qualified':'28/28', 'budgets':plan['budgets']}), flush=True)
tick = time.monotonic()
code = None
try:
    code = subprocess.call(args, cwd=ROOT)
finally:
    result = {'exit_code': code, 'cli_wall_seconds': time.monotonic()-tick, 'source_unchanged': identities() == source,
              'stats_prefix_unchanged': stats.read_bytes()[:len(before)] == before,
              'ended_utc': datetime.now(timezone.utc).isoformat()}
    launch.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result), flush=True)
assert result['source_unchanged'] and result['stats_prefix_unchanged']
sys.exit(code)
