"""Chronological feedback integration with synthetic tools, never hardware evidence."""
import hashlib
import json
from pathlib import Path
from unittest.mock import Mock

import pytest
from autortl import fsm, roles
from autortl.config import RunConfig
from autortl.roles import Evaluation
from autortl.report_parser import VivadoMetrics
from autortl.proposal_feedback import source_identity
from autortl.triage import FailureKind
from tests.test_fsm_resume import configuration, install_models, install_tools, SOURCE, WINNER


def setup(tmp_path, monkeypatch, iterations=3, enabled=True):
    cfg = configuration(tmp_path)
    cfg.max_iterations = iterations
    cfg.proposal_feedback = enabled
    o = fsm.Orchestrator(cfg, tmp_path / 'run')
    install_tools(monkeypatch)
    install_models(o)
    return o


def read(o, iteration, name):
    return json.loads((o.state.iter_dir(iteration) / f'proposal_{name}.json').read_text())


def test_feedback_reaches_generation_and_planning_only_from_past(tmp_path, monkeypatch):
    o = setup(tmp_path, monkeypatch)
    contexts = []
    plans = []
    def generate(*args, **kwargs):
        contexts.append(o.generator.proposal_context)
        return WINNER
    def plan(*args, **kwargs):
        plans.append(o.planner.proposal_context)
        return '## Instruction for generator\nImprove area'
    o.generator.generate = Mock(side_effect=generate)
    o.planner.plan = Mock(side_effect=plan)
    result = o.run()
    assert result['best_iteration'] == 1
    assert contexts[0] == plans[0] == ''
    assert '"iteration": 1' in contexts[1] and '"iteration": 2' not in contexts[1]
    assert '"iteration": 2' in contexts[2] and '"iteration": 3' not in contexts[2]
    assert '"final_equals_current_seed": true' in contexts[1]
    assert read(o, 1, 'outcome')['is_best'] is True
    assert read(o, 2, 'outcome')['is_best'] is False
    assert read(o, 2, 'input')['seed_sha256'] == source_identity(WINNER)
    assert (o.state.run_dir / 'm_best.v').read_text() == WINNER


def test_optout_retains_audit_but_passes_no_context(tmp_path, monkeypatch):
    o = setup(tmp_path, monkeypatch, enabled=False)
    seen = []
    o.generator.generate = Mock(side_effect=lambda *a, **k: seen.append(o.generator.proposal_context) or WINNER)
    assert o.run()['status'] == 'done'
    assert seen == ['', '', '']
    assert read(o, 2, 'input')['enabled'] is False
    assert read(o, 2, 'input')['feedback'] == ''
    assert read(o, 1, 'outcome')['candidates'][0]['status'] == 'measured'


def test_failed_candidate_is_visible_without_evaluator_or_promotion(tmp_path, monkeypatch):
    o = setup(tmp_path, monkeypatch, iterations=2)
    o.generator.generate = Mock(side_effect=['bad source', WINNER])
    assert o.run()['best_iteration'] == 2
    prior = read(o, 1, 'outcome')
    assert prior['candidates'][0]['status'] == 'design_rejected'
    assert prior['is_best'] is False
    assert 'design_rejected' in read(o, 2, 'input')['feedback']
    assert o.evaluator.evaluate.call_count == 1


def test_infrastructure_block_never_becomes_completed_proposal(tmp_path, monkeypatch):
    o = setup(tmp_path, monkeypatch)
    install_tools(monkeypatch, fail_sim=True)
    assert o.run()['status'] == 'infra_blocked'
    assert not (o.state.iter_dir(1) / 'proposal_outcome.json').exists()
    assert [d['iteration'] for d in o.state.read_designs()] == [0]


