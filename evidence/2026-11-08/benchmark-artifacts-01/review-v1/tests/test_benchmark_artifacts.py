"""Real temporary artifact files; no benchmark, model, vendor or simulator runs."""
import copy
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
from types import SimpleNamespace

import pytest

from benchmark import artifacts as a


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


@pytest.fixture
def sample(tmp_path):
    public = tmp_path / 'public'
    private = tmp_path / 'private'
    rtl = tmp_path / 'rtl-source'
    for directory in (public, private, rtl):
        directory.mkdir()
    (public / 'statement.txt').write_bytes(b'Public task only\r\n')
    (public / 'interface.v').write_bytes(b'module top(input a, output y); endmodule\n')
    sentinel = b'PRIVATE_SENTINEL_MUST_NEVER_EXPORT_3948'
    (private / 'secret-grader.py').write_bytes(sentinel)
    # A private neighbor even in the public directory is not allowlisted.
    (public / 'private-neighbor.txt').write_bytes(sentinel)
    (rtl / 'child.v').write_bytes(b'module child(input a,output y); assign y=a; endmodule\r\n')
    (rtl / 'top.sv').write_bytes(b'module top(input a,output y); child u(a,y); endmodule\n')
    manifest = {
        'schema': 1,
        'identity': {
            'dataset': {'commit': '1' * 40, 'format': 'synthetic'},
            'source_commit': '2' * 40,
            'runtime': {'commit': '3' * 40, 'sha256': '4' * 64},
            'requested_model': 'synthetic-model', 'observed_model': None,
        },
        'tasks': [{
            'id': 'fixture_task',
            'public_files': [{'path': name, 'sha256': sha((public / name).read_bytes())}
                             for name in ['statement.txt', 'interface.v']],
            'private_files': [{'path': 'secret-grader.py', 'sha256': sha(sentinel)}],
        }],
        'cells': [{'task': 'fixture_task', 'trial': 0, 'arm': 'full',
                   'budget': {'model_calls': 3, 'tool_seconds': 5.5, 'wall_seconds': 10},
                   'verification_policy': 'full'}],
    }
    path = tmp_path / 'frozen.json'
    path.write_text(json.dumps(manifest), encoding='utf-8')
    files = [{'path': name, 'sha256': sha((rtl / name).read_bytes()), 'role': 'rtl'}
             for name in ['child.v', 'top.sv']]
    return SimpleNamespace(root=tmp_path, public=public, private=private, rtl=rtl,
                           manifest=manifest, path=path, files=files, sentinel=sentinel,
                           cell={'task': 'fixture_task', 'trial': 0, 'arm': 'full'})


def seal(s, destination, **overrides):
    options = dict(source_root=s.rtl, files=s.files, destination=destination, top='top',
                   internal_status='accepted', selection_reason='accepted_incumbent', termination='done')
    options.update(overrides)
    return a.seal_candidate(s.manifest, s.cell, **options)


def write_manifest(s):
    s.path.write_text(json.dumps(s.manifest), encoding='utf-8')


def test_manifest_verifies_both_exact_byte_groups(sample):
    s = sample
    assert a.load_manifest(s.path, public_root=s.public, private_root=s.private) == s.manifest
    (s.private / 'secret-grader.py').write_bytes(b'changed')
    with pytest.raises(a.ArtifactError, match='hash mismatch'):
        a.load_manifest(s.path, public_root=s.public, private_root=s.private)


