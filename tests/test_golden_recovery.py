"""A malformed generated oracle gets bounded diagnostic repair, never false credit."""
import hashlib
import json
from pathlib import Path
from unittest.mock import Mock
import pytest
from autortl import fsm
from autortl.config import RunConfig
from autortl.spec import ModuleSpec,Port,IOExample

GOOD = """def init():
    return {}
def step(state, inputs):
    return state, {"y": (inputs["a"] + 1) & 255}
"""
RTL = "module m(input [7:0] a, output [7:0] y); assign y=a+1'b1; endmodule"


@pytest.fixture
def oracle_build(tmp_path,monkeypatch):
    o=fsm.Orchestrator(RunConfig(mode="build",top_module="m"),tmp_path/"run")
    spec=ModuleSpec("m","increment modulo256",[Port("a","input",8),Port("y","output",8)],
                    examples=[IOExample({"a":1},{"y":2})])
    folder=tmp_path/"module"; folder.mkdir()
    monkeypatch.setattr(o,"_generate_verified",Mock(return_value=RTL))
    monkeypatch.setattr(fsm,"qualify_tb",Mock(return_value=(True,"controlled assertion proof")))
    return o,spec,folder


@pytest.mark.parametrize("bad",[
    "def init(:", "def init(): return {}",
    'def init(): return {}\ndef step(s,i): return s,{"y":i["missing"]}',
    'def init(): return {}\ndef step(s,i): return s,{"y":0}',
    'def init(): return {}\ndef step(s,i): return s,({"y":2} if i["a"]==1 else {"wrong":0})',
])
def test_oracle_program_errors_retry_once_with_diagnostic_and_source_receipt(oracle_build,monkeypatch,bad):
    o,spec,folder=oracle_build
    model=Mock(side_effect=[bad,GOOD]); monkeypatch.setattr(o.generator,"golden_model",model)
    assert o._build_module(spec,folder)==RTL
    assert model.call_count==2
    assert model.call_args_list[0].kwargs=={}
    assert model.call_args_list[1].kwargs["feedback"]
    rejected=json.loads((folder/"golden_attempt_1.log").read_text())
    accepted=json.loads((folder/"golden_attempt_2.log").read_text())
    assert rejected["status"]=="oracle_rejected" and len(rejected["diagnostic"])<=2020
    assert len(rejected["source_sha256"])==64
    assert accepted["status"]=="oracle_qualified"
    assert accepted["source_sha256"]==hashlib.sha256((folder/"golden.py").read_bytes()).hexdigest()
    assert o.state.read_designs()==[]


def test_two_bad_oracles_stop_without_rtl_generation_or_rejection_history(oracle_build,monkeypatch):
    o,spec,folder=oracle_build
    model=Mock(return_value="def init(:"); monkeypatch.setattr(o.generator,"golden_model",model)
    assert o._build_module(spec,folder) is None
    assert model.call_count==2
    o._generate_verified.assert_not_called()
    fsm.qualify_tb.assert_not_called()
    assert o.state.read_designs()==[]
    assert json.loads((folder/"golden_attempt_2.log").read_text())["status"]=="oracle_rejected"


@pytest.mark.parametrize("examples",[[],[IOExample({"a":1},{})],[IOExample({"a":1},{"y":2},10**12)]])
def test_invalid_anchors_stop_before_model_calls(oracle_build,monkeypatch,examples):
    o,spec,folder=oracle_build; spec.examples=examples
    model=Mock(); monkeypatch.setattr(o.generator,"golden_model",model)
    assert o._build_module(spec,folder) is None
    model.assert_not_called(); o._generate_verified.assert_not_called()
    assert json.loads((folder/"golden_qualification.log").read_text())["model_calls"]==0


def test_provider_failure_is_not_mislabeled_as_an_oracle_program_error(oracle_build,monkeypatch):
    o,spec,folder=oracle_build
    model=Mock(side_effect=RuntimeError("LLM_BUDGET: exhausted")); monkeypatch.setattr(o.generator,"golden_model",model)
    with pytest.raises(RuntimeError,match="LLM_BUDGET"):
        o._build_module(spec,folder)
    assert model.call_count==1 and not list(folder.glob("golden_attempt_*.log"))


def test_storage_failure_is_not_retried_as_model_code(oracle_build,monkeypatch):
    o,spec,folder=oracle_build
    model=Mock(return_value=GOOD); monkeypatch.setattr(o.generator,"golden_model",model)
    original=Path.write_text
    def write(path,*args,**kwargs):
        if path.name=="golden.py": raise PermissionError("controlled storage block")
        return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,"write_text",write)
    with pytest.raises(PermissionError,match="storage block"):
        o._build_module(spec,folder)
    assert model.call_count==1 and not list(folder.glob("golden_attempt_*.log"))
