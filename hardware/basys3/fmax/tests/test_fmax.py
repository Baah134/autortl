"""Vivado-free tests for the Fmax sweep: report parsers on real Vivado
reports, the pass rule, the search, and the TCL each attempt runs."""
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import fmax  # noqa: E402

FIXTURES = HERE / "fixtures"


def read(name):
    return (FIXTURES / name).read_text(errors="replace")


def test_timing_summary_of_a_closing_out_of_context_run():
    # sync_fifo at 3.000 ns, out of context
    assert fmax.parse_timing_summary(read("ooc_closes_timing.rpt")) == {
        "wns_ns": 0.256, "tns_ns": 0.0, "setup_failing": 0, "whs_ns": 0.151, "ths_ns": 0.0, "hold_failing": 0,
        "wpws_ns": 0.25, "tpws_ns": 0.0, "pulse_width_failing": 0}


def test_timing_summary_of_a_failing_run_includes_pulse_width():
    # sync_fifo at 2.000 ns: setup fails, and so does the clock's own pulse width
    timing = fmax.parse_timing_summary(read("ooc_fails_timing.rpt"))
    assert timing["wns_ns"] == -0.617 and timing["setup_failing"] == 28
    assert timing["wpws_ns"] == -0.25 and timing["pulse_width_failing"] == 12
    assert not fmax.closes(timing)


def test_pulse_width_alone_blocks_closure():
    timing = fmax.parse_timing_summary(read("ooc_closes_timing.rpt"))
    assert fmax.closes(timing)
    assert not fmax.closes({**timing, "wpws_ns": -0.01, "pulse_width_failing": 1})
    assert not fmax.closes({**timing, "whs_ns": -0.01, "hold_failing": 1})


def test_timing_summary_without_the_table_is_an_error():
    with pytest.raises(fmax.FmaxError):
        fmax.parse_timing_summary("no table here\n")


def test_critical_path_inside_the_core():
    path = fmax.parse_critical_path(read("ooc_closes_path.rpt"))
    assert path == {"source": "tail_rd_ptr_reg/C", "destination": "head_reg[4]/D", "logic_levels": 2,
                    "cells": "LUT6=1 RAMD32=1", "through_pad": False, "path_type": "register_to_register"}


def test_critical_path_of_the_harness_flow_ends_at_a_pin():
    # The harness's own FIR measurement: register, LUT, output buffer, pin.
    path = fmax.parse_critical_path(read("harness_flow_timing.rpt"))
    assert path["source"] == "full_reg/C" and path["destination"] == "in_ready"
    assert path["path_type"] == "register_to_output" and path["through_pad"]
    assert path["cells"] == "LUT2=1 OBUF=1"


@pytest.mark.parametrize("source, destination, kind", [
    ("a_reg/C", "b_reg/D", "register_to_register"),
    ("in_valid", "b_reg/D", "input_to_register"),
    ("a_reg/C", "out_valid", "register_to_output"),
    ("in_valid", "out_valid", "input_to_output"),
])
def test_classify_path(source, destination, kind):
    assert fmax.classify_path(source, destination) == kind


def fake(boundary, noise=0.0):
    """A design that closes at periods >= boundary, with slack = period - boundary."""
    calls = []

    def attempt(period):
        calls.append(period)
        slack = round(period - boundary + noise, 3)
        return {"wns_ns": slack, "whs_ns": 0.1, "wpws_ns": 1.0, "setup_failing": 0 if slack >= 0 else 5,
                "hold_failing": 0, "pulse_width_failing": 0, "tns_ns": min(slack, 0), "ths_ns": 0.0, "tpws_ns": 0.0}
    return attempt, calls


@pytest.mark.parametrize("boundary", [3.0, 3.37, 6.12, 9.95])
def test_search_finds_the_boundary_quickly(boundary):
    attempt, calls = fake(boundary)
    result = fmax.search(attempt)
    assert boundary <= result["best_period_ns"] <= boundary + fmax.RESOLUTION_NS + 1e-9
    assert calls[0] == fmax.SLOWEST_NS
    assert len(calls) <= 4                      # slack-guided, not a blind bisection
    assert all(a["closes"] == (a["period_ns"] >= boundary) for a in result["attempts"])


