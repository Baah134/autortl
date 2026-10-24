"""One fresh actual seed-binding validation; preparation here does not execute it.

Run only after integration, full regression, and commit. Refuses an existing
output directory. This is a mechanism validation, not a feedback/PPA comparison.
"""
import ast
import hashlib
import json
import re
import subprocess
import sys
import time
import traceback
from pathlib import Path

ROOT = Path('C:/Users/prince.baah/Downloads/autortl-work')
STUDY = ROOT / 'logs/proposal-feedback-study-02'
OUTPUT = ROOT / 'logs/seed-binding-live-01'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def text_sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def identities():
    """Same source selection as proposal_study02.identities, without importing it."""
    result = {}
    for name in ('autortl', 'llm', 'tests', 'curriculum', 'scripts', 'data', '.claude'):
        for path in (ROOT / name).rglob('*'):
            if (path.is_file() and path.suffix in ('.py', '.v', '.sv', '.json', '.yaml', '.md')
                    and '__pycache__' not in path.parts):
                result[path.relative_to(ROOT).as_posix()] = sha(path)
    result['run.py'] = sha(ROOT / 'run.py')
    return result


def journal(output):
    stages = {}
    for path in sorted((output / 'journal').glob('*/started.json')):
        started = read(path)
        completion = path.with_name('completed.json')
        stages[started['stage']] = {
            'started_path': str(path), 'started': started,
            'completed_path': str(completion) if completion.is_file() else None,
            'completed': read(completion) if completion.is_file() else None}
    return stages


def generation_argument(started):
    """Parse a repr as syntax only; never evaluate model or journal text.

    The current stage schema stores positional args with a Budget object repr.
    Replace only that nonliteral object repr, then inspect the seed Constant.
    """
    source = re.sub(r'<autortl\.budget\.Budget object at 0x[0-9a-fA-F]+>',
                    'None', started['args'])
    node = ast.parse(source, mode='eval').body
    if not isinstance(node, ast.Tuple) or len(node.elts) < 2:
        raise ValueError('Unsupported generator journal argument schema')
    seed = node.elts[1]
    if not isinstance(seed, ast.Constant) or not isinstance(seed.value, str):
        raise ValueError('Generator journal seed is not a string literal')
    return seed.value


