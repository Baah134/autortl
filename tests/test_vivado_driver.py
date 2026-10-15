from autortl import vivado
from autortl.config import RunConfig
from autortl.triage import classify, FailureKind


def test_clock_query_is_written_literally_to_xdc(tmp_path, monkeypatch):
    monkeypatch.setattr(vivado, "_run", lambda *a: (0, "SYNTH_COMPLETE"))
    source = tmp_path / "counter.v"
    source.write_text("module counter(input clk); endmodule")
    ok, _, _ = vivado.run_synthesis([source], "counter", RunConfig(mode="optimize"), tmp_path)
    assert ok
    script = (tmp_path / "synth.tcl").read_text()
    assert 'puts $fp {create_clock -period 10.000 -name clk [get_ports clk]}' in script


def test_no_open_design_is_not_an_rtl_failure():
    assert classify("ERROR: [Common 17-53] User Exception: No open design.") == FailureKind.INFRA