def test_search_converges_when_slack_overpromises():
    # Real tools find less slack at a tighter target: predictions are optimistic.
    attempt, calls = fake(4.0, noise=0.4)
    result = fmax.search(attempt)
    assert result["best_period_ns"] >= 4.0 - 0.4
    lo, best = result["bracket_ns"]
    assert best - lo <= fmax.RESOLUTION_NS + 1e-9 or len(calls) == 12


def test_search_reports_a_design_that_never_closes():
    attempt, calls = fake(12.0)
    result = fmax.search(attempt)
    assert result["best_period_ns"] is None and calls == [fmax.SLOWEST_NS]


def test_search_is_bounded():
    def attempt(period):          # pathological: slack always points just outside the bracket
        return {"wns_ns": 50.0, "whs_ns": 0.1, "wpws_ns": 50.0, "setup_failing": 0, "hold_failing": 0,
                "pulse_width_failing": 0, "tns_ns": 0.0, "ths_ns": 0.0, "tpws_ns": 0.0}
    result = fmax.search(attempt, limit=6)
    assert len(result["attempts"]) <= 6


def test_summarize_and_markdown(tmp_path):
    import json
    attempt, _ = fake(3.37)
    result = fmax.search(attempt)
    for a in result["attempts"]:
        a["critical_path"] = {"path_type": "register_to_register", "logic_levels": 2, "cells": "LUT6=1 RAMD32=1"}
    (tmp_path / "sync_fifo" / "ooc").mkdir(parents=True)
    (tmp_path / "sync_fifo" / "ooc" / "search.json").write_text(json.dumps(result))
    never, _ = fake(12.0)
    (tmp_path / "sync_fifo" / "harness").mkdir()
    (tmp_path / "sync_fifo" / "harness" / "search.json").write_text(json.dumps(fmax.search(never)))
    rows = fmax.summarize(tmp_path)
    ooc = rows["sync_fifo"]["ooc"]
    assert ooc["best_period_ns"] == result["best_period_ns"] and ooc["fmax_mhz"] == round(1000 / ooc["best_period_ns"], 1)
    assert ooc["wns_at_100mhz_ns"] == round(10.0 - 3.37, 3)
    assert rows["sync_fifo"]["harness"]["fmax_mhz"] is None
    table = fmax.markdown(rows)
    assert "| sync_fifo | does not close |" in table
    assert f"{ooc['fmax_mhz']:.1f} MHz" in table and "register to register, 2 levels (LUT6=1 RAMD32=1)" in table


def test_tcl_for_each_mode(tmp_path):
    src, work = Path("C:/x/core.v"), Path("C:/x/w")
    ooc = fmax.tcl_script([src], "core", 3.25, "ooc", work)
    assert "synth_design -top core -flatten_hierarchy rebuilt -mode out_of_context" in ooc
    assert "HD.CLK_SRC BUFGCTRL_X0Y0" in ooc and "set_input_delay" not in ooc
    assert "create_clock -period 3.250 -name clk" in ooc
    harness = fmax.tcl_script([src], "core", 10.0, "harness", work)
    assert "-mode out_of_context" not in harness and "HD.CLK_SRC" not in harness
    assert "set_input_delay -clock clk -max 0.000" in harness and "set_output_delay -clock clk -max 0.000" in harness
    assert harness.index("synth_design") < harness.index("set_input_delay") < harness.index("opt_design")
    assert harness.startswith("catch {close_project -quiet}\ncreate_project -in_memory -part xc7a35tcpg236-1")


def test_tcl_rejects_unsafe_paths_and_modes():
    with pytest.raises(fmax.FmaxError, match="unsafe"):
        fmax.tcl_script([Path("C:/x/a;b.v")], "core", 10.0, "ooc", Path("C:/w"))
    with pytest.raises(fmax.FmaxError, match="unsafe"):
        fmax.tcl_script([Path("C:/x/[exec rm].v")], "core", 10.0, "ooc", Path("C:/w"))
    with pytest.raises(fmax.FmaxError, match="mode"):
        fmax.tcl_script([Path("C:/x/a.v")], "core", 10.0, "fast", Path("C:/w"))


def test_harness_flow_constraints_match_the_harness():
    # The harness mode must keep measuring what autortl/vivado.py measures.
    harness = (fmax.REPO / "autortl" / "vivado.py").read_text(encoding="utf-8")
    for line in fmax.IO_DELAYS.strip().splitlines():
        assert line.replace("{", "{{").replace("}", "}}") in harness or line in harness
    assert "synth_design -top {top} -flatten_hierarchy rebuilt" in harness