@pytest.mark.parametrize('mutation', [
    lambda m: m.update(schema=True), lambda m: m.update(schema=2),
    lambda m: m.update(extra='unknown'),
    lambda m: m['identity']['dataset'].update(commit='main'),
    lambda m: m['identity']['dataset'].update(format='unknown'),
    lambda m: m['identity'].update(source_commit='short'),
    lambda m: m['identity']['runtime'].update(sha256='A' * 64),
    lambda m: m['identity'].update(observed_model=''),
    lambda m: m['cells'].append(copy.deepcopy(m['cells'][0])),
    lambda m: m['tasks'].append(copy.deepcopy(m['tasks'][0])),
    lambda m: m['cells'][0].update(trial=True),
    lambda m: m['cells'][0].update(arm='unknown'),
    lambda m: m['cells'][0].update(verification_policy='silent_skip'),
    lambda m: m['cells'][0].update(task='not_registered'),
    lambda m: m['cells'][0]['budget'].update(model_calls=True),
    lambda m: m['cells'][0]['budget'].update(wall_seconds=0),
    lambda m: m['cells'][0]['budget'].update(tool_seconds=float('inf')),
    lambda m: m['tasks'][0]['public_files'].append(copy.deepcopy(m['tasks'][0]['public_files'][0])),
])
def test_strict_manifest_rejects_unfrozen_unknown_duplicate_and_nonfinite(sample, mutation):
    mutation(sample.manifest)
    write_manifest(sample)
    with pytest.raises(a.ArtifactError):
        a.load_manifest(sample.path, public_root=sample.public, private_root=sample.private)


def test_duplicate_json_key_and_bad_json_rejected(sample):
    for raw in [b'{"schema":1,"schema":1}', b'not json', b'\xff']:
        sample.path.write_bytes(raw)
        with pytest.raises(a.ArtifactError):
            a.load_manifest(sample.path, public_root=sample.public, private_root=sample.private)


def test_public_export_private_neighbor_and_private_metadata_never_export(sample, monkeypatch):
    s = sample
    loaded = a.load_manifest(s.path, public_root=s.public, private_root=s.private)
    original_read = a._read
    def public_reads_only(root, record):
        assert Path(root) != s.private
        assert 'private' not in record['path'] and 'secret' not in record['path']
        return original_read(root, record)
    monkeypatch.setattr(a, '_read', public_reads_only)
    result = a.export_public(loaded, public_root=s.public, destination=s.root / 'export')
    combined = b''.join(p.read_bytes() for p in (s.root / 'export').rglob('*') if p.is_file())
    for forbidden in [s.sentinel, b'secret-grader.py', b'private_files', sha(s.sentinel).encode()]:
        assert forbidden not in combined
    assert result['identity']['observed_model'] is None
    assert (s.root / 'export/files/fixture_task/statement.txt').read_bytes() == b'Public task only\r\n'


def test_public_source_drift_prevents_completed_receipt(sample):
    (sample.public / 'statement.txt').write_bytes(b'drift')
    destination = sample.root / 'export'
    with pytest.raises(a.ArtifactError, match='hash mismatch'):
        a.export_public(sample.manifest, public_root=sample.public, destination=destination)
    assert not (destination / 'receipt.json').exists()
    with pytest.raises(a.ArtifactError):
        a.load_artifact(destination, expected_id='0' * 64)


def test_complete_ordered_multifile_bundle_and_destination_independent_identity(sample):
    s = sample
    first = seal(s, s.root / 'one')
    second = seal(s, s.root / 'two')
    assert first == second
    assert [r['path'] for r in first['files']] == ['rtl/child.v', 'rtl/top.sv']
    for record in s.files:
        assert (s.root / 'one/rtl' / record['path']).read_bytes() == (s.rtl / record['path']).read_bytes()
    reverse = seal(s, s.root / 'reverse', files=list(reversed(s.files)))
    assert reverse['id'] != first['id']
    with pytest.raises(a.ArtifactError):
        seal(s, s.root / 'one')
    assert a.load_artifact(s.root / 'one', expected_id=first['id']) == first


def test_rejected_complete_is_preserved_without_acceptance(sample):
    result = seal(sample, sample.root / 'rejected', internal_status='rejected',
                  selection_reason='latest_complete', termination='budget')
    assert result['kind'] == 'candidate' and result['internal_status'] == 'rejected'
    assert len(result['files']) == 2 and result['termination'] == 'budget'
    with pytest.raises(a.ArtifactError, match='incumbent'):
        seal(sample, sample.root / 'false-incumbent', internal_status='rejected')


