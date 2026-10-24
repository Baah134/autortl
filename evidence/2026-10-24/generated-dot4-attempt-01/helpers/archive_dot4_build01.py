"""Prepared archive helper: execute only after actual dot4 verification completes.

No work occurs on import. This helper does not run models, tools, tests or Git.
All readiness checks precede creation of the new canonical evidence directory.
"""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path('C:/Users/prince.baah/Downloads/autortl-work')
WORK = Path('C:/Users/prince.baah/Documents/Codex/2026-10-15/hey')
RUN = ROOT/'logs/build-dot4-01'
PROOF = ROOT/'logs/build-dot4-01-verification'
PLAN = ROOT/'logs/build-dot4-01-prelaunch.json'
STAGE = WORK/'work/dot4-fixture-stage'
OUT = ROOT/'evidence/2026-10-24/generated-dot4-attempt-01'
CHILDREN = ('dot4_pair01', 'dot4_pair23', 'dot4_merge')
ALLOWED = {'.v', '.sv', '.py', '.json', '.jsonl', '.log', '.txt', '.rpt',
           '.md', '.yaml', '.yml', '.xdc', '.tcl', '.jou'}
EXCLUDED = {'artifacts', 'xsim.dir', '.xil', '__pycache__', '.pytest_cache'}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def verify_manifest(path):
    manifest = read(path)
    require(isinstance(manifest, dict) and bool(manifest), f'Empty manifest: {path}')
    for name, digest in manifest.items():
        target = (path.parent/name).resolve()
        require(target.is_relative_to(path.parent.resolve()), f'Unsafe manifest path: {name}')
        require(target.is_file() and sha(target) == digest, f'Manifest mismatch: {target}')


