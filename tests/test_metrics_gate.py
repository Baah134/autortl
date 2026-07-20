import pytest
from autortl.report_parser import VivadoMetrics
from autortl.metrics_gate import validate, MetricsGateError


def good():
    return VivadoMetrics(sim_passed=True, lut_used=48, lut_total=20800,
                         ff_used=37, ff_total=41600, wns_ns=4.09, timing_met=True)


def test_good_metrics_pass():
    validate(good(), synthesis_ran=True)


def test_zero_total_rejected():
    m = good(); m.lut_total = 0
    with pytest.raises(MetricsGateError):
        validate(m, synthesis_ran=True)      # THE v3 lut_total:0 bug, now fatal


def test_used_above_total_rejected():
    m = good(); m.ff_used = 99999
    with pytest.raises(MetricsGateError):
        validate(m, synthesis_ran=True)


def test_sim_only_skips_gate():
    m = VivadoMetrics(sim_passed=True)       # no synthesis: no resource claims
    validate(m, synthesis_ran=False)
