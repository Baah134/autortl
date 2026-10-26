"""Signed scoreboard payload traces; no vendor or model calls."""
import copy
import random
from pathlib import Path
from unittest.mock import Mock

import pytest

from autortl import tbgen
from autortl.golden import GoldenModel
from autortl.spec import DesignSpec, IOExample, ModuleSpec, Port, ResetSpec


def channel(*, signed=True, width=4, reset_cycles=3):
    return ModuleSpec('signed_channel', 'accepted signed payload',
        [Port('clk', 'input', 1), Port('rst', 'input', 1),
         Port('a', 'input', width, signed=signed), Port('b', 'input', 7),
         Port('y', 'output', 16, signed=True),
         Port('in_valid', 'input', 1, protocol='valid_ready'),
         Port('in_ready', 'output', 1, protocol='valid_ready'),
         Port('out_valid', 'output', 1, protocol='valid_ready'),
         Port('out_ready', 'input', 1, protocol='valid_ready')],
        latency=3, compare_mode='scoreboard', reset=ResetSpec(duration_cycles=reset_cycles))


def legacy_corners_and_tail(spec, count, seed):
    ports = [p for p in spec.ports if p.protocol == 'none' and p.direction == 'input'
             and p.name not in ('clk', spec.reset.signal)]
    rows = [{p.name: fn(p.width) for p in ports} for fn in
            (lambda w: 0, lambda w: (1 << w)-1, lambda w: 1 << (w-1))]
    rng = random.Random(seed)
    return rows, [{p.name: rng.randrange(1 << p.width) for p in ports} for _ in range(count)]


def test_real_restricted_fir_oracle_reaches_both_signed13_extrema(tmp_path):
    root = Path(__file__).resolve().parents[1]
    spec = DesignSpec.load(root/'curriculum/tier3/signed_fir4_build/design_spec.json').modules[0]
    path = tmp_path/'fir_oracle.py'
    path.write_text('''def init():
    return [0,0,0]
def step(state, inputs):
    if inputs.get("rst",0):
        return init(), {"out_data":0}
    x=inputs["x"]
    if x>=128:
        x=x-256
    result=3*x-5*state[0]+7*state[1]-2*state[2]
    return [x,state[0],state[1]], {"out_data":result & 8191}
''', encoding='utf-8')
    oracle = GoldenModel(path)
    oracle.work_parent = tmp_path
    rows = tbgen.gen_stimulus(spec, n_random=100, seed=1234)
    result = tbgen.expected_outputs(spec, oracle, rows)
    values = [row['out_data']-8192 if row['out_data']>=4096 else row['out_data'] for row in result]
    assert 2166 in values and -2169 in values
    # The exact signed12 truncation observed in the admitted mutation must
    # change these expected bit patterns; a signed8 boundary alone does not.
    for value in (2166, -2169):
        bits = value & 8191
        truncated = (bits & 4095) | ((bits & 2048) << 1)
        assert truncated != bits


def test_mixed_signed_widths_preserve_prefix_examples_and_random_tail():
    spec = channel()
    spec.ports.insert(3, Port('s', 'input', 9, signed=True))
    spec.examples = [IOExample({'rst':0, 'in_valid':1, 'a':3, 's':17, 'b':9}, {'y':0}),
                     IOExample({'rst':0, 'in_valid':1, 'a':3, 's':17, 'b':9}, {'y':0})]
    before = copy.deepcopy(spec)
    corners, tail = legacy_corners_and_tail(spec, 17, 61)
    rows = tbgen.gen_stimulus(spec, n_random=17, seed=61)
    assert rows[:4] == corners + [{'a':3, 's':17, 'b':9}]
    assert rows[4:10] == [{'a':8, 's':256, 'b':0}, {'a':7, 's':255, 'b':0}] * 3
    assert rows[10:] == tail
    assert len(rows) == 3+1+6+17
    assert spec == before
    assert all(set(row) == {'a', 's', 'b'} for row in rows)
    widths = {'a':4, 's':9, 'b':7}
    assert all(type(value) is int and 0<=value<(1<<widths[name]) for row in rows for name,value in row.items())


def test_signed_one_bit_trace_keeps_repeated_temporal_rows():
    spec = channel(width=1)
    assert tbgen.gen_stimulus(spec, n_random=0) == [
        {'a':0,'b':0}, {'a':1,'b':127}, {'a':1,'b':64},
        *([{'a':1,'b':0}, {'a':0,'b':0}]*3)]


@pytest.mark.parametrize('mode', ['fixed_latency', 'scoreboard_unsigned', 'scoreboard_signed_output_only'])
def test_unaffected_modes_keep_exact_legacy_sequence(mode):
    spec = channel(signed=False)
    if mode == 'fixed_latency':
        spec.ports = [p for p in spec.ports if p.protocol == 'none']
        spec.compare_mode = 'fixed_latency'
        spec.ports[2].signed = True
        spec.examples = None
    elif mode == 'scoreboard_unsigned':
        next(p for p in spec.ports if p.name=='y').signed = False
    corners, tail = legacy_corners_and_tail(spec, 13, 19)
    assert tbgen.gen_stimulus(spec, n_random=13, seed=19) == corners+tail


def test_signed_handshake_controls_do_not_trigger_a_data_trace():
    spec = channel(signed=False)
    for port in spec.ports:
        if port.protocol == 'valid_ready':
            port.signed = True
    corners, tail = legacy_corners_and_tail(spec, 7, 11)
    assert tbgen.gen_stimulus(spec, n_random=7, seed=11) == corners+tail


@pytest.mark.parametrize('reset_cycles', [1,3,1000])
def test_signed_trace_exact_total_limit_includes_reset_and_unique_examples(reset_cycles):
    spec = channel(reset_cycles=reset_cycles)
    spec.examples = [IOExample({'rst':0, 'in_valid':1, 'a':3, 'b':9}, {'y':0})]
    count = 10000-reset_cycles-3-1-6
    rows = tbgen.gen_stimulus(spec, n_random=count)
    assert len(rows)+reset_cycles == 10000
    with pytest.raises(ValueError, match='exceeds 10000 steps'):
        tbgen.gen_stimulus(spec, n_random=count+1)


def test_signed_trace_overflow_rejected_before_random_or_oracle_or_output(tmp_path, monkeypatch):
    spec = channel()
    rng = Mock(side_effect=AssertionError('must not allocate RNG'))
    monkeypatch.setattr(tbgen.random, 'Random', rng)
    golden = Mock()
    output = tmp_path/'must_not_exist'
    with pytest.raises(ValueError, match='exceeds 10000 steps'):
        tbgen.generate(spec, golden, output, n_random=9989)
    rng.assert_not_called()
    golden.run.assert_not_called()
    assert not output.exists()