def main():
    require(not OUT.exists(), f'Archive already exists: {OUT}')
    plan = read(PLAN)
    frozen = plan['runtime_source']
    require(len(frozen) == 203, 'Expected original 203-file runtime source freeze')
    require(all(sha(ROOT/name) == digest for name, digest in frozen.items()),
            'Source changed; archive before integrating a runtime patch')
    require(len(plan['fixture_hashes']) == 7, 'Expected seven frozen fixture files')
    require(all(sha(STAGE/name) == digest for name, digest in plan['fixture_hashes'].items()),
            'Frozen fixture inputs changed')
    require(Path(plan['spec_path']).resolve() == (STAGE/'design_spec.json').resolve()
            and sha(Path(plan['spec_path'])) == plan['spec_sha256'], 'Spec input changed')
    require(Path(plan['tb_path']).resolve() == (STAGE/'dot4_pipeline_tb.v').resolve()
            and sha(Path(plan['tb_path'])) == plan['tb_sha256'], 'Independent TB changed')
    require(plan['reference_is_not_a_generation_input'] is True, 'Unexpected reference input')
    admission = Path(plan['admission_archive'])
    require(sha(admission/'archive-manifest.json') == plan['admission_manifest_sha256'],
            'Admission manifest binding changed')
    verify_manifest(admission/'archive-manifest.json')
    require(len(read(admission/'archive-manifest.json')) == 144, 'Unexpected admission archive size')
    admission_plan = read(admission/'admission/prelaunch-plan.json')
    admitted = read(admission/'admission/result.json')
    require(admission_plan['runtime_source'] == frozen
            and admission_plan['stage_files'] == plan['fixture_hashes'], 'Admission freeze mismatch')
    require(admitted['qualified'] is True and admitted['admitted'] == admitted['executed']
            == admitted['planned'] == 13, 'Independent checker not admitted 13/13')
    require(all(admitted[k] is True for k in
                ('runtime_source_unchanged', 'stage_unchanged', 'router_stats_unchanged'))
            and admitted['model_calls'] == 0, 'Admission integrity mismatch')

    summary, state = read(RUN/'run_summary.json'), read(RUN/'state.json')
    require(summary['status'] == 'done' and state['phase'] == 'DONE'
            and summary['top_module'] == 'dot4_pipeline', 'Build is not DONE')
    runtime = read(RUN/'runtime.json')['implementation']
    require(bool(runtime) and all(frozen.get(name) == digest
            and sha(ROOT/name) == digest for name, digest in runtime.items()), 'Runtime manifest mismatch')
    saved = RUN/'dot4_pipeline_best.v'
    measured = Path(summary['best_artifact_dir'])/'dot4_pipeline.v'
    require(sha(saved) == state['best_sha256'], 'Saved winner identity mismatch')
    require(saved.read_bytes().replace(b'\r\n', b'\n')
            == measured.read_bytes().replace(b'\r\n', b'\n'), 'Saved/measured source differs')
    require(all(sha(Path(name)) == digest for name, digest in state['final_artifacts'].items()),
            'Final artifact source/report identities changed')
    for name in CHILDREN:
        child = RUN/'modules'/name/(name+'.v')
        require(state['final_artifacts'].get(str(child.resolve())) == sha(child),
                f'Generated child is not final-bound: {name}')
        require((child.parent/'golden.py').is_file(), f'Missing generated golden: {name}')
    inputs = read(RUN/'inputs.json')
    require(sha(Path(inputs['testbench_path']['path'])) == plan['tb_sha256'], 'Run TB drift')
    baseline, best, budget = summary['baseline_metrics'], summary['best_metrics'], read(RUN/'budget.json')
    for key, before, after in [('lut_used', 325, 17), ('ff_used', 52, 18), ('dsp_used', 0, 4),
                               ('wns_ns', .087, .354), ('whs_ns', .202, .254),
                               ('total_power_w', .157, .158)]:
        require(baseline[key] == before and best[key] == after, f'Unexpected measured {key}')
    require(budget['llm_calls'] == 11, 'Unexpected model call total')

    proof = read(PROOF/'result.json')
    for key in ('passed', 'independent_exact_top_and_three_children', 'all_restored_unchanged',
                'budget_stats_and_file_set_unchanged', 'no_new_model_or_optimization_tool_charges',
                'runtime_source_unchanged'):
        require(proof.get(key) is True, f'Actual verification incomplete: {key}')
    require(proof['checked_cycles'] == 685 and proof['budget'] == budget
            and proof['best_metrics'] == best and proof['baseline_metrics'] == baseline,
            'Verification measured result or budget mismatch')
    probes = [*('child_'+name for name in CHILDREN), 'resolved_spec', 'plan_binding',
              'proposal_input', 'proposal_outcome', 'saved_winner']
    codes = proof['cli_exit_codes']
    require(set(codes) == {'nominal', *probes} and codes['nominal'] == 0
            and all(type(codes[name]) is int and codes[name] != 0 for name in probes),
            'Expected nominal DONE reuse and eight restored rejection probes')
    require(all(sha(Path(name)) == digest for name, digest in proof['identities'].items()),
            'Protected source/budget/router identity changed after actual verification')
    independent = read(PROOF/'independent/result.json')
    require(independent['passed'] is True and all(sha(Path(name)) == digest
            for name, digest in independent['identities'].items()), 'Independent exact sources changed')
    require('COVERAGE checked=685 holds=684 resets=5 pulses=1' in
            (PROOF/'independent/sim_log.txt').read_text(encoding='utf-8', errors='replace'),
            'Missing exact independent coverage proof')
    for path in sorted(PROOF.rglob('archive-manifest.json')):
        verify_manifest(path)
    require((PROOF/'archive-manifest.json').is_file(), 'Missing completed verification manifest')

    copies = {}

    def add(source, name):
        source, name = source.resolve(), Path(name)
        require(source.is_file(), f'Missing archive input: {source}')
        require(not name.is_absolute() and '..' not in name.parts, f'Unsafe output path: {name}')
        key = name.as_posix()
        require(key not in copies, f'Duplicate output path: {key}')
        copies[key] = (source, sha(source))

    def tree(source, prefix):
        require(source.is_dir(), f'Missing archive source: {source}')
        for path in sorted(source.rglob('*')):
            relative = path.relative_to(source)
            if path.is_file() and path.suffix.lower() in ALLOWED and not any(
                    part.lower() in EXCLUDED for part in relative.parts):
                require(not path.is_symlink(), f'Unexpected source symlink: {path}')
                add(path, Path(prefix)/relative)

    tree(RUN, 'build-dot4-01')
    tree(PROOF, 'verification')
    tree(admission, 'checker-admission')
    for name in plan['fixture_hashes']:
        add(STAGE/name, Path('fixture')/name)
    add(PLAN, 'build-dot4-01-prelaunch.json')
    add(saved, 'winner/dot4_pipeline_best.v')
    add(measured, 'winner/measured-dot4_pipeline.v')
    for name in frozen:
        add(ROOT/name, Path('source-snapshot')/name)
    for name in ('admit_dot4.py', 'prepare_dot4_build.py', 'verify_dot4_build.py',
                 'archive_dot4_build01.py'):
        add(WORK/'work'/name, Path('helpers')/name)
    for name in ('AutoRTL-build-dot4-01.txt', 'AutoRTL-dot4-admission-01.txt',
                 'AutoRTL-dot4-verification-01.txt'):
        add(WORK/'outputs'/name, Path('console')/name)
    timescale_logs = [name for name, (path, _) in copies.items()
                      if name.startswith('build-dot4-01/') and path.suffix.lower() in
                      {'.log', '.txt', '.json', '.jsonl'} and 'XSIM 43-4099' in
                      path.read_text(encoding='utf-8', errors='replace')]
    require(bool(timescale_logs), 'Original mechanical-top timescale failure not preserved')

    OUT.mkdir(parents=True, exist_ok=False)
    for name, (source, digest) in copies.items():
        require(sha(source) == digest, f'Input changed during archival: {source}')
        target = OUT/name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        require(sha(target) == digest, f'Copied file mismatch: {name}')
    verification = {'runtime_files': len(frozen), 'all_current_frozen_identities_match': True,
                    'runtime_commit_from_prelaunch': plan['git_commit'],
                    'measured_sha256': sha(measured), 'saved_sha256': sha(saved),
                    'saved_measured_equal_after_crlf_only': True, 'checker_admitted': '13/13',
                    'independent_checked_cycles': 685, 'restored_done_probes': 8,
                    'initial_timescale_failure_retained_in': timescale_logs,
                    'baseline_metrics': baseline, 'best_metrics': best, 'budget': budget,
                    'copies': {name: {'source': str(source), 'sha256': digest}
                               for name, (source, digest) in copies.items()}}
    (OUT/'source-verification.json').write_text(json.dumps(verification, indent=2)+'\n', encoding='utf-8')
    (OUT/'source-freeze.json').write_text(json.dumps(frozen, indent=2)+'\n', encoding='utf-8')
    (OUT/'README.md').write_text(
        '# Generated three-child dot-product build\n\n'
        'Three generated RTL children and their generated Python goldens were verified '
        'with the independently admitted top checker. Exact saved top plus three children '
        'passed 685 checked cycles; actual DONE reuse and eight restored tamper probes '
        'preserved sources, budgets, router records and file set.\n\n'
        'Measured baseline to winner: 325 to 17 LUTs, 52 to 18 FFs, 0 to 4 DSPs; '
        'setup slack .087 to .354 ns, hold slack .202 to .254 ns. Total reported power '
        '.157 to .158 W. Resource improvement uses DSP mapping and is not a power gain. '
        'Raw budget and reports provide the recorded costs.\n\n'
        'The original mechanical top lacked a timescale and failed XSIM 43-4099. '
        'The existing baseline repair call added the directive; original failure journals '
        'are retained. This archive precedes any deterministic harness repair.\n\n'
        'Checker admission, seven original fixture files, prelaunch plan, generated sources, '
        'goldens, reports, journals, console outputs and full 203-file source snapshot are '
        'included. Binary artifacts/, xsim.dir/ and .Xil/ trees are excluded. '
        'Nested original manifests describe their original runtime trees; the outer '
        'archive-manifest.json defines the preserved file set. This is one design '
        'experiment, not formal proof or controlled model comparison.\n', encoding='utf-8')
    manifest = {path.relative_to(OUT).as_posix(): sha(path)
                for path in sorted(OUT.rglob('*')) if path.is_file()}
    (OUT/'archive-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    verify_manifest(OUT/'archive-manifest.json')
    require(all(sha(ROOT/name) == digest for name, digest in frozen.items()),
            'Frozen runtime changed during archival')
    print(json.dumps({'archive': str(OUT), 'files': len(manifest),
                      'bytes': sum((OUT/name).stat().st_size for name in manifest),
                      'frozen_sources': len(frozen), 'verified_cycles': 685,
                      'restored_done_probes': 8, 'best_luts': best['lut_used']}))


if __name__ == '__main__':
    main()
