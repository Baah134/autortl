"""Read-only saved-stimulus edge analysis. No simulator or model invocation."""
import hashlib
import json
from pathlib import Path

ROOT = Path('C:/Users/prince.baah/Downloads/autortl-work')
RUNS = [('01', 'tier3_6h_ol6d8', 'sync_byte_fifo'),
        ('02', 'tier3_cn0rc15p', 'uart_tx'),
        ('03', 'tier3_70q5kppw', 'sync_byte_fifo')]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fifo(rows, output_names):
    q = []
    ans = []
    data = next(n for n in output_names if n in ('out_data', 'data_out'))
    valid = next(n for n in output_names if n in ('out_valid', 'valid_out'))
    for row in rows:
        accept = len(q) < 8 and row['in_valid']
        remove = bool(q) and row['out_ready']
        if remove:
            q.pop(0)
        if accept:
            q.append(row['in_data'])
        ans.append({'in_ready': int(len(q) < 8), data: q[0] if q else 0, valid: int(bool(q))})
    return {'in_ready': 1, data: 0, valid: 0}, ans


def uart(rows):
    # Independent cycle counter: -1 means idle; 0..159 current frame age.
    age, data = -1, 0
    ans = []
    for row in rows:
        ready = age in (-1, 159)
        if ready:
            if row['tx_valid']:
                age, data = 0, row['tx_data']
            else:
                age = -1
        else:
            age += 1
        bit = age // 16
        tx = 1 if age == -1 or bit == 9 else 0 if bit == 0 else (data >> (bit - 1)) & 1
        ans.append({'tx_ready': int(age in (-1, 159)), 'tx': tx})
    return {'tx_ready': 1, 'tx': 1}, ans


report = []
for number, dirname, module in RUNS:
    base = ROOT / f'logs/signoff4-t3-{number}' / dirname / 'uart_fifo_build'
    spec = json.loads((base / 'design_spec.json').read_text())
    child = next(m for m in spec['modules'] if m['name'] == module)
    unit = base / 'modules' / module
    saved = json.loads((unit / 'stimulus.json').read_text())
    expected, stimulus = saved['expected'], saved['stimulus']
    initial, independently_computed = uart(stimulus) if module == 'uart_tx' else fifo(stimulus, expected[0])
    # latency0 current-row pre-edge sample sees reset/previous-row post-edge state.
    pre = [initial] + independently_computed[:-1]
    mismatches = [{'index': i, 'signal': name, 'pre_edge': actual[name], 'expected_post_edge': want[name]}
                  for i, (actual, want) in enumerate(zip(pre, expected))
                  for name in want if actual[name] != want[name]]
    candidate = unit / 'candidate_standard_0'
    sim = (candidate / 'sim_log.txt').read_text()
    actual_failures = [line for line in sim.splitlines() if line.startswith('FAIL index=')]
    predicted_failures = [f"FAIL index={m['index']} signal={m['signal']}" for m in mismatches]
    exits = [json.loads(line) for line in (candidate / 'tool_exit_records.log').read_text().splitlines()]
    model_stages = []
    for path in (base / 'journal').glob('*/completed.json'):
        record = json.loads(path.read_text())
        if ':model:' in record.get('stage', ''):
            model_stages.append({'path': path.relative_to(ROOT).as_posix(), 'stage': record['stage'],
                                 'keys': list(record), 'outcome': record.get('outcome')})
    inputs = [base / 'design_spec.json', unit / 'golden.py', unit / 'stimulus.json',
              unit / f'{module}_tb.v', candidate / f'{module}.v', candidate / 'sim_log.txt',
              candidate / 'tool_exit_records.log', base / 'budget.json']
    row = {'run': number, 'module': module, 'latency': child['latency'],
           'budget': json.loads((base / 'budget.json').read_text()),
           'independent_post_edge_equals_saved_expected': independently_computed == expected,
           'pre_edge_mismatch_count': len(mismatches), 'saved_fail_count': len(actual_failures),
           'predicted_failures_equal_saved_first_candidate': sorted(predicted_failures) == sorted(actual_failures),
           'unexpected_saved_failures': sorted(set(actual_failures) - set(predicted_failures))[:8],
           'predicted_failures_not_saved': sorted(set(predicted_failures) - set(actual_failures))[:8],
           'first_mismatches': mismatches[:5],
           'exits': [{'tool': r['tool'], 'returncode': r['returncode'], 'status': r['status']} for r in exits],
           'model_stages': sorted(model_stages, key=lambda r: r['stage']),
           'input_sha256': {str(p.relative_to(ROOT)): digest(p) for p in inputs}}
    assert row['independent_post_edge_equals_saved_expected']
    assert all(e['returncode'] == 0 and e['status'] == 'exited' for e in row['exits'])
    report.append(row)

print(json.dumps(report, indent=2))