def audit_bindings(output, original_seed_source_sha256):
    """Apply each local binding before generation and each restart afterward."""
    stages = journal(output)
    problems, details, plans = [], [], []
    binding = None
    original_sha = original_seed_source_sha256
    previous_input = None
    previous_iteration = None
    previous_outcome = None
    previous_restart = False
    changed_seeds = 0
    changed_seed_refreshes = 0
    generated_inputs = 0
    unbound = []
    inspected_generators = set()

    def load_binding(path, iteration, method):
        data = read(path)
        identity = f'iteration_{iteration}:model:planner.{method}:0'
        stage = stages.get(identity)
        entry = {'iteration': iteration, 'method': method, 'path': str(path),
                 'seed_sha256': data.get('seed_sha256'),
                 'plan_sha256': data.get('plan_sha256'),
                 'journal_stage': identity, 'plan_sha_matches_journal': False,
                 'journal_seed_available': False, 'journal_seed_matches_binding': None}
        if data.get('schema_version') != 1 or data.get('iteration') != iteration:
            problems.append(f'Invalid binding identity: {path}')
        if data.get('original_seed_sha256') != original_sha:
            problems.append(f'Original seed identity does not match frozen UTF-8 source: {path}')
        for key in ('original_seed_sha256', 'seed_sha256', 'plan_sha256'):
            if not isinstance(data.get(key), str) or not re.fullmatch(r'[a-f0-9]{64}', data[key]):
                problems.append(f'Invalid {key}: {path}')
        if stage and stage['completed'] and isinstance(stage['completed'].get('result'), str):
            entry['plan_sha_matches_journal'] = text_sha(stage['completed']['result']) == data.get('plan_sha256')
            if stage['completed'].get('stage') != identity:
                problems.append(f'Journal stage identity mismatch: {identity}')
            try:
                kwargs = ast.literal_eval(stage['started']['kwargs'])
                supplied = kwargs.get('generation_seed')
                if isinstance(supplied, str):
                    entry['journal_seed_available'] = True
                    entry['journal_seed_matches_binding'] = text_sha(supplied) == data.get('seed_sha256')
            except (SyntaxError, ValueError, TypeError, AttributeError):
                entry['journal_seed_note'] = 'Unsupported saved kwargs schema'
        if not entry['plan_sha_matches_journal']:
            problems.append(f'Plan SHA not established by completed journal string: {identity}')
        if entry['journal_seed_matches_binding'] is not True:
            problems.append(f'Planner source match not established by known journal kwargs schema: {identity}')
        if method == 'restart_plan' and data.get('seed_sha256') != original_sha:
            problems.append(f'Restart does not bind original source: {path}')
        plans.append(entry)
        return data

    for directory in sorted(output.glob('iter_*')):
        if not re.fullmatch(r'iter_\d+', directory.name):
            continue
        iteration = int(directory.name.split('_')[1])
        input_path = directory / 'proposal_input.json'
        normal = directory / 'proposal_plan_binding.json'
        restart = directory / 'proposal_restart_plan_binding.json'
        if normal.is_file():
            binding = load_binding(normal, iteration, 'plan')
        inputs = read(input_path) if input_path.is_file() else None
        if inputs:
            if inputs.get('before_iteration') != iteration or inputs.get('enabled') is not False or inputs.get('feedback') != '':
                problems.append(f'Input identity or default-off context violated: {input_path}')
            seed = inputs.get('seed_sha256')
            changed = previous_input is not None and seed != previous_input
            changed_seeds += int(changed)
            previous_input = seed
        else:
            seed, changed = None, False
        generation = [(key, value) for key, value in stages.items()
                      if key.startswith(f'iteration_{iteration}:model:generator.generate:')]
        local = {'iteration': iteration, 'input_seed_sha256': seed,
                 'seed_changed_from_prior_input': changed,
                 'binding_seed_sha256': binding.get('seed_sha256') if binding else None,
                 'fresh_plan': normal.is_file(), 'generated_inputs': len(generation)}
        accepted_source_transition = bool(previous_iteration == iteration - 1
            and previous_outcome is not None and previous_outcome.get('is_best') is True
            and previous_outcome.get('selected_source_sha256') == seed
            and not previous_restart)
        local['immediate_prior_accepted_source_transition'] = accepted_source_transition
        local_inputs_bound = True
        for identity, stage in generation:
            generated_inputs += 1
            inspected_generators.add(identity)
            okay = inputs is not None and binding is not None and seed == binding.get('seed_sha256')
            try:
                actual = text_sha(generation_argument(stage['started']))
                okay = okay and actual == seed
            except (SyntaxError, ValueError, KeyError, TypeError) as error:
                okay = False
                problems.append(f'Cannot establish generator seed from journal: {identity}: {error}')
            if not okay:
                local_inputs_bound = False
                unbound.append(identity)
        # The corrected path needs a changed source, a new ordinary plan for that
        # source, an immediately preceding acceptance of that exact source with
        # no intervening restart, and an actual generator input using the plan.
        # Restart-to-original plus periodic planning does not count.
        fresh_verified_plan = (normal.is_file() and plans
            and plans[-1]['iteration'] == iteration and plans[-1]['method'] == 'plan'
            and plans[-1]['plan_sha_matches_journal'] is True
            and plans[-1]['journal_seed_matches_binding'] is True)
        local['changed_seed_refresh_exercised'] = bool(changed and generation
            and accepted_source_transition and local_inputs_bound and fresh_verified_plan)
        changed_seed_refreshes += int(local['changed_seed_refresh_exercised'])
        details.append(local)
        if restart.is_file():
            binding = load_binding(restart, iteration, 'restart_plan')
        previous_iteration = iteration
        outcome_path = directory / 'proposal_outcome.json'
        previous_outcome = read(outcome_path) if outcome_path.is_file() else None
        previous_restart = (directory / 'proposal_restart.json').is_file() or restart.is_file()
    all_generators = {key for key in stages if ':model:generator.generate:' in key}
    unbound.extend(sorted(all_generators - inspected_generators))
    if unbound:
        problems.append('Generated inputs without matching chronological seed binding')
    if generated_inputs == 0:
        problems.append('No generator input observed; mechanism was not exercised')
    invariant_passed = not problems
    corrected_path_exercised = changed_seed_refreshes > 0
    return {'passed': invariant_passed and corrected_path_exercised,
            'binding_invariant_passed': invariant_passed,
            'corrected_path_exercised': corrected_path_exercised,
            'live_mechanism_gate_passed': invariant_passed and corrected_path_exercised,
            'mechanism_status': ('failed' if not invariant_passed else
                                 'exercised' if corrected_path_exercised else 'inconclusive'),
            'inconclusive_reason': ('No immediately accepted changed source was followed without restart by a verified fresh plan and bound generation'
                                    if invariant_passed and not corrected_path_exercised else None),
            'original_seed_source_sha256': original_sha,
            'changed_seed_refreshes_exercised': changed_seed_refreshes,
            'problems': problems,
            'fresh_plans': sum(p['method'] == 'plan' for p in plans),
            'restart_plans': sum(p['method'] == 'restart_plan' for p in plans),
            'changed_input_seeds': changed_seeds, 'generated_inputs': generated_inputs,
            'unbound_generated_inputs': unbound,
            'journal_planner_seed_available': sum(p['journal_seed_available'] for p in plans),
            'journal_planner_seed_unavailable': sum(not p['journal_seed_available'] for p in plans),
            'plans': plans, 'iterations': details}


