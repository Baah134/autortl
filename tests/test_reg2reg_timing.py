"""Advisory register-to-register slack beside the I/O-constrained WNS.

Taxonomy: io_dominated_timing_metric. Fixtures are real Vivado 2025.2
reports: the campaign16 counter winner routed with the harness flow at
100 MHz (met.rpt, timing_routed.rpt) and at 400 MHz (violated.rpt).
"""
import shutil
from pathlib import Path

from autortl import vivado
from autortl.report_parser import VivadoMetrics, parse_all, parse_reg2reg
from autortl.roles import reg2reg_text

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "reg2reg"


def test_met_and_violated_reports():
    m = VivadoMetrics()
    parse_reg2reg(FIXTURES / "met.rpt", m)
    assert m.reg2reg_wns_ns == 1.460
    parse_reg2reg(FIXTURES / "violated.rpt", m)
    assert m.reg2reg_wns_ns == -0.553


def test_missing_report_means_no_register_path():
    m = VivadoMetrics()
    parse_reg2reg(FIXTURES / "absent.rpt", m)
    assert m.reg2reg_wns_ns is None
    assert reg2reg_text(m) == "not reported (no register-to-register path)"


def test_pad_limited_design_shows_both_numbers_and_acceptance_is_unchanged(tmp_path):
    shutil.copy(FIXTURES / "timing_routed.rpt", tmp_path / "timing_routed.rpt")
    shutil.copy(FIXTURES / "met.rpt", tmp_path / "timing_reg2reg.rpt")
    m = parse_all(tmp_path)
    # The I/O-constrained WNS decides acceptance; the reg-to-reg slack is advisory.
    assert (m.wns_ns, m.whs_ns, m.reg2reg_wns_ns) == (0.126, 0.026, 1.460)
    assert m.timing_met is True
    assert reg2reg_text(m) == "1.46ns"


def test_old_metric_records_still_load():
    old = VivadoMetrics(lut_used=5).to_dict()
    del old["reg2reg_wns_ns"]
    assert VivadoMetrics.from_dict(old).reg2reg_wns_ns is None


def test_flow_reports_reg2reg_only_when_registers_exist():
    tcl = vivado.SYNTH_TCL.format(promotions="", part="p", sources='"m.v"', workdir="W", period="10.000",
                                  top="m", extra_synth="", phys_opt="")
    line = next(l for l in tcl.splitlines() if "timing_reg2reg.rpt" in l)
    # Unguarded, report_timing -from [all_registers] errors (Vivado 12-4739) and aborts the flow.
    assert line.startswith("catch { if {[llength [all_registers]] > 0} {")  # advisory: never stops the flow
    assert tcl.index("timing_routed.rpt") < tcl.index("timing_reg2reg.rpt") < tcl.index("SYNTH_COMPLETE")
