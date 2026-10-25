"""Typed build behavior remains complete and distinct from incidental RTL values."""
import hashlib
import json
from pathlib import Path
import pytest
from autortl import contract_context,roles
from autortl.config import RunConfig
from autortl.contract_context import run_evidence,render_fixed_optimize_contract
from autortl.report_parser import VivadoMetrics

ROOT=Path(__file__).resolve().parents[1]
QUALIFIER="Invalid out_data is unspecified."


@pytest.fixture
def setup(tmp_path):
    source=tmp_path/"sync_fifo.v"
    source.write_text("module sync_fifo(input clk,rst,input [7:0] in_data,input in_valid,output in_ready,output [7:0] out_data,output out_valid,input out_ready); endmodule")
    tb=tmp_path/"sync_fifo_tb.v";tb.write_text("// independent top testbench fixture")
    spec=tmp_path/"design_spec.json"
    spec.write_bytes((ROOT/"curriculum/tier2/sync_fifo_build/design_spec.json").read_bytes())
    cfg=RunConfig(mode="build",top_module="sync_fifo",spec_path=spec,design_path=source,testbench_path=tb)
    return cfg,source,tb,spec,tmp_path


def evidence(setup,*,path=True):
    cfg,source,tb,spec,directory=setup
    return run_evidence(cfg,VivadoMetrics(),[source],tb,directory,{},build_spec_path=spec if path else None)


def test_complete_resolved_typed_build_spec_is_hashed_and_preserves_actual_qualifier(setup):
    facts=evidence(setup)
    spec_path=setup[3]
    spec=facts["build_spec"]
    assert spec["sha256"]==hashlib.sha256(spec_path.read_bytes()).hexdigest()
    assert spec["path"]==str(spec_path.resolve()) and spec["truncated"] is False
    module=spec["resolved_spec"]["modules"][0]
    assert QUALIFIER in module["behavior"]
    assert module["parameters"]=={"WIDTH":8,"DEPTH":3}
    assert module["ports"][2]["signed"] is False
    assert module["reset"]["duration_cycles"]==3
    text=render_fixed_optimize_contract(facts)
    assert QUALIFIER in text
    assert "Explicitly unspecified cases remain unspecified" in text
    assert "do not impose blanket equality" in text
    assert "Preserve all defined behavior" in text
    assert "No new pipeline stages, extra cycles" in text


def test_qualifier_after_source_preview_limit_is_never_silently_dropped(setup):
    spec=setup[3]
    raw=json.loads(spec.read_text())
    raw["modules"][0]["behavior"]="Behavior qualification context. "*700+QUALIFIER
    spec.write_text(json.dumps(raw))
    assert spec.read_text().index(QUALIFIER)>16000
    facts=evidence(setup)
    assert QUALIFIER in facts["build_spec"]["resolved_spec"]["modules"][0]["behavior"]
    assert QUALIFIER in render_fixed_optimize_contract(facts)


def test_oversized_semantic_build_spec_fails_instead_of_truncating(setup):
    spec=setup[3]
    raw=json.loads(spec.read_text())
    raw["modules"][0]["behavior"]="x"*(contract_context.MAX_BUILD_SPEC_CHARS+1)+QUALIFIER
    spec.write_text(json.dumps(raw))
    with pytest.raises(ValueError,match="semantic evidence exceeds budget"):
        evidence(setup)


def test_build_mode_cannot_silently_omit_spec(setup):
    with pytest.raises(ValueError,match="requires complete typed build spec"):
        evidence(setup,path=False)


def test_standalone_mode_cannot_borrow_build_unspecified_exception(setup):
    setup[0].mode="optimize"
    with pytest.raises(ValueError,match="standalone optimization cannot"):
        evidence(setup)
    facts=evidence(setup,path=False)
    assert facts["build_spec"] is None
    text=render_fixed_optimize_contract(facts)
    assert "Preserve the frozen source's ports" in text
    assert "do not infer unspecified behavior merely from missing test coverage" in text
    assert "do not impose blanket equality" not in text


def test_build_spec_hash_binds_the_same_single_read_as_semantic_content(setup,monkeypatch):
    spec=setup[3]
    raw=spec.read_bytes()
    original=Path.read_bytes
    reads=[]
    def snapshot(path):
        if path==spec:
            reads.append(path)
            return raw if len(reads)==1 else b"changed spec"
        return original(path)
    monkeypatch.setattr(Path,"read_bytes",snapshot)
    facts=evidence(setup)
    assert len(reads)==1
    assert facts["build_spec"]["sha256"]==hashlib.sha256(raw).hexdigest()
    assert QUALIFIER in facts["build_spec"]["resolved_spec"]["modules"][0]["behavior"]


@pytest.mark.parametrize("mode",["invalid_json","wrong_top","invalid_ports"])
def test_malformed_or_mismatched_spec_never_becomes_authority(setup,mode):
    spec=setup[3]
    if mode=="invalid_json":
        spec.write_text("not JSON")
    else:
        data=json.loads(spec.read_text())
        if mode=="wrong_top": data["top_name"]="wrong"
        else: data["modules"][0]["ports"][2]["width"]=0
        spec.write_text(json.dumps(data))
    with pytest.raises(ValueError,match="typed build spec"):
        evidence(setup)


def test_actual_generator_and_evaluator_prompts_carry_complete_build_qualifier(setup,monkeypatch):
    facts=evidence(setup)
    calls=[]
    monkeypatch.setattr(roles,"ask",lambda role,prompt,**kwargs:calls.append((role,prompt)) or "module sync_fifo; endmodule")
    generator,evaluator=roles.Generator(),roles.Evaluator()
    generator.run_context=evaluator.run_context=json.dumps(facts)
    from autortl.spec import DesignSpec
    module=DesignSpec.load(setup[3]).modules[0]
    generator.generate(module,"source","instruction","mutation",None)
    evaluator.evaluate(1,render_fixed_optimize_contract(facts),"ladder",VivadoMetrics(),"",0,3,None)
    assert [role for role,_ in calls]==["generator","evaluator"]
    assert all(QUALIFIER in prompt for _,prompt in calls)
    assert all("resolved_spec" in prompt for _,prompt in calls)
