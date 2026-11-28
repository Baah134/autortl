"""Public contract and matched failed-oracle context; no hidden grader input."""
import hashlib
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from autortl import fsm, roles
from autortl.config import RunConfig
from autortl.spec import IOExample, ModuleSpec, Port


GOOD = 'def init(): return {}\ndef step(s,i): return s,{"y":(i["a"]+1)&255}'
BAD1 = 'def init(:'
BAD2 = 'def init(): return {}\ndef step(s,i): return s,{"y":i["missing"]}'
RTL = "module m(input [7:0] a, output [7:0] y); assign y=a+1'b1; endmodule"


def module(name='m'):
    return ModuleSpec(name,'Increment the authoritative external input a modulo256.',
                      [Port('a','input',8),Port('y','output',8)],
                      examples=[IOExample({'a':19},{'y':20},3), IOExample({'a':254},{'y':255},1)])


def prompt(monkeypatch, spec=None, **kwargs):
    request=Mock(return_value=GOOD)
    monkeypatch.setattr(roles,'ask',request)
    monkeypatch.setattr(roles,'conventions',lambda:'')
    roles.Generator().golden_model(spec or module(),None,**kwargs)
    return request.call_args.args[1]


def test_public_examples_include_original_values_cycle_semantics_and_no_reference(monkeypatch):
    spec=module();spec.golden_model='FORBIDDEN_HIDDEN_REFERENCE'
    text=prompt(monkeypatch,spec)
    assert 'AUTHORITATIVE PUBLIC CONTRACT EXAMPLES' in text
    assert 'fresh init() state' in text and 'after_cycles calls to step()' in text
    assert 'one accepted input transaction, not a physical clock cycle' in text
    records=[json.loads(line) for line in text.splitlines() if line.startswith('{"after_cycles"')]
    assert records==[{'index':0,'inputs':{'a':19},'expected':{'y':20},'after_cycles':3},
                     {'index':1,'inputs':{'a':254},'expected':{'y':255},'after_cycles':1}]
    assert 'FORBIDDEN_HIDDEN_REFERENCE' not in text
    assert 'UNTRUSTED PREVIOUS FAILED' not in text


def test_example_omissions_are_explicit_and_never_cut_json():
    spec=module();spec.examples=[IOExample({'a':'x'*20000},{'y':0},1)]+spec.examples
    text=roles.golden_examples_context(spec)
    assert len(text)<=roles.GOLDEN_EXAMPLES_MAX_CHARS
    assert 'Omitted examples: 1 of 3' in text
    records=[json.loads(line) for line in text.splitlines() if line.startswith('{"after_cycles"')]
    assert [r['index'] for r in records]==[1,2]
    spec.examples=[IOExample({'a':1},{'y':2},1)]*100
    text=roles.golden_examples_context(spec)
    assert len(text)<=roles.GOLDEN_EXAMPLES_MAX_CHARS and 'Omitted examples:' in text


def test_failed_source_is_untrusted_bounded_and_separates_file_from_text_identity(monkeypatch):
    source='# "quoted"\n'*5000
    digest='f'*64
    text=prompt(monkeypatch,feedback='ValueError: matching_latest_failure',
                previous_source=source,previous_source_sha256=digest)
    assert text.index('AUTHORITATIVE PUBLIC CONTRACT EXAMPLES') < text.index('UNTRUSTED PREVIOUS FAILED')
    # The JSON artifact occupies one physical line; later diagnostic stays last.
    records=[json.loads(line) for line in text.splitlines() if line.startswith('{"failed_file_sha256"')]
    assert len(records)==1
    record=records[0]
    assert record['failed_file_sha256']==digest
    assert record['source_text_utf8_sha256']==hashlib.sha256(source.encode()).hexdigest()
    assert record['truncated'] and record['shown_characters']<record['original_characters']
    assert source.startswith(record['source_text_prefix'])
    serialized=next(line for line in text.splitlines() if line.startswith('{"failed_file_sha256"'))
    assert len(serialized)<=roles.GOLDEN_SOURCE_MAX_CHARS
    assert text.endswith('ValueError: matching_latest_failure')


def test_empty_failed_source_keeps_its_raw_file_identity(monkeypatch):
    empty_hash=hashlib.sha256(b'').hexdigest()
    text=prompt(monkeypatch,feedback='ValueError: missing init and step',
                previous_source='',previous_source_sha256=empty_hash)
    records=[json.loads(line) for line in text.splitlines() if line.startswith('{"failed_file_sha256"')]
    assert len(records)==1
    assert records[0]['failed_file_sha256']==empty_hash
    assert records[0]['source_text_prefix']=='' and records[0]['original_characters']==0
    assert records[0]['source_text_utf8_sha256']==empty_hash and records[0]['truncated'] is False


