"""empty_netlist_unplaceable: wiring-only and path-free designs complete with vacuous timing.

Template text and parser rule; live Vivado results are recorded in
evidence/2026-11-15/empty-netlist-01.
"""
from pathlib import Path

import pytest

from autortl.config import RunConfig
from autortl.metrics_gate import MetricsGateError, validate
from autortl.report_parser import VivadoMetrics, apply_no_timing_paths, parse_all
from autortl.vivado import synthesis_tcl

OOC_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "ooc"


def tcl(tmp_path, implementation):
    cfg = RunConfig(mode="optimize", top_module="TopModule", implementation=implementation)
    return synthesis_tcl([tmp_path / "TopModule.v"], "TopModule", cfg, tmp_path)


@pytest.mark.parametrize("implementation", ["chip_top", "out_of_context"])
def test_stale_marker_is_deleted_first_and_no_path_marker_precedes_completion(tmp_path, implementation):
    text = tcl(tmp_path, implementation)
    lines = [l for l in text.splitlines() if l.strip()]
    assert lines[0].startswith("file delete -force") and lines[0].endswith('no_timing_paths.txt"')
    marker = next(i for i, l in enumerate(lines) if l.startswith("if {[llength [get_timing_paths -quiet -max_paths 1]] == 0}"))
    assert lines[marker + 1] == 'puts "SYNTH_COMPLETE"' and marker + 2 == len(lines)
    assert 'puts $fp "no_paths period_ns 10.000"' in lines[marker]


def test_only_out_of_context_skips_place_and_route_for_an_empty_netlist(tmp_path):
    ooc, chip = tcl(tmp_path, "out_of_context"), tcl(tmp_path, "chip_top")
    guard = "if {[llength [get_cells -quiet -hierarchical -filter {IS_PRIMITIVE}]] == 0} {"
    assert guard in ooc and guard not in chip  # chip_top always has I/O buffers
    block = ooc[ooc.index(guard):ooc.index("place_design")]
    assert ooc.index("opt_design") < ooc.index(guard) < ooc.index("place_design")
    assert "utilization_routed.rpt" in block and "timing_routed.rpt" in block
    assert 'puts "SYNTH_COMPLETE"' in block and "exit 0" in block
    assert 'puts $fp "empty_netlist period_ns 10.000"' in block


def metrics(wns=-999.0, whs=-999.0):
    m = VivadoMetrics()
    m.wns_ns, m.whs_ns = wns, whs
    m.lut_total, m.ff_total = 20800, 41600
    return m


@pytest.mark.parametrize("text", ["empty_netlist period_ns 10.000\n", "no_paths period_ns 6.667"])
def test_marker_gives_vacuous_timing_only_when_report_has_no_numbers(tmp_path, text):
    marker = tmp_path / "no_timing_paths.txt"
    marker.write_text(text)
    m = metrics()
    apply_no_timing_paths(marker, m)
    assert (m.wns_ns, m.whs_ns, m.timing_met) == (float(text.split()[2]), 0.0, True)
    validate(m, True)  # the unchanged gate accepts explicit vacuous timing


def test_marker_never_overrides_measured_slack(tmp_path):
    marker = tmp_path / "no_timing_paths.txt"
    marker.write_text("no_paths period_ns 10.000")
    measured = metrics(wns=-0.5, whs=0.1)
    apply_no_timing_paths(marker, measured)
    assert (measured.wns_ns, measured.whs_ns, measured.timing_met) == (-0.5, 0.1, False)
    half = metrics(wns=3.0)  # WHS missing is still a parse failure, not vacuous
    apply_no_timing_paths(marker, half)
    assert half.whs_ns == -999.0
    with pytest.raises(MetricsGateError):
        validate(half, True)


@pytest.mark.parametrize("text", ["", "period_ns 10", "no_paths period_ns -1", "no_paths period_ns abc",
                                  "no_paths period_ns 0", "something else period_ns 10.0"])
def test_malformed_marker_changes_nothing_and_gate_still_fails(tmp_path, text):
    marker = tmp_path / "no_timing_paths.txt"
    marker.write_text(text)
    m = metrics()
    apply_no_timing_paths(marker, m)
    assert m.wns_ns == -999.0 and not m.timing_met
    with pytest.raises(MetricsGateError):
        validate(m, True)


def test_absent_marker_keeps_missing_timing_fatal(tmp_path):
    m = metrics()
    apply_no_timing_paths(tmp_path / "no_timing_paths.txt", m)
    with pytest.raises(MetricsGateError):
        validate(m, True)


def test_parse_all_with_real_reports_ignores_a_marker(tmp_path):
    """Real out-of-context reports with numeric slack: a marker beside them has no effect."""
    for name in ("utilization_routed.rpt", "timing_routed.rpt"):
        (tmp_path / name).write_bytes((OOC_FIXTURES / name).read_bytes())
    before = parse_all(tmp_path)
    (tmp_path / "no_timing_paths.txt").write_text("no_paths period_ns 10.000")
    after = parse_all(tmp_path)
    assert before.wns_ns != -999.0 and (after.wns_ns, after.whs_ns) == (before.wns_ns, before.whs_ns)


# ------------------------------------------------ vivado_exit_crash_after_completion
from autortl import vivado  # noqa: E402
from autortl.triage import FailureKind  # noqa: E402

REAL_TAIL = ("INFO: [Timing 38-191] Multithreading enabled for timing update using a maximum of 2 CPUs\n"
             "SYNTH_COMPLETE\n"
             "INFO: [Common 17-206] Exiting Vivado at Sun Nov 15 09:15:35 2026...\n"
             "Abnormal program termination (EXCEPTION_ACCESS_VIOLATION)\n"
             "Please check 'W/hs_err_pid13112.log' for details\n")


def test_exit_crash_after_completion_is_recognised_only_in_order():
    assert vivado.crashed_only_at_exit(REAL_TAIL)
    assert not vivado.crashed_only_at_exit('# puts "SYNTH_COMPLETE"\nAbnormal program termination (EXCEPTION_ACCESS_VIOLATION)\n')
    early = "Abnormal program termination (EXCEPTION_ACCESS_VIOLATION)\n" + REAL_TAIL
    assert not vivado.crashed_only_at_exit(early)  # a crash before completion is never excused
    assert not vivado.crashed_only_at_exit("SYNTH_COMPLETE\nAbnormal program termination (EXCEPTION_ACCESS_VIOLATION)\n")
    assert not vivado.crashed_only_at_exit("SYNTH_COMPLETE\nINFO: [Common 17-206] Exiting Vivado at ...\n")


@pytest.mark.parametrize("log, ok, kind", [
    (REAL_TAIL, True, FailureKind.DESIGN),
    ("report_power completed successfully\nAbnormal program termination (EXCEPTION_ACCESS_VIOLATION)\n",
     False, FailureKind.INFRA),
])
def test_run_synthesis_accepts_only_a_shutdown_crash(tmp_path, monkeypatch, log, ok, kind):
    monkeypatch.setattr(vivado, "_run", lambda *a: (1, log))
    source = tmp_path / "m.v"
    source.write_text("module m(input a, output y); assign y = a; endmodule")
    cfg = RunConfig(mode="optimize", implementation="out_of_context")
    result = vivado.run_synthesis([source], "m", cfg, tmp_path)
    assert (result[0], result[2]) == (ok, kind)
