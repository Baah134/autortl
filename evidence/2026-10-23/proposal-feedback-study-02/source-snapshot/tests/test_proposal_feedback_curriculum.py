from tests.test_curriculum import curriculum, records
from curriculum import runner


def test_frozen_feedback_override_is_forwarded_and_resets_cohort(curriculum):
    _, orch, output = curriculum
    assert runner.run_tier(0, output_root=output, proposal_feedback=False) == 0
    baseline = records()[-1]
    assert all(call.args[0].proposal_feedback is False for call in orch.call_args_list)
    orch.reset_mock()
    assert runner.run_tier(0, output_root=output, proposal_feedback=True) == 0
    feedback = records()[-1]
    assert all(call.args[0].proposal_feedback is True for call in orch.call_args_list)
    assert baseline['cohort'] != feedback['cohort']
    assert feedback['consecutive_qualifying_runs'] == 1
