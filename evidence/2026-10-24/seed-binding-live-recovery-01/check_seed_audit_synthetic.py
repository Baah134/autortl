"""Pure stdlib fixtures for live-helper audit; never calls a model or vendor tool."""
import hashlib
import json
import runpy
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HELPER = ROOT / 'validate_seed_binding_live.py'
api = runpy.run_path(str(HELPER), run_name='audit_import_only')
digest = api['text_sha']
A, B = 'module m; // original\nendmodule', 'module m; // accepted\nendmodule'

def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding='utf-8')

def stage(root, iteration, role, method, seed, *, missing=False):
    identity = f'iteration_{iteration}:model:{role}.{method}:0'
    folder = root/'journal'/hashlib.sha256(identity.encode()).hexdigest()
    put(folder/'started.json', {'stage': identity,
        'kwargs': repr({} if missing else {'generation_seed': seed}),
        'args': f'(ModuleSpec(name="m"), {seed!r}, "instruction", "standard", <autortl.budget.Budget object at 0x123abc>)'})
    put(folder/'completed.json', {'stage': identity, 'result': 'plan text' if role == 'planner' else seed})

def iteration(root, number, seed, *, plan=True, missing=False, accepted=None):
    directory = root/f'iter_{number:03d}'
    put(directory/'proposal_input.json', {'before_iteration': number, 'enabled': False,
        'feedback': '', 'seed_sha256': digest(seed)})
    if plan:
        binding(root, number, seed, missing=missing)
    stage(root, number, 'generator', 'generate', seed)
    put(directory/'proposal_outcome.json', {'is_best': accepted is not None,
        'selected_source_sha256': digest(accepted or seed)})

def binding(root, number, seed, *, restart=False, missing=False):
    method = 'restart_plan' if restart else 'plan'
    stage(root, number, 'planner', method, seed, missing=missing)
    put(root/f'iter_{number:03d}'/f'proposal_{method}_binding.json', {
        'schema_version': 1, 'iteration': number, 'original_seed_sha256': digest(A),
        'seed_sha256': digest(seed), 'plan_sha256': digest('plan text')})

def main():
    output = Path(tempfile.mkdtemp(prefix='seed-audit-fixtures-', dir=ROOT))
    results = {}
    for case in ('accepted_refresh', 'stale_binding', 'missing_planner_seed', 'wrong_original', 'restart_periodic'):
        root = output/case
        if case == 'restart_periodic':
            iteration(root, 1, A, accepted=B)
            iteration(root, 2, B)
            binding(root, 2, A, restart=True)
            iteration(root, 3, A)
        else:
            iteration(root, 1, A, accepted=B)
            iteration(root, 2, B, plan=case != 'stale_binding', missing=case == 'missing_planner_seed')
        result = api['audit_bindings'](root, digest('wrong') if case == 'wrong_original' else digest(A))
        if case == 'accepted_refresh':
            assert result['passed'] and result['changed_seed_refreshes_exercised'] == 1
        elif case == 'restart_periodic':
            assert result['binding_invariant_passed'] and result['changed_seed_refreshes_exercised'] == 1
            assert result['iterations'][-1]['changed_seed_refresh_exercised'] is False
        else:
            assert not result['passed'] and not result['binding_invariant_passed']
        results[case] = result
    report = {'helper_sha256': hashlib.sha256(HELPER.read_bytes()).hexdigest(),
        'fixture_root': str(output), 'cases_passed': len(results), 'results': results,
        'scope': 'Synthetic journal audit only; no RTL/model/vendor execution'}
    put(ROOT/'seed-audit-synthetic-result.json', report)
    print(json.dumps({'cases_passed': len(results), 'fixture_root': str(output)}))

if __name__ == '__main__':
    main()