def main():
    sys.path.insert(0, str(ROOT))
    from autortl.config import RunConfig
    from autortl.fsm import Orchestrator
    from autortl.state import atomic_write_text
    from autortl.vivado import xsim_run
    from autortl.triage import FailureKind
    from autortl.contract_context import tool_exit_evidence

    if OUTPUT.exists():
        raise RuntimeError('Never reset, overwrite, or resume seed-binding-live-01')
    default = RunConfig.__dataclass_fields__['proposal_feedback'].default
    if default is not False:
        raise RuntimeError('Integrate default-off configuration before this actual validation')
    old_plan = read(STUDY / 'plan.json')
    seed, tb = STUDY / 'seed.v', STUDY / 'tb.v'
    if sha(seed) != old_plan['seed_sha256'] or sha(tb) != old_plan['testbench_sha256']:
        raise RuntimeError('Study02 frozen seed/testbench changed; do not regenerate them')
    binroot = 'C:/AMDDesignTools/2025.2/Vivado/bin/'
    # Omit proposal_feedback deliberately: this validates the actual False default.
    cfg = RunConfig(mode='optimize', top_module='iterative_divider_core',
        design_path=seed, testbench_path=tb, max_iterations=3, best_of_n=1,
        max_llm_calls=16, max_vivado_minutes=25, max_wall_minutes=35,
        max_infra_retries=1, vivado_bin=binroot+'vivado.bat',
        xvlog_bin=binroot+'xvlog.bat', xelab_bin=binroot+'xelab.bat',
        xsim_bin=binroot+'xsim.bat', work_dir=OUTPUT)
    if cfg.proposal_feedback is not False:
        raise RuntimeError('New configuration did not use False default')
    plan = {'schema_version': 1, 'helper_path': str(Path(__file__).resolve()),
        'helper_sha256': sha(__file__), 'study02_plan_sha256': sha(STUDY/'plan.json'),
        'seed_path': str(seed), 'seed_sha256': sha(seed),
        'original_seed_source_sha256': text_sha(seed.read_text(encoding='utf-8')),
        'testbench_path': str(tb), 'testbench_sha256': sha(tb),
        'runtime_source': identities(),
        'git_commit': subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
        'config': cfg.to_dict(), 'proposal_feedback_default': default,
        'proposal_feedback_explicit_override': False,
        'task': 'Actual seed-bound planning using unchanged study02 core seed and independent six-width checker',
        'claim_limit': 'Mechanism and verified completion only; no repeated-code benefit or causal PPA claim',
        'independent_timeout_seconds': 90,
        'independent_budget_scope': 'Separate exact saved winner check; not charged to optimization budget',
        'stats_scope': 'Raw router stats appended during owned run; requires no concurrent model job'}
    plan['mechanism_gate'] = 'Require binding invariant and an immediately accepted changed-source fresh-plan generation without intervening restart; otherwise inconclusive, with no automatic rerun or reset'
    OUTPUT.mkdir(parents=True, exist_ok=False)
    atomic_write_text(OUTPUT/'prelaunch-plan.json', json.dumps(plan, indent=2))
    print(json.dumps({'prelaunch_plan': str(OUTPUT/'prelaunch-plan.json'),
                      'git_commit': plan['git_commit'], 'source_files': len(plan['runtime_source'])}), flush=True)
    if identities() != plan['runtime_source'] or sha(__file__) != plan['helper_sha256']:
        raise RuntimeError('Source/helper changed after prelaunch freeze')
    stats = ROOT/'llm/router_stats.jsonl'
    before = stats.read_bytes() if stats.exists() else b''
    start = time.monotonic()
    orchestrator = Orchestrator(cfg, OUTPUT)
    exception = None
    try:
        result = orchestrator.run()
    except Exception as error:
        exception = {'type': type(error).__name__, 'message': str(error)}
        atomic_write_text(OUTPUT/'validation-exception.txt', traceback.format_exc())
        result = {'status': 'validation_exception'}
    elapsed = time.monotonic() - start
    atomic_write_text(OUTPUT/'actual-result.json', json.dumps(result, indent=2))
    stats_after = stats.read_bytes() if stats.exists() else b''
    stats_prefix_unchanged = stats_after.startswith(before)
    raw_stats = stats_after[len(before):] if stats_prefix_unchanged else stats_after
    (OUTPUT/'validation-router-stats.jsonl').write_bytes(raw_stats)
    rows, malformed = [], []
    for index, line in enumerate(raw_stats.splitlines()):
        try:
            rows.append(json.loads(line))
        except (ValueError, TypeError):
            malformed.append(index + 1)
    names = ('input_tokens', 'cached_input_tokens', 'output_tokens')
    known = {name: sum(type((row.get('metadata', {}).get('usage') or {}).get(name)) is int
                       for row in rows) for name in names}
    usage = {name: sum((row.get('metadata', {}).get('usage') or {}).get(name) or 0 for row in rows)
             if rows and known[name] == len(rows) and not malformed else None for name in names}
    audit = audit_bindings(OUTPUT, plan['original_seed_source_sha256'])
    atomic_write_text(OUTPUT/'binding-audit.json', json.dumps(audit, indent=2))
    saved = OUTPUT/'iterative_divider_core_best.v'
    independent = {'attempted': False, 'passed': False}
    independent_start = time.monotonic()
    if result.get('status') == 'done':
        directory = OUTPUT/'validation-independent'
        directory.mkdir(exist_ok=False)
        try:
            state = read(OUTPUT/'state.json')
            saved_sha = sha(saved)
            if state.get('phase') != 'DONE' or state.get('best_sha256') != saved_sha:
                raise ValueError('Saved winner does not match actual DONE identity')
            copied, copied_tb = directory/'winner.v', directory/'tb.v'
            copied.write_bytes(saved.read_bytes())
            copied_tb.write_bytes(tb.read_bytes())
            immutable = {str(saved): saved_sha, str(copied): sha(copied), str(copied_tb): sha(copied_tb),
                         str(seed): plan['seed_sha256'], str(tb): plan['testbench_sha256']}
            atomic_write_text(directory/'inputs.json', json.dumps(immutable, indent=2))
            independent['attempted'] = True
            okay, error, kind = xsim_run([copied], copied_tb, 'iterative_divider_core_tb',
                                       cfg, directory, timeout=90)
            raw = (directory/'sim_log.txt').read_text(errors='replace') if (directory/'sim_log.txt').is_file() else ''
            exits = tool_exit_evidence(directory)
            exit_ok = exits.get('schema_valid') and all(
                exits.get('latest_by_tool', {}).get(tool, {}).get('successful')
                for tool in ('xvlog', 'xelab', 'xsim'))
            unchanged = all(Path(path).is_file() and sha(path) == digest for path, digest in immutable.items())
            independent.update({'passed': bool(okay is True and kind == FailureKind.DESIGN
                and re.search(r'(?m)^\s*TEST PASSED\s*$', raw)
                and not re.search(r'FAIL|watchdog|timeout|timed\s+out', raw, re.I)
                and exit_ok and unchanged and sha(copied) == saved_sha),
                'error': error, 'failure_kind': kind.value, 'winner_sha256': saved_sha,
                'copy_sha256': sha(copied), 'immutable_inputs_unchanged': unchanged,
                'successful_exit_receipts': bool(exit_ok), 'process_exits': exits})
        except Exception as error:
            independent['exception'] = {'type': type(error).__name__, 'message': str(error)}
            atomic_write_text(directory/'validation-exception.txt', traceback.format_exc())
        atomic_write_text(directory/'result.json', json.dumps(independent, indent=2))
    report = {'schema_version': 1, 'status': result.get('status'),
        'independent': independent, 'binding_audit_passed': audit['binding_invariant_passed'],
        'corrected_path_exercised': audit['corrected_path_exercised'],
        'changed_seed_refreshes_exercised': audit['changed_seed_refreshes_exercised'],
        'live_mechanism_gate_passed': audit['live_mechanism_gate_passed'],
        'mechanism_status': audit['mechanism_status'],
        'inconclusive_reason': audit['inconclusive_reason'],
        'fresh_plans': audit['fresh_plans'], 'restart_plans': audit['restart_plans'],
        'changed_input_seeds': audit['changed_input_seeds'],
        'generated_inputs': audit['generated_inputs'],
        'unbound_generated_inputs': audit['unbound_generated_inputs'],
        'budget': read(OUTPUT/'budget.json') if (OUTPUT/'budget.json').is_file() else None,
        'elapsed_seconds': elapsed, 'independent_seconds': time.monotonic()-independent_start,
        'provider_records': len(rows), 'reported_usage': usage, 'usage_known_calls': known,
        'malformed_stats_lines': malformed, 'stats_prefix_unchanged': stats_prefix_unchanged,
        'models_observed': sorted({str(row.get('metadata', {}).get('model')) for row in rows}),
        'model_identity_note': 'Observed metadata may contain routing aliases; actual model identity is not inferred',
        'exception': exception, 'runtime_source_unchanged': identities() == plan['runtime_source'],
        'helper_unchanged': sha(__file__) == plan['helper_sha256'],
        'study02_plan_unchanged': sha(STUDY/'plan.json') == plan['study02_plan_sha256'],
        'seed_unchanged': sha(seed) == plan['seed_sha256'], 'testbench_unchanged': sha(tb) == plan['testbench_sha256'],
        'claim_limit': plan['claim_limit']}
    report['passed'] = bool(result.get('status') == 'done' and independent['passed'] and audit['live_mechanism_gate_passed']
        and report['runtime_source_unchanged'] and report['helper_unchanged']
        and report['study02_plan_unchanged'] and report['seed_unchanged'] and report['testbench_unchanged']
        and stats_prefix_unchanged and not malformed)
    atomic_write_text(OUTPUT/'validation-result.json', json.dumps(report, indent=2))
    manifest = {path.relative_to(OUTPUT).as_posix(): sha(path) for path in OUTPUT.rglob('*') if path.is_file()}
    atomic_write_text(OUTPUT/'validation-manifest.json', json.dumps(manifest, indent=2))
    print(json.dumps(report), flush=True)
    if not report['passed']:
        raise RuntimeError('Actual validation failed or was inconclusive; retain artifacts, do not reset or automatically rerun')


if __name__ == '__main__':
    main()
