"""Strict, public-only input exports and explicit RTL submission seals.

These checks are provenance validation, not an OS sandbox, RTL safety parser,
candidate selector, simulator, grader or benchmark registration system.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat


class ArtifactError(ValueError):
    """Malformed, incomplete, changed or unsafe artifact input."""


SCHEMA = 1
ARMS = {'single_call', 'ablation', 'full'}
POLICIES = {'full', 'skip_generated_tb_mutations'}
TERMINATIONS = {'done', 'budget', 'model_blocked', 'failed', 'interrupted'}
_IDENTIFIER = re.compile(r'[A-Za-z_][A-Za-z0-9_]*\Z')
_TASK = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]*\Z')
_RESERVED = {'CON', 'PRN', 'AUX', 'NUL', 'CONIN$', 'CONOUT$'} | {
    f'{prefix}{n}' for prefix in ('COM', 'LPT') for n in '123456789¹²³'
}


def _fail(message):
    raise ArtifactError(message)


def _keys(value, expected, label):
    if type(value) is not dict or set(value) != set(expected.split()):
        _fail(f'{label}: expected exactly {expected}')


def _text(value, label):
    if type(value) is not str or not value.strip() or any(ord(c) < 32 or ord(c) == 127 for c in value):
        _fail(f'{label}: expected nonempty text without control characters')


def _one_of(value, choices, label):
    if type(value) is not str or value not in choices:
        _fail(f'unknown {label}')


def _hash(value, size=64):
    if type(value) is not str or re.fullmatch(f'[0-9a-f]{{{size}}}', value) is None:
        _fail(f'expected full lowercase {size}-digit hexadecimal identity')


def _path(value):
    _text(value, 'path')
    # Portable POSIX spelling, including on Windows. Forbid ADS, drive-relative
    # paths, UNC, reserved devices, case aliases and Win32 trim aliases.
    if '\\' in value or ':' in value or value.startswith('/'):
        _fail('path must be portable and relative')
    for part in value.split('/'):
        if (part in ('', '.', '..') or part.endswith((' ', '.'))
                or any(c in part for c in '<>"|?*')
                or part.split('.')[0].rstrip(' .').upper() in _RESERVED):
            _fail('unsafe path component')
    return value


def _files(records, role=None):
    if type(records) is not list or not records:
        _fail('expected nonempty explicit file list')
    seen = set()
    for record in records:
        _keys(record, 'path sha256' if role is None else 'path sha256 role', 'file')
        path = _path(record['path'])
        if path.casefold() in seen:
            _fail('duplicate or case-aliased file')
        if any(path.casefold().startswith(old + '/') or old.startswith(path.casefold() + '/') for old in seen):
            _fail('file/directory path collision')
        seen.add(path.casefold())
        _hash(record['sha256'])
        if role is not None and record['role'] != role:
            _fail(f'file role must be {role}')
        if role == 'rtl' and Path(path).suffix.lower() not in {'.v', '.sv'}:
            _fail('only explicitly declared .v/.sv RTL is supported')


def _identity(identity):
    _keys(identity, 'dataset source_commit runtime requested_model observed_model', 'identity')
    _keys(identity['dataset'], 'commit format', 'dataset')
    _hash(identity['dataset']['commit'], 40)
    _one_of(identity['dataset']['format'], {'verilogeval', 'rtllm', 'synthetic'}, 'dataset format')
    _hash(identity['source_commit'], 40)
    _keys(identity['runtime'], 'commit sha256', 'runtime')
    _hash(identity['runtime']['commit'], 40)
    _hash(identity['runtime']['sha256'])
    _text(identity['requested_model'], 'requested_model')
    if identity['observed_model'] is not None:
        _text(identity['observed_model'], 'observed_model')


def _cell(cell):
    _keys(cell, 'task trial arm budget verification_policy', 'cell')
    if type(cell['task']) is not str or _TASK.fullmatch(cell['task']) is None:
        _fail('invalid task identifier')
    if type(cell['trial']) is not int or cell['trial'] < 0:
        _fail('trial must be a nonnegative integer')
    _one_of(cell['arm'], ARMS, 'arm')
    _one_of(cell['verification_policy'], POLICIES, 'verification policy')
    _keys(cell['budget'], 'model_calls tool_seconds wall_seconds', 'budget')
    if type(cell['budget']['model_calls']) is not int or cell['budget']['model_calls'] <= 0:
        _fail('model_calls must be a positive integer')
    for key in ('tool_seconds', 'wall_seconds'):
        value = cell['budget'][key]
        if type(value) not in (int, float):
            _fail(f'{key} must be finite positive machine-time seconds')
        try:
            finite = math.isfinite(value)
        except OverflowError:
            finite = False
        if not finite or value <= 0:
            _fail(f'{key} must be finite positive machine-time seconds')
    expected_policy = 'skip_generated_tb_mutations' if cell['arm'] == 'ablation' else 'full'
    if cell['verification_policy'] != expected_policy:
        _fail('arm and declared verification policy disagree')
    if cell['arm'] == 'single_call' and cell['budget']['model_calls'] != 1:
        _fail('single_call must declare exactly one model call')


def _cells(cells, tasks):
    if type(cells) is not list or not cells:
        _fail('expected nonempty cells')
    seen = set()
    for cell in cells:
        _cell(cell)
        key = (cell['task'], cell['trial'], cell['arm'])
        if key in seen or cell['task'] not in tasks:
            _fail('duplicate cell or unknown task')
        seen.add(key)


def _manifest(manifest):
    _keys(manifest, 'schema identity tasks cells', 'manifest')
    if type(manifest['schema']) is not int or manifest['schema'] != SCHEMA:
        _fail('unknown manifest schema')
    _identity(manifest['identity'])
    if type(manifest['tasks']) is not list or not manifest['tasks']:
        _fail('expected nonempty tasks')
    seen = set()
    for task in manifest['tasks']:
        _keys(task, 'id public_files private_files', 'task')
        task_id = task['id']
        if type(task_id) is not str or _TASK.fullmatch(task_id) is None or task_id.casefold() in seen:
            _fail('invalid or duplicate task identifier')
        seen.add(task_id.casefold())
        _files(task['public_files'])
        _files(task['private_files'])
    _cells(manifest['cells'], {t['id'] for t in manifest['tasks']})


def _plain(path):
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
        _fail('links and Windows reparse points are forbidden')
    return info


def _directory(path):
    path = Path(os.path.abspath(path))
    for part in [*reversed(path.parents), path]:
        if not stat.S_ISDIR(_plain(part).st_mode):
            _fail('expected ordinary directory')
    return path


def _source(root, relative):
    root = _directory(root)
    target = root
    for part in _path(relative).split('/'):
        target = target / part
        _plain(target)
    if not stat.S_ISREG(target.lstat().st_mode):
        _fail('expected ordinary file')
    return target


def _read(root, record):
    try:
        path = _source(root, record['path'])
        before = _plain(path)
        flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0)
        with os.fdopen(os.open(path, flags), 'rb') as stream:
            opened = os.fstat(stream.fileno())
            raw = stream.read()
        after = _plain(path)
        signature = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)
        if signature(before) != signature(opened) or signature(before) != signature(after):
            _fail('file changed during read')
        if hashlib.sha256(raw).hexdigest() != record['sha256']:
            _fail('file hash mismatch')
        return raw
    except OSError as exc:
        raise ArtifactError(f'file unavailable: {record["path"]}') from exc


def _json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                _fail('duplicate JSON object key')
            result[key] = value
        return result
    try:
        # Decode explicitly: json.loads(bytes) also auto-detects UTF-16/32.
        # Schema 1 accepts UTF-8 without BOM only.
        text = raw.decode('utf-8')
        if text.startswith('\ufeff'):
            _fail('UTF-8 BOM is unsupported')
        return json.loads(text, object_pairs_hook=pairs,
                          parse_constant=lambda _: _fail('nonfinite JSON number'))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ArtifactError('invalid UTF-8 JSON') from exc


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('utf-8')


def load_manifest(path, *, public_root, private_root):
    """Load strict schema v1 and verify both explicitly declared file groups."""
    path = Path(path)
    try:
        _source(path.parent, path.name)
        manifest = _json(path.read_bytes())
        _manifest(manifest)
        for task in manifest['tasks']:
            for key, root in [('public_files', public_root), ('private_files', private_root)]:
                for record in task[key]:
                    _read(root, record)
        return manifest
    except OSError as exc:
        raise ArtifactError('manifest unavailable') from exc


def _receipt_files(receipt):
    if receipt['kind'] == 'public':
        return [record for task in receipt['tasks'] for record in task['files']]
    return receipt.get('files', [])


def _validate_receipt(receipt):
    common = 'schema kind id identity '
    kind = receipt.get('kind') if type(receipt) is dict else None
    if kind == 'public':
        _keys(receipt, common + 'tasks cells', 'public receipt')
    elif kind == 'candidate':
        _keys(receipt, common + 'cell files top internal_status selection_reason termination', 'candidate receipt')
    elif kind == 'missing':
        _keys(receipt, common + 'cell reason termination', 'missing receipt')
    else:
        _fail('unknown artifact kind')
    if type(receipt['schema']) is not int or receipt['schema'] != SCHEMA:
        _fail('unknown artifact schema')
    _identity(receipt['identity'])
    _hash(receipt['id'])
    if receipt['id'] != hashlib.sha256(_canonical({k: v for k, v in receipt.items() if k != 'id'})).hexdigest():
        _fail('receipt identity mismatch')
    if kind == 'public':
        if type(receipt['tasks']) is not list or not receipt['tasks']:
            _fail('expected public tasks')
        ids = set()
        for task in receipt['tasks']:
            _keys(task, 'id files', 'public task')
            if type(task['id']) is not str or _TASK.fullmatch(task['id']) is None or task['id'].casefold() in ids:
                _fail('invalid or duplicate public task')
            ids.add(task['id'].casefold())
            _files(task['files'], 'public')
            if any(not f['path'].startswith(f'files/{task["id"]}/') for f in task['files']):
                _fail('public file outside task prefix')
        _files(_receipt_files(receipt), 'public')
        _cells(receipt['cells'], {t['id'] for t in receipt['tasks']})
    else:
        _cell(receipt['cell'])
        _one_of(receipt['termination'], TERMINATIONS, 'termination')
        if kind == 'missing':
            if receipt['reason'] != 'no_complete_candidate':
                _fail('unknown missing reason')
        else:
            _files(receipt['files'], 'rtl')
            if any(not f['path'].startswith('rtl/') for f in receipt['files']):
                _fail('RTL outside declared prefix')
            if type(receipt['top']) is not str or _IDENTIFIER.fullmatch(receipt['top']) is None:
                _fail('invalid top identifier')
            _one_of(receipt['internal_status'], {'accepted', 'rejected', 'unverified'}, 'internal status')
            _one_of(receipt['selection_reason'], {'accepted_incumbent', 'latest_complete'}, 'selection reason')
            if receipt['selection_reason'] == 'accepted_incumbent' and receipt['internal_status'] != 'accepted':
                _fail('incumbent requires accepted internal status')


def _write_file(destination, relative, raw):
    target = destination / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    _directory(target.parent)
    with target.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def _publish(destination, payload, copies):
    # A failed directory is deliberately retained; it cannot load without the
    # final receipt and cannot be silently overwritten by another attempt.
    payload = _json(_canonical(payload))  # detach mutable caller structures
    payload['id'] = hashlib.sha256(_canonical(payload)).hexdigest()
    _validate_receipt(payload)
    destination = Path(os.path.abspath(destination))
    try:
        _directory(destination.parent)
        destination.mkdir(exist_ok=False)
        for root, source_record, target in copies:
            _write_file(destination, target, _read(root, source_record))
        for root, source_record, _ in copies:
            _read(root, source_record)  # detect drift after earlier copies
        for record in _receipt_files(payload):
            _read(destination, record)  # verify copied bytes before final seal
        _write_file(destination, 'receipt.pending', _canonical(payload) + b'\n')
        os.replace(destination / 'receipt.pending', destination / 'receipt.json')
        return load_artifact(destination, expected_id=payload['id'])
    except OSError as exc:
        raise ArtifactError('artifact write failed; destination is not reusable') from exc


def export_public(manifest, *, public_root, destination):
    """Copy public allowlisted bytes only; never traverse/read private input."""
    _manifest(manifest)
    tasks, copies = [], []
    for task in manifest['tasks']:
        records = []
        for source in task['public_files']:
            target = f'files/{task["id"]}/{source["path"]}'
            records.append({'path': target, 'sha256': source['sha256'], 'role': 'public'})
            copies.append((public_root, dict(source), target))
        tasks.append({'id': task['id'], 'files': records})
    return _publish(destination, {'schema': SCHEMA, 'kind': 'public',
                    'identity': manifest['identity'], 'tasks': tasks, 'cells': manifest['cells']}, copies)


def _selected_cell(manifest, cell):
    _manifest(manifest)
    _keys(cell, 'task trial arm', 'cell selector')
    if (type(cell['task']) is not str or type(cell['trial']) is not int
            or cell['trial'] < 0):
        _fail('invalid cell selector')
    _one_of(cell['arm'], ARMS, 'arm')
    found = [c for c in manifest['cells'] if all(c[k] == v for k, v in cell.items())]
    if len(found) != 1:
        _fail('cell not registered in manifest')
    return found[0]


def seal_candidate(manifest, cell, *, source_root, files, destination, top,
                   internal_status, selection_reason, termination):
    """Seal the caller's complete ordered RTL list; make no selection/acceptance decision."""
    selected = _selected_cell(manifest, cell)
    _files(files, 'rtl')
    records = [dict(f, path='rtl/' + f['path']) for f in files]
    copies = [(source_root, dict(source), target['path']) for source, target in zip(files, records)]
    return _publish(destination, {'schema': SCHEMA, 'kind': 'candidate',
                    'identity': manifest['identity'], 'cell': selected, 'files': records,
                    'top': top, 'internal_status': internal_status,
                    'selection_reason': selection_reason, 'termination': termination}, copies)


