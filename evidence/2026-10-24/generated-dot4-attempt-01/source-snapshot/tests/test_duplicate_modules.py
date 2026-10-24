"""Observed duplicate-definition warnings must fail even with successful exits."""
from pathlib import Path
from unittest.mock import Mock
import pytest
from autortl import vivado
from autortl.config import RunConfig
from autortl.triage import FailureKind

FIXTURES=Path(__file__).parent/"fixtures"


def mocked_run(monkeypatch,text,returncode=0):
    def run(args,work,timeout,log):
        log.write_text(text,encoding="utf-8")
        return returncode,text
    call=Mock(side_effect=run)
    monkeypatch.setattr(vivado,"_run",call)
    return call


@pytest.mark.parametrize("stage,fixture,identifier",[
    ("compile","duplicate_xvlog.log","VRFC 10-3609"),
    ("synthesis","duplicate_synth.log","Synth 8-9873")])
@pytest.mark.parametrize("returncode",[0,1])
def test_duplicate_definition_is_design_failure_and_keeps_raw_log(tmp_path,monkeypatch,stage,fixture,identifier,returncode):
    raw=(FIXTURES/fixture).read_text()
    mocked_run(monkeypatch,raw,returncode)
    cfg=RunConfig(mode="optimize")
    if stage=="compile":
        result=vivado.xvlog_check([tmp_path/"m.v"],cfg,tmp_path)
        log=tmp_path/"xvlog.log"
    else:
        result=vivado.run_synthesis([tmp_path/"m.v"],"m",cfg,tmp_path)
        log=tmp_path/"vivado_synth_output.log"
    assert result[0] is False and result[2]==FailureKind.DESIGN
    assert identifier in result[1]
    assert log.read_text()==raw


def test_simulation_stops_before_elaboration_when_xvlog_overwrites_module(tmp_path,monkeypatch):
    raw=(FIXTURES/"duplicate_xvlog.log").read_text()
    calls=mocked_run(monkeypatch,raw)
    cfg=RunConfig(mode="optimize",xvlog_bin="mock-xvlog",xelab_bin="mock-xelab",xsim_bin="mock-xsim")
    result=vivado.xsim_run([tmp_path/"m.v"],tmp_path/"tb.v","m_tb",cfg,tmp_path)
    assert result[0] is False and result[2]==FailureKind.DESIGN
    assert calls.call_count==1 and calls.call_args.args[0][0]=="mock-xvlog"
    assert not (tmp_path/"xelab.log").exists()


@pytest.mark.parametrize("stage",["compile","synthesis"])
def test_ordinary_warning_remains_accepted(tmp_path,monkeypatch,stage):
    raw="WARNING: [VRFC 10-36090] unrelated warning\nWARNING: [Synth 8-98730] unrelated warning\nSYNTH_COMPLETE\n"
    mocked_run(monkeypatch,raw)
    cfg=RunConfig(mode="optimize")
    result=vivado.xvlog_check([],cfg,tmp_path) if stage=="compile" else vivado.run_synthesis([],"m",cfg,tmp_path)
    assert result==(True,"",FailureKind.DESIGN)


@pytest.mark.parametrize("stage,fixture",[("compile","duplicate_xvlog.log"),("synthesis","duplicate_synth.log")])
def test_nonzero_infrastructure_failure_takes_precedence_over_duplicate_diagnostic(tmp_path,monkeypatch,stage,fixture):
    raw=(FIXTURES/fixture).read_text()+"ERROR: license server Connection refused\n"
    mocked_run(monkeypatch,raw,1)
    cfg=RunConfig(mode="optimize")
    result=vivado.xvlog_check([],cfg,tmp_path) if stage=="compile" else vivado.run_synthesis([],"m",cfg,tmp_path)
    assert result[0] is False and result[2]==FailureKind.INFRA


def test_duplicate_diagnostic_is_retained_even_when_later_log_is_long(tmp_path,monkeypatch):
    raw=(FIXTURES/"duplicate_xvlog.log").read_text()+"ordinary analysis continues\n"*1000
    mocked_run(monkeypatch,raw)
    result=vivado.xvlog_check([],RunConfig(mode="optimize"),tmp_path)
    assert result[0] is False and "VRFC 10-3609" in result[1]
