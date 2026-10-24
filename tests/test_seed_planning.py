"""Seed-bound planning with synthetic verification; no model or vendor jobs."""
from unittest.mock import Mock

import pytest
from autortl import fsm, roles
from autortl.config import RunConfig
from autortl.proposal_feedback import source_identity
from autortl.roles import Evaluation
from autortl.report_parser import VivadoMetrics
from tests.test_fsm_resume import SOURCE, WINNER, install_models, install_tools
from tests.test_proposal_feedback_flow import setup, read


def test_changed_accepted_source_requires_plan_for_exact_seed(tmp_path, monkeypatch):
    o = setup(tmp_path, monkeypatch, iterations=2, enabled=False)
    assert o.run()['best_iteration'] == 1
    assert [c.kwargs['generation_seed'] for c in o.planner.plan.call_args_list] == [SOURCE, WINNER]
    binding = read(o, 2, 'plan_binding')
    assert binding['original_seed_sha256'] == source_identity(SOURCE)
    assert binding['seed_sha256'] == source_identity(WINNER)
    assert binding['plan_sha256'] == source_identity('## Instruction for generator\nImprove area')


def test_same_source_physical_improvement_does_not_force_plan(tmp_path, monkeypatch):
    o = setup(tmp_path, monkeypatch, iterations=2)
    o.generator.generate = Mock(return_value=SOURCE)
    assert o.run()['best_iteration'] == 1
    assert o.planner.plan.call_count == 1
    assert [c.args[1] for c in o.generator.generate.call_args_list] == [SOURCE, SOURCE]


def test_rejection_keeps_seed_and_existing_stall_replanning(tmp_path, monkeypatch):
    o = setup(tmp_path, monkeypatch, iterations=2)
    o.evaluator.evaluate = Mock(return_value=Evaluation('reject', 'REJECT', 1, 0))
    assert o.run()['best_iteration'] == 0
    assert [c.kwargs['generation_seed'] for c in o.planner.plan.call_args_list] == [SOURCE, SOURCE]


@pytest.mark.parametrize('first_allowed', [True, False])
@pytest.mark.parametrize('exhausted', [True, False])
def test_no_budget_for_seed_plan_retains_verified_incumbent(tmp_path, monkeypatch, first_allowed, exhausted):
    o = setup(tmp_path, monkeypatch, iterations=2)
    o.budget.allow_replan = Mock(side_effect=[True, False] if first_allowed else [False])
    o.budget.exhausted = Mock(side_effect=[False, True] if exhausted and first_allowed else [False, False])
    result = o.run()
    assert result['status'] == 'done'
    assert result['termination_reason'] == 'planning_unavailable_for_generation_seed'
    assert result['best_iteration'] == (1 if first_allowed else 0)
    assert (o.state.run_dir/'m_best.v').read_text() == (WINNER if first_allowed else SOURCE)
    assert o.generator.generate.call_count == (1 if first_allowed else 0)
    assert [d['iteration'] for d in o.state.read_designs()] == ([0, 1] if first_allowed else [0])
    assert not (o.state.iter_dir(2 if first_allowed else 1)/'proposal_outcome.json').exists()
    assert 'planning_unavailable_for_generation_seed' in o.state.events_path.read_text()


def test_restart_binds_original_source_and_preserves_incumbent(tmp_path, monkeypatch):
    o = setup(tmp_path, monkeypatch, iterations=4)
    o.cfg.stall_restart_threshold = 1
    o.evaluator.evaluate = Mock(side_effect=[Evaluation('ok','ACCEPT',1,0),
        Evaluation('restart','RESTART',1,0), Evaluation('reject','REJECT',1,0),
        Evaluation('reject','REJECT',1,0)])
    o.planner.restart_plan = Mock(return_value='## Instruction for generator\nRestart')
    assert o.run()['best_iteration'] == 1
    assert o.planner.restart_plan.call_args.kwargs['generation_seed'] == SOURCE
    assert o.planner.restart_plan.call_args.args[3].lut_used == 10
    assert read(o, 2, 'restart_plan_binding')['seed_sha256'] == source_identity(SOURCE)
    assert read(o, 2, 'restart_plan_binding')['plan_sha256'] == source_identity('## Instruction for generator\nRestart')
    assert read(o, 3, 'input')['seed_sha256'] == source_identity(SOURCE)


