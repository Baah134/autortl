"""Measure a frozen generated FIR unit grader; never regrade the original run.

Preparation alone does not execute tools. Run only after build01 and its
independent proof have been archived. Missed mutants are measured outcomes,
not permission to alter this attempt's grader, stimulus, or denominator.
"""
import hashlib
import json
import re
import runpy
import shutil
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('C:/Users/prince.baah/Downloads/autortl-work')
WORK = Path(__file__).resolve().parent
RUN = ROOT / 'logs/build-signed-fir4-01'
OUT = ROOT / 'logs/signed-fir4-generated-audit-01'
ARCHIVE = ROOT / 'evidence/2026-10-26/generated-signed-fir4-attempt-01'
ADMISSION = ROOT / 'evidence/2026-10-25/signed-fir4-admission-attempt-01'
MODULE = RUN / 'modules/signed_fir4_core'
TB = MODULE / 'signed_fir4_core_tb.v'
GOLDEN = MODULE / 'golden.py'
STIMULUS = MODULE / 'stimulus.json'
STATS = ROOT / 'llm/router_stats.jsonl'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def utc():
    return datetime.now(timezone.utc).isoformat()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2), encoding='utf-8')


def verify_manifest(directory):
    manifest = read(directory / 'archive-manifest.json')
    assert manifest and isinstance(manifest, dict)
    for relative, digest in manifest.items():
        target = (directory / relative).resolve()
        assert target.is_relative_to(directory.resolve()), relative
        assert sha(target) == digest, relative
    return manifest


def source_identities():
    result = {}
    for name in ('autortl', 'llm', 'tests', 'curriculum', 'scripts', 'data', '.claude'):
        for path in (ROOT / name).rglob('*'):
            if (path.is_file() and path.suffix in ('.py', '.v', '.sv', '.json', '.yaml', '.md')
                    and '__pycache__' not in path.parts):
                result[path.relative_to(ROOT).as_posix()] = sha(path)
    result['run.py'] = sha(ROOT / 'run.py')
    return result


