"""Synthetic active-exit accounting; no provider or vendor processes."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from autortl import budget as budget_module, fsm
from autortl.budget import Budget
from autortl.config import RunConfig
from llm.client import ModelCallError
from tests.test_fsm_resume import configuration, install_models, install_tools

NO_TOKENS = {'input_tokens': 0, 'cached_input_tokens': 0, 'output_tokens': 0}


@pytest.fixture
def clock(monkeypatch):
    # Replace only budget.py's module binding, never the shared time module.
    value = SimpleNamespace(now=1000.0)
    value.advance = lambda seconds: setattr(value, 'now', value.now + seconds)
    monkeypatch.setattr(budget_module, 'time', SimpleNamespace(time=lambda: value.now))
    return value


def saved_budget(orchestrator):
    return json.loads((orchestrator.state.run_dir/'budget.json').read_text())


def test_public_checkpoint_persists_wall_without_charges(tmp_path, clock):
    path = tmp_path/'budget.json'
    budget = Budget(16, 25, 35, path)
    budget.charge_llm(2)
    budget.charge_vivado(1.25)
    clock.advance(12)
    budget.checkpoint()
    assert json.loads(path.read_text()) == {
        'llm_calls': 2, 'vivado_seconds': 1.25, 'elapsed': 12, 'tokens': NO_TOKENS}


@pytest.mark.parametrize('outcome', ['module_failed', 'model_blocked', 'budget_exhausted',
                                    'unhandled', 'keyboard_interrupt'])
def test_active_exits_checkpoint_last_model_wall(tmp_path, monkeypatch, clock, outcome):
    cfg = configuration(tmp_path)
    cfg.mode = 'build'
    orchestrator = fsm.Orchestrator(cfg, tmp_path/'run')

    def active(saved):
        orchestrator.budget.charge_vivado(1.25)
        orchestrator.budget.charge_llm()
        clock.advance(7)
        orchestrator.budget.charge_llm()
        assert saved_budget(orchestrator)['elapsed'] == 7
        clock.advance(11)
        if outcome == 'model_blocked':
            raise ModelCallError('generator', 'CODEX_QUOTA')
        if outcome == 'budget_exhausted':
            raise RuntimeError('LLM_BUDGET: model call budget exhausted')
        if outcome == 'unhandled':
            raise ValueError('active failure')
        if outcome == 'keyboard_interrupt':
            raise KeyboardInterrupt('graceful interruption')
        return {'status': 'module_failed', 'module': 'm', 'error': 'rejected oracle'}

    monkeypatch.setattr(orchestrator, '_run_build', active)
    if outcome in ('unhandled', 'keyboard_interrupt'):
        exception = ValueError if outcome == 'unhandled' else KeyboardInterrupt
        with pytest.raises(exception):
            orchestrator.run()
    else:
        assert orchestrator.run()['status'] == outcome
    assert saved_budget(orchestrator) == {
        'llm_calls': 2, 'vivado_seconds': 1.25, 'elapsed': 18, 'tokens': NO_TOKENS}
    clock.advance(3600)  # Time between invocations must not consume active budget.
    resumed = Budget(16, 25, 35, orchestrator.state.run_dir/'budget.json')
    assert resumed.wall_minutes * 60 == pytest.approx(18)
    clock.advance(3)
    resumed.checkpoint()
    assert json.loads(resumed.state_path.read_text()) == {
        'llm_calls': 2, 'vivado_seconds': 1.25, 'elapsed': 21, 'tokens': NO_TOKENS}


def test_new_done_checkpoints_and_reuse_or_tamper_preserves_budget(tmp_path, monkeypatch, clock):
    orchestrator = fsm.Orchestrator(configuration(tmp_path), tmp_path/'run')
    install_models(orchestrator)
    install_tools(monkeypatch)
    optimize = orchestrator._run_optimize

    def active(saved):
        result = optimize(saved)
        clock.advance(9)
        return result

    monkeypatch.setattr(orchestrator, '_run_optimize', active)
    result = orchestrator.run()
    assert result['status'] == 'done'
    assert saved_budget(orchestrator)['elapsed'] == 9
    run = orchestrator.state.run_dir
    final = orchestrator.state.load_fsm()['final_artifacts']
    assert str((run/'budget.json').resolve()) not in final
    assert all(hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest
               for name, digest in final.items())
    raw = (run/'budget.json').read_bytes()
    clock.advance(3600)
    resumed = fsm.Orchestrator(RunConfig.load(run/'config.json'), run)
    install_models(resumed, forbidden=True)
    assert resumed.run() == result
    assert (run/'budget.json').read_bytes() == raw
    (run/'m_best.v').write_text('changed winner')
    clock.advance(11)
    with pytest.raises(ValueError, match='winner artifact'):
        resumed.run()
    assert (run/'budget.json').read_bytes() == raw


@pytest.mark.parametrize('guard', ['input', 'config', 'runtime'])
def test_prepare_input_guards_never_checkpoint(tmp_path, monkeypatch, clock, guard):
    orchestrator = fsm.Orchestrator(configuration(tmp_path), tmp_path/'run')

    def active(saved):
        orchestrator.budget.charge_llm()
        clock.advance(10)
        return {'status': 'module_failed'}

    monkeypatch.setattr(orchestrator, '_run_optimize', active)
    orchestrator.run()
    run = orchestrator.state.run_dir
    raw = (run/'budget.json').read_bytes()
    cfg = RunConfig.load(run/'config.json')
    if guard == 'input':
        cfg.design_path.write_text('modified frozen input')
    elif guard == 'config':
        cfg.target_freq_mhz += 1
    else:
        path = run/'runtime.json'
        data = json.loads(path.read_text())
        data['python'] = 'changed interpreter'
        path.write_text(json.dumps(data))
    clock.advance(50)
    resumed = fsm.Orchestrator(cfg, run)
    clock.advance(7)
    with pytest.raises(ValueError):
        resumed.run()
    assert (run/'budget.json').read_bytes() == raw