def record_missing(manifest, cell, *, destination, termination):
    """Publish a terminal missing-output record, never an empty RTL submission."""
    selected = _selected_cell(manifest, cell)
    return _publish(destination, {'schema': SCHEMA, 'kind': 'missing',
                    'identity': manifest['identity'], 'cell': selected,
                    'reason': 'no_complete_candidate', 'termination': termination}, [])


def load_artifact(destination, *, expected_id):
    """Verify against a trusted external ID plus exact bytes and file inventory."""
    _hash(expected_id)
    try:
        destination = _directory(destination)
        receipt_path = _source(destination, 'receipt.json')
        receipt = _json(receipt_path.read_bytes())
        _validate_receipt(receipt)
        if receipt['id'] != expected_id:
            _fail('artifact differs from trusted expected identity')
        expected = {'receipt.json'}
        for record in _receipt_files(receipt):
            _read(destination, record)
            expected.add(record['path'])
        actual = set()
        def traversal_error(error):
            raise error
        for parent, directories, files in os.walk(destination, followlinks=False,
                                                  onerror=traversal_error):
            for name in directories + files:
                path = Path(parent) / name
                info = _plain(path)
                if stat.S_ISREG(info.st_mode):
                    actual.add(path.relative_to(destination).as_posix())
                elif not stat.S_ISDIR(info.st_mode):
                    _fail('unexpected artifact file type')
        if actual != expected:
            _fail('unlisted or missing artifact file')
        return receipt
    except OSError as exc:
        raise ArtifactError('artifact incomplete or unavailable') from exc