@pytest.mark.parametrize('point', ['plan_result', 'plan_binding', 'outcome'])
def test_interruption_reconstructs_binding_and_exact_call_budget(tmp_path, monkeypatch, point):
    o = setup(tmp_path, monkeypatch, iterations=2)
    persist = o._proposal_evidence
    def interrupt(directory, name, data):
        result = persist(directory, name, data)
        if directory.name == 'iter_001' and name == point:
            raise KeyboardInterrupt('after persisted stage')
        return result
    monkeypatch.setattr(o, '_proposal_evidence', interrupt)
    model = o._model
    def interrupt_model(role, name, *args, **kwargs):
        result = model(role, name, *args, **kwargs)
        if point == 'plan_result' and role == 'planner' and name == 'plan':
            raise KeyboardInterrupt('after saved planner result')
        return result
    monkeypatch.setattr(o, '_model', interrupt_model)
    with pytest.raises(KeyboardInterrupt): o.run()
    assert o.budget.llm_calls == (3 if point == 'outcome' else 1)
    resumed = fsm.Orchestrator(RunConfig.load(o.state.run_dir/'config.json'), o.state.run_dir)
    models = install_models(resumed)
    install_tools(monkeypatch)
    assert resumed.run()['best_iteration'] == 1
    assert resumed.budget.llm_calls == 6
    assert models[('planner','plan')].call_count == 1
    assert models[('generator','generate')].call_count == (1 if point == 'outcome' else 2)
    assert read(resumed, 1, 'input')['feedback'] == ''


@pytest.mark.parametrize('done', [True, False])
@pytest.mark.parametrize('change', ['edit', 'delete'])
def test_binding_evidence_tamper_blocks_replay(tmp_path, monkeypatch, done, change):
    o = setup(tmp_path, monkeypatch, iterations=1)
    if done:
        o.run()
    else:
        o.generator.generate = Mock(side_effect=KeyboardInterrupt('before generation'))
        with pytest.raises(KeyboardInterrupt): o.run()
    path = o.state.iter_dir(1)/'proposal_plan_binding.json'
    if done: assert str(path.resolve()) in o.state.load_fsm()['final_artifacts']
    if change == 'edit': path.write_text('{}')
    else: path.unlink()
    resumed = fsm.Orchestrator(RunConfig.load(o.state.run_dir/'config.json'), o.state.run_dir)
    models = install_models(resumed, forbidden=True)
    if done:
        with pytest.raises(ValueError, match='evidence'): resumed.run()
    else:
        assert resumed.run()['status'] == 'infra_blocked'
    for model in models.values(): model.assert_not_called()


@pytest.mark.parametrize('restart', [True, False])
def test_planner_prompt_separates_supplied_seed_and_incumbent(monkeypatch, restart):
    ask = Mock(return_value='plan')
    monkeypatch.setattr(roles, 'ask', ask)
    p = roles.Planner()
    metrics = VivadoMetrics(lut_used=17, ff_used=9, wns_ns=.2)
    if restart:
        p.restart_plan('contract', 2, 'tried', metrics, None, generation_seed=SOURCE)
    else:
        p.plan(2, 'contract', 'progress', [], metrics, [], None, generation_seed=WINNER)
    prompt = ask.call_args.args[1]
    assert (SOURCE if restart else WINNER) in prompt
    assert 'incumbent measurements' in prompt
    assert 'LUTs=17' in prompt
    assert 'generation seed' in prompt


def test_planner_direct_api_remains_compatible(monkeypatch):
    monkeypatch.setattr(roles, 'ask', Mock(return_value='plan'))
    p = roles.Planner(); metrics = VivadoMetrics()
    assert p.plan(1, 'contract', '', [], metrics, [], None) == 'plan'
    assert p.restart_plan('contract', 1, '', metrics, None) == 'plan'