def make_orchestrator(tmp_path,monkeypatch,name='one',journal=False):
    o=fsm.Orchestrator(RunConfig(mode='build',top_module='m'),tmp_path/name)
    o._journal_enabled=journal
    monkeypatch.setattr(o,'_generate_verified',Mock(return_value=RTL))
    monkeypatch.setattr(o,'_qualify_source',Mock(return_value=(True,'controlled proof')))
    monkeypatch.setattr(fsm,'qualify_tb',Mock(return_value=(True,'controlled proof')))
    folder=tmp_path/(name+'_module');folder.mkdir(exist_ok=True)
    return o,folder


def test_successive_repairs_receive_only_immediately_preceding_source_and_raw_digest(tmp_path,monkeypatch):
    o,folder=make_orchestrator(tmp_path,monkeypatch)
    calls=[]
    def generation(spec,budget,**kwargs):
        calls.append(kwargs)
        if len(calls)>1:
            receipt=json.loads((folder/f'golden_attempt_{len(calls)-1}.log').read_text())
            assert kwargs['previous_source_sha256']==receipt['source_sha256']
            assert kwargs['previous_source_sha256']==hashlib.sha256((folder/'golden.py').read_bytes()).hexdigest()
            assert kwargs['feedback']==receipt['diagnostic']
        return [BAD1,BAD2,GOOD][len(calls)-1]
    monkeypatch.setattr(o.generator,'golden_model',generation)
    assert o._build_module(module(),folder)==RTL
    assert calls[0]=={}
    assert calls[1]['previous_source']==BAD1 and calls[2]['previous_source']==BAD2
    assert 'SyntaxError' in calls[1]['feedback'] and 'missing' in calls[2]['feedback']
    assert len(calls)==fsm.ORACLE_ATTEMPTS==3


def test_repair_context_is_local_to_each_module(tmp_path,monkeypatch):
    o,folder=make_orchestrator(tmp_path,monkeypatch)
    model=Mock(side_effect=[BAD1,GOOD,GOOD]);monkeypatch.setattr(o.generator,'golden_model',model)
    assert o._build_module(module(),folder)==RTL
    other=tmp_path/'other_module';other.mkdir()
    assert o._build_module(module('other'),other)==RTL
    assert model.call_args_list[2].kwargs=={}


def test_replay_restores_rejected_sources_without_new_generation_calls(tmp_path,monkeypatch):
    o,folder=make_orchestrator(tmp_path,monkeypatch,journal=True)
    model=Mock(side_effect=[BAD1,BAD2,GOOD]);monkeypatch.setattr(o.generator,'golden_model',model)
    assert o._build_module(module(),folder)==RTL
    assert model.call_count==3
    replay,_=make_orchestrator(tmp_path,monkeypatch,journal=True)
    forbidden=Mock(side_effect=AssertionError('replay must not regenerate'))
    monkeypatch.setattr(replay.generator,'golden_model',forbidden)
    assert replay._build_module(module(),folder)==RTL
    forbidden.assert_not_called()


def test_provider_failure_during_repair_propagates_without_consuming_more_attempts(tmp_path,monkeypatch):
    o,folder=make_orchestrator(tmp_path,monkeypatch)
    model=Mock(side_effect=[BAD1,RuntimeError('provider failure')]);monkeypatch.setattr(o.generator,'golden_model',model)
    with pytest.raises(RuntimeError,match='provider failure'):
        o._build_module(module(),folder)
    assert model.call_count==2 and not (folder/'golden_attempt_2.log').exists()
    o._generate_verified.assert_not_called()


def test_source_storage_failure_during_repair_propagates_without_oracle_credit(tmp_path,monkeypatch):
    o,folder=make_orchestrator(tmp_path,monkeypatch)
    model=Mock(side_effect=[BAD1,GOOD]);monkeypatch.setattr(o.generator,'golden_model',model)
    original=Path.write_text
    calls=[]
    def write(path,*args,**kwargs):
        if path==folder/'golden.py':
            calls.append(path)
            if len(calls)==2:
                raise OSError('controlled source storage failure')
        return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,'write_text',write)
    with pytest.raises(OSError,match='controlled source storage failure'):
        o._build_module(module(),folder)
    assert model.call_count==2 and not (folder/'golden_attempt_2.log').exists()
    o._generate_verified.assert_not_called()
