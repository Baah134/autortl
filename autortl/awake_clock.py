"""Seconds the host has been awake, for charging run budgets.

host_sleep_charged_to_run_budget: time.time() and, on Windows, time.monotonic()
keep counting while the machine sleeps or hibernates, so a laptop that suspends
overnight used to end runs as budget_exhausted. Budgets measure this clock
instead; it only moves while the host is running.
"""
from __future__ import annotations
import sys
import time


def _windows_clock():
    import ctypes
    query = ctypes.windll.kernel32.QueryUnbiasedInterruptTime  # 100 ns units, excludes sleep and hibernate
    value = ctypes.c_ulonglong(0)

    def awake_seconds() -> float:
        if not query(ctypes.byref(value)):
            return time.monotonic()
        return value.value / 1e7
    awake_seconds()
    return awake_seconds


def _posix_clock():
    clock = getattr(time, "CLOCK_MONOTONIC", None)  # Linux: excludes suspend
    if clock is None:
        return time.monotonic
    return lambda: time.clock_gettime(clock)


try:
    awake_seconds = _windows_clock() if sys.platform == "win32" else _posix_clock()
except (AttributeError, OSError):
    awake_seconds = time.monotonic
