"""Run budgets count only time the host is awake.

Taxonomy: host_sleep_charged_to_run_budget. A laptop that slept on battery and
hibernated overnight ended three runs as budget_exhausted (fir16-ooc-01,
explore-tier6-01, explore-tier6-02).
"""
import json
import sys
import time

import pytest

from autortl import awake_clock, budget, fsm, vivado
from autortl.budget import Budget


def test_awake_clock_moves_forward_like_a_monotonic_clock():
    a = awake_clock.awake_seconds()
    time.sleep(0.05)
    b = awake_clock.awake_seconds()
    assert 0.03 < b - a < 5


@pytest.mark.skipif(sys.platform != "win32", reason="Windows unbiased interrupt time")
def test_windows_uses_the_unbiased_interrupt_time():
    import ctypes
    value = ctypes.c_ulonglong(0)
    assert ctypes.windll.kernel32.QueryUnbiasedInterruptTime(ctypes.byref(value))
    assert abs(awake_clock.awake_seconds() - value.value / 1e7) < 5


def test_wall_budget_ignores_wall_time_that_passed_while_asleep(monkeypatch, tmp_path):
    awake = [1000.0]
    monkeypatch.setattr(budget, "awake_seconds", lambda: awake[0])
    b = Budget(10, 60, 60, tmp_path / "budget.json")
    awake[0] += 30  # 30 s awake; any hours asleep are invisible to this clock
    assert abs(b.wall_minutes - 0.5) < 1e-9
    assert b.fraction_left() > 0.9


def test_resumed_budget_keeps_saved_awake_time(monkeypatch, tmp_path):
    awake = [50.0]
    monkeypatch.setattr(budget, "awake_seconds", lambda: awake[0])
    path = tmp_path / "budget.json"
    first = Budget(10, 60, 60, path)
    awake[0] += 120
    first.charge_llm()
    assert json.loads(path.read_text())["elapsed"] == pytest.approx(120)
    awake[0] = 7.0  # a reboot restarts the awake clock
    resumed = Budget(10, 60, 60, path)
    assert resumed.wall_minutes == pytest.approx(2.0)


def test_tool_time_is_charged_from_the_awake_clock():
    assert fsm.awake_seconds is awake_clock.awake_seconds
    assert vivado.awake_seconds is awake_clock.awake_seconds
