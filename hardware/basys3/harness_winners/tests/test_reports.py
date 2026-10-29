"""Fixture tests for the Vivado report parsers (hwsuite.reports)."""
from pathlib import Path
import sys

import pytest

SUITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SUITE))

from hwsuite import reports        # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


def test_instance_utilization_from_real_report():
    row = reports.instance_utilization(FIXTURES / "utilization_hier_fir4_shell.rpt", "u_dut")
    assert row == {"instance": "u_dut", "module": "signed_fir4", "total_luts": 49, "logic_luts": 49,
                   "lutrams": 0, "srls": 0, "ffs": 67, "ramb36": 0, "ramb18": 0, "dsps": 0}


def test_instance_must_appear_exactly_once():
    with pytest.raises(ValueError, match="found 2"):
        reports.instance_utilization(FIXTURES / "utilization_hier_duplicate.rpt", "u_winner")
    with pytest.raises(ValueError, match="found 0"):
        reports.instance_utilization(FIXTURES / "utilization_hier_fir4_shell.rpt", "u_missing")


def test_non_numeric_cell_is_rejected():
    with pytest.raises(ValueError, match="not a number"):
        reports.instance_utilization(FIXTURES / "utilization_hier_duplicate.rpt", "u_bad")


def test_build_result_reads_only_the_printed_line_not_the_echoed_command():
    assert reports.build_result(FIXTURES / "vivado_build_fir4_shell.log") == {"wns_ns": 2.718, "whs_ns": 0.113}
    assert reports.build_result(FIXTURES / "vivado_warnings.log") == {"wns_ns": -0.25, "whs_ns": 0.031}


def test_infra_only_recognizes_the_real_locked_directory_failure():
    from hwsuite.cli import infra_only
    assert infra_only(FIXTURES / "vivado_build_locked_dir.log")           # real Vivado 2025.2 log
    assert not infra_only(FIXTURES / "vivado_warnings.log")               # a design/tool error too
    assert not infra_only(FIXTURES / "vivado_build_fir4_shell.log")       # no errors at all


def test_build_warnings_counts_every_severity_that_matters():
    assert reports.build_warnings(FIXTURES / "vivado_build_fir4_shell.log") == 0
    assert reports.build_warnings(FIXTURES / "vivado_warnings.log") == 3
