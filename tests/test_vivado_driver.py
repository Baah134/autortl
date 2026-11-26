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


windows_only = pytest.mark.skipif(__import__("os").name != "nt", reason="MAX_PATH applies to Windows")


def _work_dir_with_object_path_length(tmp_path, length):
    """A work directory whose xelab object path for snapshot tb_snap has this many characters."""
    base = len(vivado.xelab_object_path(tmp_path / "w", "tb_snap"))
    return tmp_path / ("w" + "x" * (length - base))


@windows_only
def test_an_xelab_object_path_at_max_path_is_infrastructure_before_any_tool(tmp_path, monkeypatch):
    """xelab_c_compile_failure_classified_design: 260 characters failed every time in the re-hold."""
    run = Mock(return_value=(0, "TEST PASSED\n"))
    monkeypatch.setattr(vivado, "_run", run)
    work = _work_dir_with_object_path_length(tmp_path, vivado.WINDOWS_MAX_PATH)
    assert len(vivado.xelab_object_path(work, "tb_snap")) == 260
    passed, error, kind = vivado.xsim_run([], tmp_path / "tb.v", "tb", RunConfig(mode="optimize"), work)
    assert not passed and kind == FailureKind.INFRA
    assert error.startswith("host path too long") and "260 characters" in error
    assert run.call_count == 0


@windows_only
def test_an_xelab_object_path_one_below_max_path_runs(tmp_path, monkeypatch):
    run = Mock(return_value=(0, "TEST PASSED\n"))
    monkeypatch.setattr(vivado, "_run", run)
    work = _work_dir_with_object_path_length(tmp_path, vivado.WINDOWS_MAX_PATH - 1)
    work.mkdir()
    assert vivado.xelab_path_too_long(work, "tb_snap") == ""
    assert vivado.xsim_run([], tmp_path / "tb.v", "tb", RunConfig(mode="optimize"), work)[0]
    assert run.call_count == 3


@pytest.mark.skipif(__import__("os").name == "nt", reason="non-Windows hosts have no MAX_PATH limit")
def test_no_path_limit_off_windows(tmp_path):
    assert vivado.xelab_path_too_long(tmp_path / ("x" * 300), "tb_snap") == ""
