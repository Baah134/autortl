"""Prompt/API regressions only; no model, worker or vendor process."""
import ast
import re

import pytest
from autortl import roles, golden_worker
from autortl.spec import ModuleSpec, Port, ResetSpec


@pytest.mark.parametrize('mode', ['scoreboard', 'fixed_latency'])
@pytest.mark.parametrize('feedback', ['', 'unsupported golden syntax: JoinedStr'])
def test_initial_and_repair_prompt_preserve_api_policy_and_context(monkeypatch, mode, feedback):
    captured = []
    monkeypatch.setattr(roles, 'ask', lambda *args, **kwargs: captured.append((args, kwargs)) or '```python\ndef init(): return dict()\ndef step(state, inputs): return state, dict()\n```')
    monkeypatch.setattr(roles, 'conventions', lambda: 'unchanged conventions')
    spec = ModuleSpec('sample', 'EXACT_BEHAVIOR', [Port('payload', 'input', 8, signed=True),
        Port('answer', 'output', 9), Port('out_valid', 'output', 1, protocol='valid_ready')],
        latency=2, compare_mode=mode, reset=ResetSpec(signal='reset_n', active_high=False),
        parameters={'WIDTH': 8})
    budget = object()
    roles.Generator().golden_model(spec, budget, feedback)
    args, kwargs = captured[0]
    assert args[0] == 'generator' and kwargs['budget'] is budget
    prompt = args[1]
    assert 'Allowed builtins: ' + ', '.join(sorted(golden_worker.SAFE_BUILTINS)) in prompt
    assert 'Allowed methods: ' + ', '.join(sorted(golden_worker.SAFE_METHODS)) in prompt
    scaffold = re.search(r'```python\n(.*?)```', prompt, re.S).group(1)
    ast.parse(scaffold)
    golden_worker.validate_source(scaffold)
    assert 'def step(state, inputs):' in scaffold
    assert 'syntax only' in prompt and 'fill\noutputs with every named data output' in prompt
    assert 'EXACT_BEHAVIOR' in prompt and '"WIDTH": 8' in prompt
    assert f'Comparison mode: {mode}' in prompt and 'Declared RTL latency: 2' in prompt
    assert "active_low 'reset_n'" in prompt
    assert 'data outputs: ["answer"]' in prompt
    assert 'two\'s-complement' in prompt and 'ONE ACCEPTED input transaction' in prompt
    assert 'do\nnot add a separate pipeline-delay queue' in prompt
    assert ('previous Python reference failed validation' in prompt) == bool(feedback)
    if feedback:
        assert prompt.endswith(feedback)


def test_prompt_policy_names_come_from_worker_at_format_time(monkeypatch):
    captured=[]
    monkeypatch.setattr(golden_worker, 'SAFE_BUILTINS', {'policy_probe': None})
    monkeypatch.setattr(golden_worker, 'SAFE_METHODS', {'method_probe'})
    monkeypatch.setattr(roles, 'ask', lambda *args, **kwargs: captured.append(args[1]) or '')
    monkeypatch.setattr(roles, 'conventions', lambda: '')
    roles.Generator().golden_model(ModuleSpec('sample', 'behavior', [Port('y','output',1)]), None)
    assert 'Allowed builtins: policy_probe\n' in captured[0]
    assert 'Allowed methods: method_probe\n' in captured[0]


def test_historical_invalid_signature_remains_rejected():
    with pytest.raises(SyntaxError):
        golden_worker.validate_source('def init(): return {}\ndef step(state, inputs: dict) -> (state, outputs: dict):\n    return state, {}\n')


def test_historical_formatted_port_names_remain_rejected():
    source = '''def init():
    return {}
def step(state, inputs: dict) -> (dict, dict):
    if inputs.get("rst", 0) & 1:
        return init(), {"out_data": 0}
    total = sum((inputs.get(f"a{i}", 0) & 0xFF) * (inputs.get(f"b{i}", 0) & 0xFF) for i in range(4))
    return state, {"out_data": total & 0x3FFFF}
'''
    with pytest.raises(ValueError, match='JoinedStr'):
        golden_worker.validate_source(source)
