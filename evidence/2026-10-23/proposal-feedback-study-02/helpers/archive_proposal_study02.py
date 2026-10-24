"""Archive study02 only after six original rows, comparison, and DONE proof exist.

Prepared for coordinator review; importing this file does not write anything.
Execution creates a new archive and never rewrites study rows or their costs.
"""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path('C:/Users/prince.baah/Downloads/autortl-work')
WORK = Path('C:/Users/prince.baah/Documents/Codex/2026-10-15/hey')
STUDY = ROOT/'logs/proposal-feedback-study-02'
DONE = ROOT/'logs/proposal-feedback-study-02-done-check'
OUT = ROOT/'evidence/2026-10-23/proposal-feedback-study-02'
FULLSUITE = ROOT/'evidence/2026-10-23/proposal-feedback-tests-01'
ALLOWED = {'.v', '.sv', '.py', '.json', '.jsonl', '.log', '.txt', '.rpt',
           '.md', '.yaml', '.yml', '.xdc', '.tcl'}
EXCLUDED = {'artifacts', 'xsim.dir', '.xil', '__pycache__', '.pytest_cache'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    require(not OUT.exists(), f'Archive already exists: {OUT}')
    frozen_path = WORK/'work/proposal-source-freeze-01.json'
    frozen = load(frozen_path)
    require(len(frozen) == 202, 'Expected original 202-file freeze')
    require(all(sha(ROOT/name) == digest for name, digest in frozen.items()),
            'Current source differs from original frozen source')
    plan = load(STUDY/'plan.json')
    require(plan['runtime_source'] == frozen, 'Plan/freeze source mismatch')
    require(plan['order'] == [[1, False], [1, True], [2, True], [2, False],
                              [3, False], [3, True]], 'Unexpected study order')
    require(sha(WORK/'work/proposal_study02.py') == plan['helper_sha256'],
            'Frozen study helper changed')
    for name, key in [('seed.v', 'seed_sha256'), ('tb.v', 'testbench_sha256')]:
        require(sha(STUDY/name) == plan[key], f'Frozen {name} changed')
    for source in plan['sources']:
        require(sha(Path(source['path'])) == source['sha256'],
                f'Original seed/wrapper changed: {source["path"]}')

    rows = []
    runtime_checks = {}
    for pair, feedback in plan['order']:
        name = f'pair{pair}-{"feedback" if feedback else "baseline"}'
        run = STUDY/name
        row = load(run/'study-result.json')
        require(row['pair'] == pair and row['feedback'] is feedback,
                f'Row identity mismatch: {name}')
        require(row['runtime_source_unchanged'] is True, f'Row source drift: {name}')
        runtime = load(run/'runtime.json')['implementation']
        require(bool(runtime), f'Empty runtime manifest: {name}')
        require(all(frozen.get(p) == h and sha(ROOT/p) == h
                    for p, h in runtime.items()), f'Runtime source drift: {name}')
        if (pair, feedback) == (2, False):
            require(row['status'] == 'model_blocked', 'Original quota row was replaced')
            recovery = load(run/'quota-resume/result.json')
            require(recovery['status'] == 'done' and recovery['independent_passed'] is True,
                    'Quota recovery incomplete')
            require(recovery['original_blocked_result_unchanged'] is True
                    and recovery['no_budget_reset'] is True, 'Quota recovery evidence invalid')
            require((run/'quota-resume/before-study-result.json').read_bytes()
                    == (run/'study-result.json').read_bytes(), 'Original blocked row changed')
            require(recovery['budget_before']['llm_calls'] == row['budget']['llm_calls']
                    and recovery['budget_after']['llm_calls']
                    == recovery['budget_before']['llm_calls'] + recovery['additional_model_calls'],
                    'Recovery call accounting mismatch')
        else:
            require(row['status'] == 'done' and row['independent_passed'] is True,
                    f'Planned original row incomplete: {name}')
        require(load(run/'state.json')['phase'] == 'DONE'
                and load(run/'run_summary.json')['status'] == 'done',
                f'Final runtime state incomplete: {name}')
        runtime_checks[name] = {'runtime_files': len(runtime), 'all_match_freeze': True,
                               'original_row_sha256': sha(run/'study-result.json')}
        rows.append((name, row))

    comparison = load(STUDY/'comparison.json')
    require((STUDY/'COMPARISON.md').is_file(), 'Missing readable comparison')
    require(comparison['plan_sha256'] == sha(STUDY/'plan.json'), 'Comparison plan mismatch')
    require(len(comparison['trials']) == 6, 'Comparison omitted planned rows')
    for (name, row), compared in zip(rows, comparison['trials']):
        require(all(compared.get(k) == v for k, v in row.items())
                and compared['result_sha256'] == sha(STUDY/name/'study-result.json'),
                f'Comparison rewrote original row: {name}')

    done = load(DONE/'result.json')
    for key in ('ok', 'all_restored_unchanged', 'file_set_unchanged',
                'budget_and_router_stats_unchanged', 'no_new_model_or_tool_charges'):
        require(done.get(key) is True, f'DONE proof incomplete: {key}')
    codes = done['cli_exit_codes']
    require(codes.get('nominal') == 0 and all(
        type(codes.get(k)) is int and codes[k] != 0 for k in
        ('feedback_input', 'feedback_outcome', 'prior_standard_source', 'prior_standard_script')),
        'Missing actual DONE/tamper outcomes')
    require(Path(done['run']).resolve() in [
        (STUDY/name).resolve() for name, _ in rows], 'DONE proof covers another study')
    require(all(sha(Path(p)) == h for p, h in done['identities'].items()),
            'DONE proof protected identities subsequently changed')
    for name, digest in load(DONE/'archive-manifest.json').items():
        require(sha(DONE/name) == digest, f'DONE proof file changed: {name}')
    require(load(FULLSUITE/'source-freeze.json') == frozen,
            'Fullsuite source freeze mismatch')
    fullsuite = load(FULLSUITE/'result.json')
    require(fullsuite['passed'] == 1301 and fullsuite['source_unchanged'] is True,
            'Expected completed 1301-test gate')
    for name, digest in load(FULLSUITE/'archive-manifest.json').items():
        require(sha(FULLSUITE/name) == digest, f'Fullsuite evidence changed: {name}')

    # Build every copy operation before creating the archive. Hashes protect
    # against inputs changing between preflight and copying.
    copies = {}

    def add(source, relative):
        source = source.resolve()
        relative = Path(relative)
        require(source.is_file(), f'Missing archive input: {source}')
        require(not relative.is_absolute() and '..' not in relative.parts,
                f'Unsafe archive path: {relative}')
        require(relative.as_posix() not in copies, f'Duplicate archive path: {relative}')
        copies[relative.as_posix()] = (source, sha(source))

    def tree(source, prefix):
        require(source.is_dir(), f'Missing archive tree: {source}')
        for path in sorted(source.rglob('*')):
            relative = path.relative_to(source)
            if path.is_file() and path.suffix.lower() in ALLOWED and not any(
                    p.lower() in EXCLUDED for p in relative.parts):
                require(not path.is_symlink(), f'Unexpected source symlink: {path}')
                add(path, Path(prefix)/relative)

    tree(STUDY, 'study')
    tree(DONE, 'done-check')
    tree(FULLSUITE, 'fullsuite')
    add(frozen_path, 'source-freeze.json')
    for name in frozen:
        add(ROOT/name, Path('source-snapshot')/name)
    for source in plan['sources']:
        path = Path(source['path'])
        add(path, Path('original-seed-sources')/path.relative_to(ROOT/'logs/build-golden-divider-01'))
    for name in ('proposal_study02.py', 'report_proposal_study.py', 'check_proposal_done.py',
                 'archive_proposal_study02.py'):
        add(WORK/'work'/name, Path('helpers')/name)
    required_console = ['AutoRTL-proposal-study02-prepare.txt',
                        *[f'AutoRTL-proposal-study02-{i}.txt' for i in range(6)],
                        'AutoRTL-proposal-study02-quota-resume.txt',
                        'AutoRTL-proposal-full-01.txt']
    for name in required_console:
        require((WORK/'outputs'/name).is_file(), f'Missing raw console: {name}')
    consoles = set(WORK.joinpath('outputs').glob('AutoRTL-proposal-study02*.txt'))
    consoles.update(WORK.joinpath('outputs').glob('AutoRTL-proposal*done*.txt'))
    consoles.add(WORK/'outputs/AutoRTL-proposal-full-01.txt')
    for path in sorted(consoles):
        add(path, Path('console')/path.name)

    OUT.mkdir(parents=True, exist_ok=False)
    for name, (source, digest) in copies.items():
        require(sha(source) == digest, f'Archive input changed: {source}')
        target = OUT/name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        require(sha(target) == digest, f'Copy verification failed: {name}')
    verification = {'source_files': len(frozen), 'current_source_matches_freeze': True,
                    'runs': runtime_checks, 'original_pair2_blocked_row_retained': True,
                    'supplemental_quota_recovery_retained_separately': True,
                    'done_proof_verified': True, 'copy_sources': {
                        name: {'path': str(source), 'sha256': digest}
                        for name, (source, digest) in copies.items()}}
    (OUT/'source-verification.json').write_text(json.dumps(verification, indent=2)+'\n', encoding='utf-8')
    (OUT/'README.md').write_text(
        '# Previous-proposal feedback study02\n\n'
        'Six original chronological paired rows are retained in study/. Pair2 baseline '
        'remains model_blocked; its supplemental quota recovery is archived separately. '
        'See study/COMPARISON.md and comparison.json for the actual decision and limits.\n\n'
        'All 202 frozen source identities and each run runtime manifest were verified. '
        'Fullsuite evidence and actual DONE reuse/restored tamper proof are included. '
        'Only source/report/journal text formats were copied; artifacts/, xsim.dir/ and '
        '.Xil/ build trees are excluded. This archive does not claim rerunnable binary '
        'tool builds, a complete uninterrupted efficacy comparison, or model superiority.\n', encoding='utf-8')
    manifest = {p.relative_to(OUT).as_posix(): sha(p)
                for p in sorted(OUT.rglob('*')) if p.is_file()}
    (OUT/'archive-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    require(all(sha(OUT/name) == digest for name, digest in manifest.items()),
            'Final archive manifest verification failed')
    require(all(sha(ROOT/name) == digest for name, digest in frozen.items()),
            'Frozen source changed during archival')
    print(json.dumps({'archive': str(OUT), 'manifest_files': len(manifest),
                      'bytes': sum((OUT/name).stat().st_size for name in manifest),
                      'source_files_verified': 202, 'original_rows': 6,
                      'original_blocked_row_retained': True, 'done_proof_verified': True}))


if __name__ == '__main__':
    main()
