"""Feasibility precedes optimization; comparison does not waive verification gates."""
from __future__ import annotations
import math
from collections.abc import Mapping

_OBJECTIVES = {
    "minimize_luts": ("lut_used", False),
    "minimize_ffs": ("ff_used", False),
    "maximize_freq": ("wns_ns", True),
    "minimize_power": ("dynamic_power_w", False),
}


def _get(metrics, name, default=None):
    return metrics.get(name, default) if isinstance(metrics, Mapping) else getattr(metrics, name, default)


def _finite(value):
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _timing_state(metrics):
    flag, setup, hold = (_get(metrics,name) for name in ("timing_met","wns_ns","whs_ns"))
    if type(flag) is not bool or not _finite(setup) or not _finite(hold):
        return None
    if setup == -999.0 or hold == -999.0:
        return None  # parser's missing-data sentinel is not a measured failure
    measured_met = setup >= 0 and hold >= 0
    if flag != measured_met:
        return None  # contradictory flag/slack evidence cannot establish recovery
    return measured_met


def timing_feasible(metrics) -> bool:
    """True only with an explicit passing flag and finite nonnegative setup/hold."""
    return _timing_state(metrics) is True


def _verified(metrics):
    return (_get(metrics,"sim_passed") is True and
            _get(metrics,"sim_error","") == "" and _get(metrics,"synth_error","") == "")


def improvement_kind(new, best, objective: str) -> str | None:
    """Return timing_recovery, objective, or None; unknown evidence never wins.

    Timing recovery is a feasibility improvement, not a resource/power saving.
    The caller still enforces source, testbench, report and process-exit integrity.
    """
    if objective not in _OBJECTIVES:
        raise ValueError("unsupported objective: " + str(objective))
    if not _verified(new) or not _verified(best) or not timing_feasible(new):
        return None
    previous_timing = _timing_state(best)
    if previous_timing is None:
        return None
    field, maximize = _OBJECTIVES[objective]
    new_value = _get(new,field)
    if not _finite(new_value) or new_value < 0:
        return None
    if previous_timing is False:
        return "timing_recovery"
    previous_value = _get(best,field)
    if not _finite(previous_value) or previous_value < 0:
        return None
    better = new_value > previous_value if maximize else new_value < previous_value
    return "objective" if better else None
