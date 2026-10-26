from autortl import vivado
from autortl.config import RunConfig
from autortl.triage import classify, FailureKind
from unittest.mock import Mock
import pytest


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


def test_simulation_uses_remaining_deadline(tmp_path, monkeypatch):
    monkeypatch.setattr(vivado.time, "monotonic", Mock(side_effect=[0, 4, 8]))
    calls = []
    def run(cmd, cwd, timeout, log):
        calls.append(timeout)
        return 0, "TEST PASSED\n"
    monkeypatch.setattr(vivado, "_run", run)
    assert vivado.xsim_run([], tmp_path / "tb.v", "tb", RunConfig(mode="optimize"), tmp_path, timeout=10)[0]
    assert calls == [10, 6, 2]


def test_expired_simulation_deadline_stops_before_elaboration(tmp_path, monkeypatch):
    monkeypatch.setattr(vivado.time, "monotonic", Mock(side_effect=[0, 11]))
    run = Mock(return_value=(0, ""))
    monkeypatch.setattr(vivado, "_run", run)
    passed, _, kind = vivado.xsim_run([], tmp_path / "tb.v", "tb", RunConfig(mode="optimize"), tmp_path, timeout=10)
    assert not passed and kind == FailureKind.INFRA
    assert run.call_count == 1


@pytest.mark.parametrize("seconds", ["0.001", "5", "12.3456"])
def test_fractional_timeout_is_infrastructure(seconds):
    assert classify(f"timed out after {seconds}s") == FailureKind.INFRA