@pytest.mark.parametrize('adopted', [False, True])
def test_standard_snapshot_is_not_overwritten_by_doctor(tmp_path, monkeypatch, adopted):
    o = setup(tmp_path, monkeypatch, iterations=2)
    base_metrics = VivadoMetrics(sim_passed=True, lut_used=30, lut_total=100,
        ff_used=8, ff_total=100, wns_ns=-1, whs_ns=.1, timing_met=False)
    monkeypatch.setattr(fsm.vivado, 'full_metrics', lambda work: base_metrics)
    monkeypatch.setattr(fsm, 'diagnose', lambda *a: type('Diagnosis', (), {
        'action':'tool_knobs', 'wns_ns':-1, 'category':type('Cat', (), {'value':'unit'})})())
    def doctor(source, metric, contract, tb, extras, idir, diagnosis, **kwargs):
        trial = VivadoMetrics(sim_passed=True, lut_used=35, lut_total=100,
            ff_used=10, ff_total=100, wns_ns=.2 if adopted else -.5,
            whs_ns=.1, timing_met=adopted)
        o._last_doctor_trial = {'status':'ADOPTED' if adopted else 'NOT_ADOPTED',
            'action':'tool_knobs', 'reason':'unit outcome', 'tools_ran':True,
            'measured_metrics':trial.to_dict()}
        # Synthetic same-directory adoption isolates snapshot semantics.
        return (source, trial, kwargs['verification_dir']) if adopted else None
    monkeypatch.setattr(o, '_doctor_trial', doctor)
    result = o.run()
    prior = read(o, 1, 'outcome')
    assert prior['candidates'][0]['metrics']['wns_ns'] == -1
    assert prior['candidates'][0]['metrics']['lut_used'] == 30
    assert prior['doctor']['measured_metrics']['lut_used'] == 35
    assert prior['doctor']['adopted'] is adopted
    assert result['best_iteration'] == (1 if adopted else 0)
    assert 'doctor_trial' in read(o, 2, 'input')['feedback']


def test_repaired_source_and_original_proposal_are_distinct(tmp_path, monkeypatch):
    o = setup(tmp_path, monkeypatch, iterations=1)
    original = fsm.vivado.xsim_run
    def sim(files, tb, top, cfg, work, **kwargs):
        if 'cand_' in str(work) and work.name != 'repair_001':
            return False, 'unit behavioral failure', FailureKind.DESIGN
        return original(files, tb, top, cfg, work, **kwargs)
    monkeypatch.setattr(fsm.vivado, 'xsim_run', sim)
    o.generator.generate = Mock(return_value=SOURCE)
    o.generator.fix = Mock(return_value=WINNER)
    assert o.run()['best_iteration'] == 1
    record = read(o, 1, 'outcome')['candidates'][0]
    assert record['generated_source_sha256'] == source_identity(SOURCE)
    assert record['final_source_sha256'] == source_identity(WINNER)
    assert record['source']['path'].endswith('repair_001/m.v') or record['source']['path'].endswith('repair_001\\m.v')


@pytest.mark.parametrize('point', ['input', 'outcome'])
def test_interrupted_feedback_reconstructs_without_extra_calls(tmp_path, monkeypatch, point):
    o = setup(tmp_path, monkeypatch)
    persist = o._proposal_evidence
    triggered = False
    def interrupt(directory, name, data):
        nonlocal triggered
        result = persist(directory, name, data)
        if directory.name == 'iter_002' and name == point and not triggered:
            triggered = True
            raise KeyboardInterrupt('after saved feedback')
        return result
    monkeypatch.setattr(o, '_proposal_evidence', interrupt)
    with pytest.raises(KeyboardInterrupt): o.run()
    first_calls = o.budget.llm_calls
    expected = read(o, 2, point)
    # Existing history has later rows during replay; earlier input stays empty.
    resumed = fsm.Orchestrator(RunConfig.load(o.state.run_dir / 'config.json'), o.state.run_dir)
    models = install_models(resumed)
    calls = install_tools(monkeypatch)
    assert resumed.run()['best_iteration'] == 1
    assert read(resumed, 2, point) == expected
    assert read(resumed, 1, 'input')['feedback'] == ''
    assert not any('iter_001' in directory for _, directory in calls)
    expected_new_evaluations = 2 if point == 'input' else 1
    assert models[('evaluator','evaluate')].call_count == expected_new_evaluations
    assert resumed.budget.llm_calls == 9
    assert models[('generator','generate')].call_count == expected_new_evaluations
    assert first_calls == (3 if point == 'input' else 6)


@pytest.mark.parametrize('name', ['input', 'outcome'])
@pytest.mark.parametrize('change', ['edit', 'delete'])
def test_done_feedback_is_bound_to_original_identity(tmp_path, monkeypatch, name, change):
    o = setup(tmp_path, monkeypatch, iterations=1)
    o.run()
    path = o.state.iter_dir(1) / f'proposal_{name}.json'
    assert str(path.resolve()) in o.state.load_fsm()['final_artifacts']
    if change == 'edit': path.write_text('{}')
    else: path.unlink()
    with pytest.raises(ValueError, match='evidence'):
        fsm.Orchestrator(RunConfig.load(o.state.run_dir / 'config.json'), o.state.run_dir).run()