def main():
    sys.dont_write_bytecode = True
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.path.insert(0, str(ROOT))
    from autortl.config import RunConfig
    from autortl.contract_context import tool_exit_evidence
    from autortl.triage import FailureKind
    from autortl.vivado import xsim_run
    from scripts.check_build_tbs import verdict

    assert not OUT.exists(), 'Never overwrite or resume an audit attempt'
    source = read(WORK / 'signed-fir4-source-freeze-01.json')
    assert len(source) == 227 and source_identities() == source
    generated_manifest = verify_manifest(ARCHIVE)
    admission_manifest = verify_manifest(ADMISSION)
    archived = read(ARCHIVE / 'result.json')
    assert archived['status'] == 'done' and archived['source_unchanged']
    assert archived['verification']['passed'] and archived['independent_cycles'] == 800
    admission = read(ADMISSION / 'admission/result.json')
    assert admission['qualified'] and admission['planned'] == admission['executed'] == admission['admitted'] == 28
    summary = read(RUN / 'run_summary.json')
    state = read(RUN / 'state.json')
    assert summary['status'] == 'done' and state['phase'] == 'DONE'
    assert all(sha(Path(path)) == digest for path, digest in state['final_artifacts'].items())

    required = [RUN / name for name in ('state.json', 'runtime.json', 'config.json', 'budget.json',
                'inputs.json', 'run_summary.json')]
    required += [GOLDEN, TB, STIMULUS]
    for path in required:
        relative = 'run/' + path.relative_to(RUN).as_posix()
        assert generated_manifest.get(relative) == sha(path), relative
    protected = {Path(path) for path in state['final_artifacts']}
    protected.update(required)
    protected.update(Path(row['path']) for row in read(RUN / 'inputs.json').values())
    protected.add(STATS)
    before = {str(path): sha(path) for path in protected}
    original_files = {path.relative_to(RUN).as_posix() for path in RUN.rglob('*') if path.is_file()}
    budget = read(RUN / 'budget.json')
    stats_sha = sha(STATS)
    helper_sha = sha(Path(__file__))
    cases_path = ROOT / 'curriculum/tier3/signed_fir4_build/qualification/cases.py'
    variants = runpy.run_path(str(cases_path))['case_sources']()
    assert len(variants) == 28 and next(iter(variants)) == 'reference'
    assert len(set(variants.values())) == 28
    case_hashes = {}
    for name, text in variants.items():
        assert re.fullmatch(r'[a-z][a-z0-9_]*', name)
        digest = hashlib.sha256(text.encode('utf-8')).hexdigest()
        archived_path = 'admission/' + name + '/children.v'
        assert admission_manifest.get(archived_path) == digest
        case_hashes[name] = digest
    cfg = RunConfig.load(RUN / 'config.json')
    OUT.mkdir(parents=True, exist_ok=False)
    plan = {
        'schema_version': 1, 'started_utc': utc(), 'helper_sha256': helper_sha,
        'python_version': sys.version, 'python_executable_sha256': sha(Path(sys.executable)),
        'runtime_source': source, 'original_run': str(RUN), 'original_identities': before,
        'original_file_set': sorted(original_files), 'original_budget': budget,
        'router_stats_sha256': stats_sha, 'case_materializer_sha256': sha(cases_path),
        'generated_archive': str(ARCHIVE), 'generated_manifest_sha256': sha(ARCHIVE / 'archive-manifest.json'),
        'independent_admission': str(ADMISSION), 'admission_manifest_sha256': sha(ADMISSION / 'archive-manifest.json'),
        'unit_tb_sha256': sha(TB), 'golden_sha256': sha(GOLDEN), 'stimulus_sha256': sha(STIMULUS),
        'case_child_sha256': case_hashes, 'planned_cases': 28, 'planned_faults': 27,
        'command': 'xsim_run([children.v], copied frozen unit TB, signed_fir4_core_tb, original RunConfig, fresh case directory, timeout=90)',
        'target_part': cfg.target_part, 'target_freq_mhz': cfg.target_freq_mhz,
        'model_calls': 0, 'synthesis_calls': 0,
        'scope': 'Frozen generated unit-grader sensitivity, compared with already admitted identical faults. No original-run regrade or resume; all27 faults remain in denominator.',
    }
    write(OUT / 'prelaunch-plan.json', plan)
    rows = []
    fatal = None
    tick = time.monotonic()
    control_passed = False

    def invariants():
        return {
            'source227_unchanged': source_identities() == source,
            'original_identities_unchanged': all(path.is_file() and sha(path) == before[str(path)] for path in protected),
            'original_file_set_unchanged': original_files == {path.relative_to(RUN).as_posix() for path in RUN.rglob('*') if path.is_file()},
            'original_budget_unchanged': read(RUN / 'budget.json') == budget,
            'router_stats_unchanged': sha(STATS) == stats_sha,
            'helper_unchanged': sha(Path(__file__)) == helper_sha,
        }

    try:
        for name, text in variants.items():
            directory = OUT / name
            directory.mkdir()
            child = directory / 'children.v'
            tb = directory / TB.name
            child.write_bytes(text.encode('utf-8'))
            shutil.copyfile(TB, tb)
            inputs = {str(child): case_hashes[name], str(tb): plan['unit_tb_sha256']}
            assert all(sha(Path(path)) == digest for path, digest in inputs.items())
            started = utc()
            case_tick = time.monotonic()
            exception = None
            try:
                passed, error, kind = xsim_run([child], tb, 'signed_fir4_core_tb', cfg, directory, timeout=90)
            except Exception:
                passed, error, kind = False, 'audit invocation exception', FailureKind.INFRA
                exception = traceback.format_exc()
            seconds = time.monotonic() - case_tick
            exits = tool_exit_evidence(directory)
            exit_ok = bool(exits['schema_valid'] and all(
                exits['latest_by_tool'].get(tool, {}).get('successful') for tool in ('xvlog', 'xelab', 'xsim')))
            raw_path = directory / 'sim_log.txt'
            raw = raw_path.read_text(encoding='utf-8', errors='replace') if raw_path.is_file() else ''
            unchanged = all(sha(Path(path)) == digest for path, digest in inputs.items())
            result = verdict(name == 'reference', passed, error, kind, raw)
            clean_pass = verdict(True, passed, error, kind, raw)['ok']
            valid = exit_ok and unchanged and exception is None and kind == FailureKind.DESIGN
            if name == 'reference':
                control_passed = bool(valid and result['ok'])
                grade = 'control_passed' if control_passed else 'control_failed'
            elif valid and result['ok']:
                grade = 'detected'
            elif valid and clean_pass:
                grade = 'missed'
            else:
                grade = 'ungraded'
            row = {
                'name': name, 'grade': grade, 'simulation_passed': passed, 'failure_kind': kind.value,
                'error': error, 'exception': exception, 'started_utc': started, 'ended_utc': utc(),
                'elapsed_seconds': seconds, 'input_hashes': inputs, 'inputs_unchanged': unchanged,
                'actual_successful_tool_exits': exit_ok, 'process_exits': exits, 'verdict': result,
                'raw_log_path': str(raw_path), 'raw_log_sha256': sha(raw_path) if raw_path.is_file() else None,
                'assertions': re.findall(r'^\s*FAIL\b[^\n]*', raw, re.MULTILINE),
                'independent_admission_detected': name != 'reference',
            }
            rows.append(row)
            write(directory / 'audit-result.json', row)
            write(OUT / 'rows.json', rows)
            print(json.dumps({'name': name, 'grade': grade, 'seconds': seconds}), flush=True)
            checks = invariants()
            if not all(checks.values()):
                raise RuntimeError('Protected input/source drift: ' + json.dumps(checks))
            if name == 'reference' and not control_passed:
                break
    except BaseException:
        fatal = traceback.format_exc()
        (OUT / 'fatal.txt').write_text(fatal, encoding='utf-8')
    try:
        checks = invariants()
    except Exception:
        checks = {'integrity_check_completed': False}
        fatal = (fatal or '') + '\n' + traceback.format_exc()
    mutants = rows[1:] if rows and rows[0]['name'] == 'reference' else []
    names = {category: [row['name'] for row in mutants if row['grade'] == category]
             for category in ('detected', 'missed', 'ungraded')}
    executed = {row['name'] for row in rows}
    not_executed = [name for name in variants if name != 'reference' and name not in executed]
    complete = control_passed and len(rows) == 28 and not names['ungraded'] and not fatal and all(checks.values())
    actual_tool_seconds = sum(record.get('elapsed_seconds', 0) for row in rows
                              for record in row['process_exits'].get('records', []))
    result = {
        'status': 'completed' if complete else 'incomplete', 'control_passed': control_passed,
        'planned_cases': 28, 'planned_faults': 27, 'executed_cases': len(rows),
        'detected': len(names['detected']), 'missed': len(names['missed']),
        'ungraded': len(names['ungraded']) + len(not_executed), 'not_executed': not_executed,
        'detected_names': names['detected'], 'missed_names': names['missed'], 'ungraded_names': names['ungraded'],
        'independent_detected': 27, 'source_files': 227, 'original_identities': before,
        'original_budget': budget, 'original_router_stats_sha256': stats_sha,
        'integrity': checks, 'model_calls': 0, 'synthesis_calls': 0,
        'elapsed_seconds': time.monotonic() - tick, 'actual_tool_seconds': actual_tool_seconds,
        'ended_utc': utc(), 'fatal': fatal, 'results': rows,
        'scope': 'Selected fault sensitivity under frozen stimulus, not formal equivalence, a model-strength comparison, or a regrade of build01.',
    }
    write(OUT / 'result.json', result)
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ('results', 'original_identities', 'original_budget')}), flush=True)
    return 0 if complete else 1


if __name__ == '__main__':
    raise SystemExit(main())
