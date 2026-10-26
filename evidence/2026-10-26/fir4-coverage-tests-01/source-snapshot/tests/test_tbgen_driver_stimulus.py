"""Generated scoreboard traffic contract; actual RTL controls are materialized separately."""
import copy
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from autortl import tbgen
from autortl.spec import ModuleSpec,Port,ResetSpec
from tests.scoreboard_driver_live_cases import cases,channel,coverage_verdict,save


def generated(*,renamed=False,kind='sync',latency=1):
    spec=channel('trace_case',latency,renamed=renamed,kind=kind)
    stimulus=[{'a':0,'b':0},{'a':255,'b':31},{'a':128,'b':17}]
    expected=[{'y':(r['a']+r['b'])&255,'z':r['a']^r['b']} for r in stimulus]
    return spec,stimulus,expected,tbgen.generate_scoreboard_tb(spec,stimulus,expected)


def test_driver_preserves_offer_using_previous_rising_edge_snapshot():
    _,_,_,text=generated()
    drive=text.split('for (_autortl_cycle=',1)[1]
    hold='if (!_autortl_input_stalled) begin'
    sample="_autortl_input_stalled=(in_valid === 1'b1 && in_ready === 1'b0);"
    assert hold in drive and sample in drive
    assert drive.index(hold)<drive.index('@(posedge _autortl_clk)')<drive.index(sample)
    assert 'in_valid = (_autortl_push < 3 && _autortl_cycle % 5 != 0);' in drive
    # Ready is allowed to recompute when consumer-ready changes at negedge.
    # The offer-hold decision must not read that newly computed ready value.
    assert 'if (!(in_valid' not in drive.split('@(posedge _autortl_clk)',1)[0]


def test_invalid_payloads_change_with_width_sized_masked_noise():
    spec=ModuleSpec('odd_names','identity',[
        Port('clk','input',1),Port('reset_low','input',1),
        Port('one','input',1,signed=True),Port('wide','input',130),Port('result','output',1),
        Port('request_valid','input',1,protocol='valid_ready'),Port('request_ready','output',1,protocol='valid_ready'),
        Port('reply_valid','output',1,protocol='valid_ready'),Port('reply_ready','input',1,protocol='valid_ready')],
        compare_mode='scoreboard',reset=ResetSpec(signal='reset_low',active_high=False))
    text=tbgen.generate_scoreboard_tb(spec,[{'one':0,'wide':0}],[{'result':0}])
    assert '_autortl_noise = !_autortl_noise;' in text
    assert "one = _autortl_noise ? 1'd1 : 1'd0;" in text
    assert f"wide = _autortl_noise ? 130'd{(1<<130)-1} : 130'd0;" in text
    assert 'request_valid = (_autortl_push < 1 && _autortl_cycle % 5 != 0);' in text
    assert "_autortl_input_stalled=(request_valid === 1'b1 && request_ready === 1'b0);" in text


@pytest.mark.parametrize('active_high',[True,False])
def test_sync_pulse_is_polarity_aware_off_edge_and_does_not_flush_queue(active_high):
    spec,stimulus,expected,_=generated(renamed=not active_high)
    text=tbgen.generate_scoreboard_tb(spec,stimulus,expected)
    rst=spec.reset.signal
    body=text.split('for (_autortl_cycle=',1)[1]
    assert f"#1; {rst} = 1'b{int(active_high)};" in body
    assert f"#2; {rst} = 1'b{1-int(active_high)};" in body
    pulse=body.split('// complete off-edge pulse',1)[1].split('@(posedge _autortl_clk)',1)[0]
    assert 'if (_autortl_push > 0 &&' in body and '_autortl_cycle % 11 == 5' in body
    assert '_autortl_push=' not in pulse and '_autortl_pop=' not in pulse and '_autortl_stalled=' not in pulse
    assert 'FAIL' not in pulse


@pytest.mark.parametrize('renamed',[True,False])
def test_async_contract_never_gets_an_unmodelled_off_edge_reset(renamed):
    _,_,_,text=generated(renamed=renamed,kind='async')
    body=text.split('for (_autortl_cycle=',1)[1]
    assert 'off-edge pulse' not in body
    assert "rst = 1'b" not in body and "reset_n = 1'b" not in body
    assert '#2;' not in body


def test_traffic_changes_do_not_change_payload_arrays_or_oracle_calls(tmp_path):
    spec=channel('same_oracle',0)
    oracle=Mock();oracle.run.side_effect=lambda rows:[{'y':(r['a']+r['b'])&255,'z':r['a']^r['b']} for r in rows]
    stimulus=tbgen.gen_stimulus(spec,n_random=7,seed=41)
    original=copy.deepcopy(stimulus)
    output=tmp_path/'generated';tbgen.generate(spec,oracle,output,n_random=7,seed=41)
    saved=json.loads((output/'stimulus.json').read_text())
    assert saved['stimulus']==original
    assert saved['expected']==[{'y':(r['a']+r['b'])&255,'z':r['a']^r['b']} for r in original]
    oracle.run.assert_called_once()
    rows=oracle.run.call_args.args[0]
    assert len(rows)==spec.reset.duration_cycles+len(original)
    assert rows[spec.reset.duration_cycles:]==[{**r,'in_valid':1,'out_ready':1,'rst':0} for r in original]
    assert stimulus==original


def test_zero_latency_same_edge_push_pop_and_drain_guards_are_retained():
    _,stimulus,_,text=generated(latency=0)
    assert text.index('_autortl_push=_autortl_push+1')<text.index('if (out_valid ===')
    assert '_autortl_cycle - _autortl_accepted_cycle[_autortl_pop] < 0' in text
    assert f'_autortl_cycle<{len(stimulus)*12+32}' in text
    assert '_autortl_drain<4' in text and 'FAIL scoreboard did not drain' in text
    assert 'watchdog timeout' in text


def test_executable_control_matrix_and_strict_materializer(tmp_path):
    output=tmp_path/'controls';rows=save(output)
    assert len(rows)==5 and {r['latency'] for r in rows}=={0,1,4}
    assert sum(r['reset_kind']=='async' for r in rows)==1
    assert all(r['expected_pass'] for r in rows)
    assert all(Path(p).exists() for row in rows for p in row['files'])
    with pytest.raises(FileExistsError):save(output)
    for case in cases():
        # Missing old-driver traffic is coverage, not a fabricated DUT failure.
        assert 'COVERAGE_MISSING driver invalid traffic' in case['tb']
        assert 'FAIL DRIVER producer changed blocked offer' in case['tb']
        assert 'FAIL DRIVER input changed during pulse' in case['tb']
        assert 'probe_release_on_bubble' in case['tb']


def test_coverage_parser_keeps_missing_driver_exercise_separate():
    row={'name':'control','required_coverage':{'accepted':{'min':3,'max':3},'pulses':{'min':1},'producer_errors':{'min':0,'max':0}}}
    assert coverage_verdict('DRIVER_COVERAGE case=control accepted=3 pulses=1 producer_errors=0\n',row)['ok']
    missing=coverage_verdict('DRIVER_COVERAGE case=control accepted=3 pulses=0 producer_errors=0\n',row)
    assert not missing['ok'] and missing['missing']==['pulses']
    assert not coverage_verdict('TEST PASSED\n',row)['ok']
