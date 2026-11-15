"""clockless_design_untimed_by_metrics_gate: generated synthesis TCL times clockless designs.

Text checks only; the live Vivado confirmation is recorded in
evidence/2026-11-14/pilot-attempts-01 (combinational_timing.json).
"""
from pathlib import Path

import pytest

from autortl.config import RunConfig
from autortl.vivado import synthesis_tcl


def tcl(tmp_path, implementation):
    cfg = RunConfig(mode="optimize", top_module="TopModule", implementation=implementation)
    return synthesis_tcl([tmp_path / "TopModule.v"], "TopModule", cfg, tmp_path)


@pytest.mark.parametrize("implementation", ["chip_top", "out_of_context"])
def test_virtual_clock_only_when_no_clock_exists(tmp_path, implementation):
    text = tcl(tmp_path, implementation)
    period = f"{RunConfig(mode='optimize').target_period_ns:.3f}"
    guard = f"if {{[llength [get_clocks -quiet]] == 0}} {{create_clock -period {period} -name clk"
    assert text.count(guard) == 1
    # The port clock is still created first, unchanged, for clocked designs.
    assert text.index(f"create_clock -period {period} -name clk [get_ports clk]") < text.index(guard)
    # The fallback runs after synthesis, before any timing report.
    assert text.index("synth_design") < text.index(guard) < text.index("report_timing_summary")


def test_chip_top_virtual_clock_precedes_existing_port_delays(tmp_path):
    text = tcl(tmp_path, "chip_top")
    assert text.index("get_clocks -quiet]] == 0") < text.index("set_input_delay -clock clk")


def test_out_of_context_times_ports_only_without_internal_paths(tmp_path):
    """single_register_design_untimed_ooc: no registers or no reg-to-reg path -> time ports."""
    text = tcl(tmp_path, "out_of_context")
    line = next(l for l in text.splitlines() if "get_timing_paths" in l)
    assert "[llength $regs] == 0 || [llength [get_timing_paths -quiet -from $regs -to $regs -max_paths 1]] == 0" in line
    assert "NAME != clk" in line  # the clock port itself gets no data delay
    assert "set_input_delay -clock clk 0.000 $data_inputs; if {[llength $regs] > 0} {set_false_path -hold -from $data_inputs -to $regs}" in line
    assert "set_output_delay -clock clk 0.000 [all_outputs]" in line
    # Outside that guard, out-of-context ports stay untimed as before.
    assert sum("set_input_delay" in l for l in text.splitlines()) == 1
    # The clock guard runs first so the port delays always have a clock.
    assert text.index("get_clocks -quiet]] == 0") < text.index("get_timing_paths")