@pytest.mark.parametrize('change', ['edit', 'delete'])
def test_inflight_feedback_tamper_blocks_without_new_model_calls(tmp_path, monkeypatch, change):
    o = setup(tmp_path, monkeypatch)
    o.generator.generate = Mock(side_effect=KeyboardInterrupt('before generation'))
    with pytest.raises(KeyboardInterrupt): o.run()
    path = o.state.iter_dir(1) / 'proposal_input.json'
    if change == 'edit': path.write_text('{}')
    else: path.unlink()
    resumed = fsm.Orchestrator(RunConfig.load(o.state.run_dir / 'config.json'), o.state.run_dir)
    models = install_models(resumed, forbidden=True)
    assert resumed.run()['status'] == 'infra_blocked'
    for model in models.values(): model.assert_not_called()


def test_only_proposal_roles_receive_context(monkeypatch):
    from autortl.verilog_interface import infer_module
    ask = Mock(return_value='```verilog\n'+SOURCE+'\n```')
    monkeypatch.setattr(roles, 'ask', ask)
    generator = roles.Generator(); generator.proposal_context = 'UNIQUE_PRIOR_CONTEXT'
    generator.generate(infer_module(SOURCE,'m'), SOURCE, 'area', 'standard', None)
    assert 'UNIQUE_PRIOR_CONTEXT' in ask.call_args.args[1]
    generator.fix(SOURCE, 'diagnosis', 'error', 'tb', [], None)
    assert 'UNIQUE_PRIOR_CONTEXT' not in ask.call_args.args[1]
    assert 'UNIQUE_PRIOR_CONTEXT' not in roles.evidence_prompt(generator, 'oracle')


def test_all_portfolio_proposals_are_recorded_without_mislabeled_dedup(tmp_path, monkeypatch):
    o = setup(tmp_path, monkeypatch, iterations=1)
    o.cfg.best_of_n = 3
    o.generator.generate = Mock(side_effect=[WINNER, WINNER, SOURCE])
    assert o.run()['status'] == 'done'
    candidates = read(o, 1, 'outcome')['candidates']
    assert len(candidates) == 3
    assert candidates[1]['status'] == 'duplicate_skipped'
    assert candidates[1]['metrics'] == {}
    assert candidates[0]['status'] == candidates[2]['status'] == 'measured'


@pytest.mark.parametrize('target', ['source', 'script', 'feedback'])
def test_modified_prior_evidence_before_done_is_not_freshly_blessed(tmp_path, monkeypatch, target):
    o = setup(tmp_path, monkeypatch, iterations=2)
    synth = fsm.vivado.run_synthesis
    def synth_with_script(files, top, cfg, work, **kwargs):
        result = synth(files, top, cfg, work, **kwargs)
        (work/'synth.tcl').write_text('controlled standard flow', encoding='utf-8')
        return result
    monkeypatch.setattr(fsm.vivado, 'run_synthesis', synth_with_script)
    calls = 0
    def evaluate(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            paths = {
                'source':o.state.iter_dir(1)/'cand_standard/m.v',
                'script':o.state.iter_dir(1)/'cand_standard/synth.tcl',
                'feedback':o.state.iter_dir(1)/'proposal_input.json'}
            paths[target].write_text('modified after observation', encoding='utf-8')
        return Evaluation('ACCEPT','ACCEPT',1,0)
    o.evaluator.evaluate = Mock(side_effect=evaluate)
    result = o.run()
    assert result['status'] == 'infra_blocked'
    assert 'evidence' in result['error'].lower()
    assert o.state.load_fsm()['phase'] != 'DONE'


def test_restart_receives_current_completed_outcome_and_preserves_incumbent(tmp_path, monkeypatch):
    o = setup(tmp_path, monkeypatch, iterations=3)
    o.cfg.stall_restart_threshold = 1
    seen = []
    o.evaluator.evaluate = Mock(side_effect=[
        Evaluation('ok','ACCEPT',1,0), Evaluation('restart','RESTART',1,0),
        Evaluation('no gain','REJECT',1,0)])
    def restart(*args, **kwargs):
        seen.append(o.planner.proposal_context)
        return '## Instruction for generator\nChange structure'
    o.planner.restart_plan = Mock(side_effect=restart)
    assert o.run()['best_iteration'] == 1
    assert len(seen) == 1 and '"iteration": 2' in seen[0]
    assert read(o,2,'restart')['seed_sha256'] == source_identity(SOURCE)
    assert read(o,3,'input')['seed_sha256'] == source_identity(SOURCE)
    assert (o.state.run_dir/'m_best.v').read_text() == WINNER
