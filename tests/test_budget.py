from autortl.budget import Budget
import pytest


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


@pytest.mark.parametrize("limits", [(0, 10, 10), (10, 0, 10), (10, 10, 0)])
def test_zero_limit_is_immediately_exhausted(limits):
    assert Budget(*limits).exhausted()


def test_negative_charges_rejected():
    b = Budget(10, 10, 10)
    with pytest.raises(ValueError):
        b.charge_llm(-1)
    with pytest.raises(ValueError):
        b.charge_vivado(-1)


def test_atomic_budget_failure_preserves_disk(monkeypatch, tmp_path):
    from autortl import state
    path = tmp_path / "budget.json"
    b = Budget(100, 100, 100, path)
    b.charge_llm(1)
    def fail(*args):
        raise OSError("interrupted")
    monkeypatch.setattr(state.os, "replace", fail)
    with pytest.raises(OSError):
        b.charge_llm(1)
    assert Budget(100, 100, 100, path).llm_calls == 1


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1])
def test_invalid_time_limits_and_charges_rejected(value):
    with pytest.raises(ValueError):
        Budget(10, value, 10)
    with pytest.raises(ValueError):
        Budget(10, 10, 10).charge_vivado(value)


def test_corrupt_budget_does_not_restore_free_calls(tmp_path):
    path = tmp_path / "budget.json"
    path.write_text('{}')
    with pytest.raises(KeyError):
        Budget(10, 10, 10, path)
