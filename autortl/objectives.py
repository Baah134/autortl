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


def timing_infeasible(metrics) -> bool:
    """True only with consistent, finite timing evidence that fails setup or hold."""
    return _timing_state(metrics) is False


def _verified(metrics):
    return (_get(metrics,"sim_passed") is True and
            _get(metrics,"sim_error","") == "" and _get(metrics,"synth_error","") == "")


# Hold slack a timing_progress candidate may lose relative to the incumbent.
HOLD_PROGRESS_TOLERANCE_NS = 0.05


def timing_progress(new, best) -> bool:
    """True when both verified designs are known setup-failing and infeasible,
    new has strictly better setup WNS, and hold is met or not worse beyond tolerance.

    Progress is not closure: it never applies once the incumbent is feasible,
    and a feasible candidate is a timing_recovery instead.
    """
    if not _verified(new) or not _verified(best):
        return False
    if _timing_state(new) is not False or _timing_state(best) is not False:
        return False
    new_setup, best_setup = _get(new,"wns_ns"), _get(best,"wns_ns")
    new_hold, best_hold = _get(new,"whs_ns"), _get(best,"whs_ns")
    # met_hold_counted_as_regression: a candidate whose hold still passes (WHS >= 0)
    # meets the hold condition; the tolerance only limits trading setup for failing hold.
    return (best_setup < 0 and new_setup > best_setup
            and (new_hold >= 0 or new_hold >= best_hold - HOLD_PROGRESS_TOLERANCE_NS))


REG2REG_FIELD = "reg2reg_wns_ns"


def objective_field(objective: str, *designs) -> str:
    """The metric the objective compares among timing-feasible verified designs.

    Full I/O-constrained WNS mostly measures pad delay (io_dominated_timing_metric),
    so maximize_freq compares register-to-register setup slack, but only when
    every compared design reports a finite value; otherwise it uses wns_ns for
    all of them, never a mix (maximize_freq_ranks_on_pad_delay). Feasibility,
    acceptance and infeasible ranking always stay on wns_ns/whs_ns.
    """
    field = _OBJECTIVES[objective][0]
    if objective == "maximize_freq" and designs and all(_finite(_get(d, REG2REG_FIELD)) for d in designs):
        return REG2REG_FIELD
    return field


# Lexicographic secondary metric among timing-feasible verified designs
# (equal_lut_ff_saving_discarded). maximize_freq and minimize_power have none.
_TIE_BREAK = {"minimize_luts": "ff_used", "minimize_ffs": "lut_used"}


def tie_break_field(objective: str, *designs) -> str | None:
    """The secondary metric that breaks an equal objective value, or None.

    minimize_luts compares (lut_used, ff_used) and minimize_ffs compares
    (ff_used, lut_used) lexicographically between timing-feasible verified
    designs: an equal primary with a strictly lower secondary is an objective
    improvement, and a worse primary never is. The field is returned only when
    every compared design reports a finite nonnegative value; otherwise there is
    no tie-break, never a comparison against missing evidence.
    """
    field = _TIE_BREAK.get(objective)
    if field is None:
        return None
    for design in designs:
        value = _get(design, field)
        if not _finite(value) or value < 0:
            return None
    return field


def improvement_kind(new, best, objective: str, *, progress: bool = False) -> str | None:
    """Return timing_recovery, objective, timing_progress, or None; unknown evidence never wins.

    Timing recovery is a feasibility improvement, not a resource/power saving.
    The objective comparison between two feasible designs uses objective_field,
    then tie_break_field when the objective values are equal.
    With progress=True, a verified but still-infeasible candidate that improves
    on an infeasible incumbent (see timing_progress) returns timing_progress.
    The caller still enforces source, testbench, report and process-exit integrity.
    """
    if objective not in _OBJECTIVES:
        raise ValueError("unsupported objective: " + str(objective))
    if not _verified(new) or not _verified(best):
        return None
    if not timing_feasible(new):
        return "timing_progress" if progress and timing_progress(new, best) else None
    previous_timing = _timing_state(best)
    if previous_timing is None:
        return None
    field, maximize = _OBJECTIVES[objective]
    new_value = _get(new,field)
    if not _finite(new_value) or new_value < 0:
        return None
    if previous_timing is False:
        return "timing_recovery"
    field = objective_field(objective, new, best)
    new_value = _get(new,field)
    if not _finite(new_value) or new_value < 0:
        return None
    previous_value = _get(best,field)
    if not _finite(previous_value) or previous_value < 0:
        return None
    better = new_value > previous_value if maximize else new_value < previous_value
    if not better and new_value == previous_value:
        # Equal primary: a strictly lower secondary is still an objective gain.
        secondary = tie_break_field(objective, new, best)
        better = secondary is not None and _get(new, secondary) < _get(best, secondary)
    return "objective" if better else None