def test_missing_is_separate_terminal_record_and_not_an_empty_candidate(sample):
    result = a.record_missing(sample.manifest, sample.cell, destination=sample.root / 'missing',
                              termination='model_blocked')
    assert result['kind'] == 'missing' and 'files' not in result
    assert result['reason'] == 'no_complete_candidate'
    with pytest.raises(a.ArtifactError, match='nonempty'):
        seal(sample, sample.root / 'empty', files=[])


@pytest.mark.parametrize('change', ['absent', 'changed'])
def test_missing_or_changed_dependency_blocks_whole_bundle(sample, change):
    if change == 'absent':
        (sample.rtl / 'top.sv').unlink()
    else:
        (sample.rtl / 'top.sv').write_bytes(b'changed after declaration')
    destination = sample.root / change
    with pytest.raises(a.ArtifactError):
        seal(sample, destination)
    assert (destination / 'rtl/child.v').exists()  # complete first copy is preserved
    assert not (destination / 'receipt.json').exists()
    with pytest.raises(a.ArtifactError):
        a.load_artifact(destination, expected_id='0' * 64)


def test_source_drift_after_copy_detected_before_final_receipt(sample, monkeypatch):
    original = a._write_file
    def write_then_change(destination, relative, raw):
        original(destination, relative, raw)
        if relative == 'rtl/top.sv':
            (sample.rtl / 'child.v').write_bytes(b'changed during export')
    monkeypatch.setattr(a, '_write_file', write_then_change)
    destination = sample.root / 'drift'
    with pytest.raises(a.ArtifactError, match='hash mismatch'):
        seal(sample, destination)
    assert not (destination / 'receipt.json').exists()


def test_partial_copy_failure_does_not_publish_or_load(sample, monkeypatch):
    original = a._write_file
    def fail_second(destination, relative, raw):
        if relative == 'rtl/top.sv':
            raise OSError('synthetic disk failure')
        original(destination, relative, raw)
    monkeypatch.setattr(a, '_write_file', fail_second)
    destination = sample.root / 'partial'
    with pytest.raises(a.ArtifactError, match='write failed'):
        seal(sample, destination)
    assert (destination / 'rtl/child.v').exists()
    assert not (destination / 'receipt.json').exists()
    with pytest.raises(a.ArtifactError):
        a.load_artifact(destination, expected_id='0' * 64)


@pytest.mark.parametrize('unsafe', [
    '/absolute.v', '../escape.v', 'a/../escape.v', './a.v', 'a//b.v',
    r'C:\escape.v', 'C:relative.v', r'\\server\share\a.v', 'a.v:stream',
    'CON.v', 'com1.sv', 'LPT9.v', 'aux .sv', 'bad./a.v', 'a.v ',
    'a\x00.v', 'bad?/a.v', 'trailing/',
])
def test_portable_path_rejects_windows_and_traversal_forms(sample, unsafe):
    files = [dict(sample.files[0], path=unsafe)]
    with pytest.raises(a.ArtifactError):
        seal(sample, sample.root / 'unsafe', files=files)


@pytest.mark.parametrize('files', [
    [{'path': 'a.v', 'sha256': '0' * 64, 'role': 'testbench'}],
    [{'path': 'run.py', 'sha256': '0' * 64, 'role': 'rtl'}],
    [{'path': 'a.v', 'sha256': '0' * 64, 'role': 'rtl'},
     {'path': 'A.v', 'sha256': '0' * 64, 'role': 'rtl'}],
    [{'path': 'a.v', 'sha256': '0' * 64, 'role': 'rtl'},
     {'path': 'a.v/b.sv', 'sha256': '0' * 64, 'role': 'rtl'}],
])
def test_roles_extensions_duplicates_and_directory_collisions_rejected(sample, files):
    with pytest.raises(a.ArtifactError):
        seal(sample, sample.root / 'bad-files', files=files)