def test_interrupted_spent_planner_attempt_retains_incumbent_under_original_budget(tmp_path, monkeypatch):
    o = setup(tmp_path, monkeypatch, iterations=2)
    o.cfg.max_llm_calls = o.budget.max_llm_calls = 4
    o.budget.allow_replan = Mock(return_value=True)
    attempts = 0
    def plan(*args, **kwargs):
        nonlocal attempts
        attempts += 1
        o.budget.charge_llm()
        if attempts == 2: raise KeyboardInterrupt('spent uncommitted planner attempt')
        return '## Instruction for generator\nImprove area'
    o.planner.plan = Mock(side_effect=plan)
    with pytest.raises(KeyboardInterrupt): o.run()
    assert o.budget.llm_calls == 4
    resumed = fsm.Orchestrator(RunConfig.load(o.state.run_dir/'config.json'), o.state.run_dir)
    models = install_models(resumed)
    resumed.planner.plan = Mock(side_effect=RuntimeError('LLM_BUDGET: model call budget exhausted'))
    install_tools(monkeypatch)
    result = resumed.run()
    assert result['status'] == 'budget_exhausted' and result['best_iteration'] == 1
    assert resumed.budget.llm_calls == 4
    assert resumed.state.load_fsm()['phase'] == 'BUDGET_EXHAUSTED'
    assert resumed.state.load_fsm()['best_iteration'] == 1
    assert (resumed.state.iter_dir(1)/'cand_standard/m.v').read_text() == WINNER
    assert read(resumed, 1, 'outcome')['selected_source_sha256'] == source_identity(WINNER)
    assert not (resumed.state.iter_dir(2)/'proposal_outcome.json').exists()
    models[('generator','generate')].assert_not_called()
    models[('evaluator','evaluate')].assert_not_called()
    resumed.planner.plan.assert_called_once()


def test_same_seed_instruction_uses_reconstructed_plan(tmp_path, monkeypatch):
    o = setup(tmp_path, monkeypatch, iterations=2)
    o.generator.generate = Mock(return_value=SOURCE)
    def evaluate(*args, **kwargs):
        o.state.write_plan('## Instruction for generator\nUnbound future plan')
        return Evaluation('ok', 'ACCEPT', 1, 0)
    o.evaluator.evaluate = Mock(side_effect=evaluate)
    assert o.run()['best_iteration'] == 1
    assert o.planner.plan.call_count == 1
    assert [c.args[2] for c in o.generator.generate.call_args_list] == ['Improve area', 'Improve area']


def test_planner_quota_remains_resumable_model_block(tmp_path, monkeypatch):
    from llm.client import ModelCallError
    o = setup(tmp_path, monkeypatch, iterations=2)
    plan = o.planner.plan
    attempts = 0
    def quota(*args, **kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 2: raise ModelCallError('planner', 'CODEX_QUOTA')
        return plan(*args, **kwargs)
    o.planner.plan = Mock(side_effect=quota)
    result = o.run()
    assert result['status'] == 'model_blocked' and result['best_iteration'] == 1
    assert result['error_code'] == 'CODEX_QUOTA'
    assert o.state.load_fsm()['phase'] == 'MODEL_BLOCKED'
    assert o.generator.generate.call_count == 1
    assert not (o.state.iter_dir(2)/'proposal_outcome.json').exists()


def test_restart_planner_budget_failure_preserves_verified_incumbent(tmp_path, monkeypatch):
    o = setup(tmp_path, monkeypatch, iterations=3)
    o.cfg.stall_restart_threshold = 1
    o.evaluator.evaluate = Mock(side_effect=[Evaluation('ok','ACCEPT',1,0),
        Evaluation('restart','RESTART',1,0)])
    o.planner.restart_plan = Mock(side_effect=RuntimeError('LLM_BUDGET: exhausted'))
    result = o.run()
    assert result['status'] == 'budget_exhausted' and result['best_iteration'] == 1
    assert o.state.load_fsm()['phase'] == 'BUDGET_EXHAUSTED'
    assert o.state.load_fsm()['best_iteration'] == 1
    assert (o.state.iter_dir(1)/'cand_standard/m.v').read_text() == WINNER
    assert read(o, 1, 'outcome')['selected_source_sha256'] == source_identity(WINNER)
    assert o.generator.generate.call_count == 2
    assert read(o, 2, 'outcome')['recommendation'] == 'RESTART'
    assert not (o.state.iter_dir(3)/'proposal_outcome.json').exists()
    assert not (o.state.iter_dir(2)/'proposal_restart_plan_binding.json').exists()
