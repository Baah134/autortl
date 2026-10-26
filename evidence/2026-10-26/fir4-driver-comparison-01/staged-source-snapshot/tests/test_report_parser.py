from pathlib import Path
import pytest
from autortl.report_parser import (VivadoMetrics, parse_sim_log,
                                   parse_utilization, parse_timing,
                                   extract_message_ids)

FIX = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize("name", ["sim_conflicting.log", "sim_finish_only.log"])
def test_unverified_simulation_fixtures(name):
    assert not parse_sim_log(FIX / name)[0]


@pytest.mark.parametrize("text", [
    'TEST PASSED\nERROR: [XSIM 43-1] failure',
    'TEST PASSED\nFatal: assertion failed',
    'TEST PASSED\nTEST FAILED',
    'TEST PASSED\n$fatal called',
    'simulation finished',
    'puts "TEST PASSED"',
    'TEST PASSED but checks were skipped',
])
def test_sim_rejects_errors_and_non_verdicts(tmp_path, text):
    p = tmp_path / "sim.log"
    p.write_text(text)
    assert not parse_sim_log(p)[0]


def test_sim_pass(tmp_path):
    p = tmp_path / "sim_log.txt"
    p.write_text("running...\nTEST PASSED\n$finish called")
    passed, err = parse_sim_log(p)
    assert passed and err == ""


def test_sim_fail_collects_fail_lines(tmp_path):
    p = tmp_path / "sim_log.txt"
    p.write_text("FAIL index=3 signal=y expected=7 got=0\nTEST FAILED: 1 errors")
    passed, err = parse_sim_log(p)
    assert not passed and "index=3" in err


def test_utilization_fixture():
    m = VivadoMetrics()
    parse_utilization(FIX / "utilization_routed.rpt", m)
    assert m.lut_used == 48 and m.lut_total == 20800
    assert m.ff_used == 37 and m.ff_total == 41600


def test_timing_fixture():
    m = VivadoMetrics()
    parse_timing(FIX / "timing_routed.rpt", m)
    assert abs(m.wns_ns - 4.092) < 1e-6 and m.timing_met
    assert m.whs_ns == 0.181


def test_real_combined_timing_columns():
    m = VivadoMetrics()
    parse_timing(FIX / "timing_counter_2025_2.rpt", m)
    assert m.wns_ns == 5.491
    assert m.whs_ns == 0.276
    assert m.timing_met


def test_negative_hold_fails_timing(tmp_path):
    p = tmp_path / "timing.rpt"
    p.write_text((FIX / "timing_counter_2025_2.rpt").read_text().replace("0.276", "-0.276"))
    m = VivadoMetrics()
    parse_timing(p, m)
    assert m.wns_ns > 0 and m.whs_ns < 0
    assert not m.timing_met


def test_message_id_extraction():
    ids = extract_message_ids(
        "WARNING: [Synth 8-327] latch\nERROR: [XSIM 43-3225] failed\n"
        "WARNING: [Synth 8-327] latch again")
    assert ids == ["Synth 8-327", "XSIM 43-3225"]


def test_from_dict_roundtrip():
    m = VivadoMetrics(lut_used=10, lut_total=100)
    d = m.to_dict()
    assert "lut_pct" in d
    m2 = VivadoMetrics.from_dict(d)
    assert m2.lut_used == 10