def test_unknown_cell_and_bool_selector_do_not_alias_a_trial(sample):
    for selector in [dict(sample.cell, task='unknown'), dict(sample.cell, trial=False)]:
        with pytest.raises(a.ArtifactError):
            a.record_missing(sample.manifest, selector, destination=sample.root / 'bad-cell', termination='failed')


def test_link_file_directory_root_and_destination_parent_rejected(sample):
    s = sample
    link = s.root / 'linked-root'
    try:
        link.symlink_to(s.rtl, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f'OS symlink privilege unavailable: {exc}')
    with pytest.raises(a.ArtifactError, match='links|reparse'):
        seal(s, s.root / 'linked-source', source_root=link)
    with pytest.raises(a.ArtifactError, match='links|reparse'):
        seal(s, link / 'destination')
    original = (s.rtl / 'child.v').read_bytes()
    (s.rtl / 'child.v').unlink()
    outside = s.root / 'outside.v'
    outside.write_bytes(original)
    (s.rtl / 'child.v').symlink_to(outside)
    with pytest.raises(a.ArtifactError, match='links|reparse'):
        seal(s, s.root / 'linked-file')


def test_windows_reparse_flag_rejected_even_without_symlink_mode(monkeypatch):
    monkeypatch.setattr(Path, 'lstat', lambda _: SimpleNamespace(
        st_mode=stat.S_IFDIR | 0o755, st_file_attributes=0x400))
    with pytest.raises(a.ArtifactError, match='reparse'):
        a._plain(Path('junction'))


@pytest.mark.parametrize('tamper', ['bytes', 'receipt', 'extra', 'missing', 'schema'])
def test_sealed_artifact_reload_rejects_tampering(sample, tamper):
    destination = sample.root / 'sealed'
    original_id = seal(sample, destination)['id']
    if tamper == 'bytes':
        (destination / 'rtl/child.v').write_bytes(b'bad')
    elif tamper == 'extra':
        (destination / 'hidden.py').write_bytes(b'not declared')
    elif tamper == 'missing':
        (destination / 'rtl/top.sv').unlink()
    else:
        path = destination / 'receipt.json'
        receipt = json.loads(path.read_text())
        if tamper == 'schema':
            receipt['schema'] = 99
            receipt['id'] = sha(a._canonical({k: v for k, v in receipt.items() if k != 'id'}))
        else:
            receipt['top'] = 'other_top'
        path.write_text(json.dumps(receipt))
    with pytest.raises(a.ArtifactError):
        a.load_artifact(destination, expected_id=original_id)


def test_receipt_rename_failure_leaves_only_incomplete_pending_record(sample, monkeypatch):
    monkeypatch.setattr(a.os, 'replace', lambda *_: (_ for _ in ()).throw(OSError('atomic rename failed')))
    destination = sample.root / 'pending'
    with pytest.raises(a.ArtifactError):
        seal(sample, destination)
    assert (destination / 'receipt.pending').exists() and not (destination / 'receipt.json').exists()
    with pytest.raises(a.ArtifactError):
        a.load_artifact(destination, expected_id='0' * 64)


def test_public_logical_identity_ignores_destination_and_json_key_order(sample):
    s = sample
    first = a.export_public(s.manifest, public_root=s.public, destination=s.root / 'public-one')
    reversed_keys = dict(reversed(list(s.manifest.items())))
    second = a.export_public(reversed_keys, public_root=s.public, destination=s.root / 'public-two')
    assert first == second
    assert str(s.root) not in json.dumps(first)


def test_completed_receipt_is_absent_until_atomic_publish(sample, monkeypatch):
    original = a.os.replace
    observed = []
    def inspect_then_publish(source, target):
        assert Path(source).name == 'receipt.pending' and Path(target).name == 'receipt.json'
        assert not Path(target).exists()
        destination = Path(target).parent
        for record in sample.files:
            assert sha((destination / 'rtl' / record['path']).read_bytes()) == record['sha256']
        observed.append('complete files, no receipt')
        return original(source, target)
    monkeypatch.setattr(a.os, 'replace', inspect_then_publish)
    result = seal(sample, sample.root / 'last')
    assert observed == ['complete files, no receipt'] and result['kind'] == 'candidate'


