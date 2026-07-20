from autortl.budget import Budget


def test_degradation_curve():
    b = Budget(max_llm_calls=100, max_vivado_minutes=100, max_wall_minutes=10**6)
    assert b.effective_best_of_n(4) == 4
    b.llm_calls = 60                       # 40% left
    assert b.effective_best_of_n(4) == 2
    b.llm_calls = 95                       # 5% left
    assert b.effective_best_of_n(4) == 1


def test_replan_gate():
    b = Budget(100, 100, 10**6)
    assert b.allow_replan()
    b.llm_calls = 80
    assert not b.allow_replan()


def test_resume_from_disk(tmp_path):
    p = tmp_path / "budget.json"
    b = Budget(100, 100, 100, state_path=p)
    b.charge_llm(7)
    b2 = Budget(100, 100, 100, state_path=p)
    assert b2.llm_calls == 7