def test_valid_digest_cannot_hide_unknown_receipt_fields(sample):
    destination = sample.root / 'unknown-fields'
    receipt = seal(sample, destination)
    receipt['private_metadata'] = 'not an allowed field'
    receipt['id'] = sha(a._canonical({k: v for k, v in receipt.items() if k != 'id'}))
    (destination / 'receipt.json').write_text(json.dumps(receipt))
    with pytest.raises(a.ArtifactError, match='expected exactly'):
        a.load_artifact(destination, expected_id=receipt['id'])


@pytest.mark.skipif(os.name != 'nt', reason='native Windows junction control')
def test_real_windows_junction_cannot_escape_source_or_destination_root(sample):
    s = sample
    link = s.root / 'junction'
    # Both paths stay within this fixture. mklink creates only a directory
    # junction; cleanup uses nonrecursive rmdir and must preserve the target.
    assert link.parent == s.root and s.rtl.parent == s.root
    result = subprocess.run(['cmd.exe', '/d', '/c', 'mklink', '/J', str(link), str(s.rtl)],
                            capture_output=True, text=True, check=False)
    if result.returncode:
        pytest.skip(f'native junction creation unavailable: {result.stderr.strip()}')
    try:
        assert link.lstat().st_file_attributes & 0x400
        with pytest.raises(a.ArtifactError, match='reparse'):
            seal(s, s.root / 'junction-input', source_root=link)
        with pytest.raises(a.ArtifactError, match='reparse'):
            seal(s, link / 'junction-output')
    finally:
        os.rmdir(link)
    assert (s.rtl / 'child.v').is_file() and (s.rtl / 'top.sv').is_file()


@pytest.mark.parametrize('arm,policy,calls', [
    ('single_call', 'full', 2),
    ('single_call', 'skip_generated_tb_mutations', 1),
    ('full', 'skip_generated_tb_mutations', 3),
    ('ablation', 'full', 3),
])
def test_declared_arm_budget_and_policy_cannot_disagree(sample, arm, policy, calls):
    sample.manifest['cells'][0].update(arm=arm, verification_policy=policy)
    sample.manifest['cells'][0]['budget']['model_calls'] = calls
    write_manifest(sample)
    with pytest.raises(a.ArtifactError, match='declare|disagree'):
        a.load_manifest(sample.path, public_root=sample.public, private_root=sample.private)


@pytest.mark.parametrize('arm,policy,calls', [
    ('single_call', 'full', 1), ('ablation', 'skip_generated_tb_mutations', 3),
])
def test_consistent_alternative_arm_metadata_is_preserved(sample, arm, policy, calls):
    sample.manifest['cells'][0].update(arm=arm, verification_policy=policy)
    sample.manifest['cells'][0]['budget']['model_calls'] = calls
    write_manifest(sample)
    result = a.load_manifest(sample.path, public_root=sample.public, private_root=sample.private)
    assert result['cells'][0]['budget']['model_calls'] == calls
    assert result['cells'][0]['verification_policy'] == policy


def test_coherent_file_and_receipt_rewrite_rejected_by_external_identity(sample):
    destination = sample.root / 'rewritten'
    original = seal(sample, destination)
    rewritten = copy.deepcopy(original)
    raw = b'module child(input a,output y); assign y=~a; endmodule\n'
    (destination / 'rtl/child.v').write_bytes(raw)
    rewritten['files'][0]['sha256'] = sha(raw)
    rewritten['id'] = sha(a._canonical({k: v for k, v in rewritten.items() if k != 'id'}))
    (destination / 'receipt.json').write_text(json.dumps(rewritten))
    with pytest.raises(a.ArtifactError, match='trusted expected'):
        a.load_artifact(destination, expected_id=original['id'])
    # The checksum is not a signature. Substituting the external trust anchor
    # too can bless replacement bytes, so that anchor must be retained separately.
    assert a.load_artifact(destination, expected_id=rewritten['id']) == rewritten
