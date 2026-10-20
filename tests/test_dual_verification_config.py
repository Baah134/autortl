"""Configuration boundaries for generated plus independent build verification."""
import json
from pathlib import Path
from unittest.mock import Mock
import pytest
import yaml
from autortl.config import RunConfig
from autortl.fsm import Orchestrator
from curriculum import runner
from tests.test_curriculum import frozen_runtime, successful_metrics
import run


@pytest.mark.parametrize("enabled",[False,True])
def test_generate_golden_roundtrip(enabled,tmp_path):
    cfg=RunConfig(mode="build",generate_golden=enabled,spec_path=tmp_path/"spec.json")
    cfg.save(tmp_path/"config.json")
    restored=RunConfig.load(tmp_path/"config.json")
    assert restored.generate_golden is enabled
    assert restored.to_dict()==cfg.to_dict()


def test_schema1_migration_defaults_only_new_field():
    old=RunConfig(mode="build").to_dict(); del old["generate_golden"]
    assert RunConfig.from_dict(old).generate_golden is False
    del old["target_part"]
    with pytest.raises(ValueError,match="target_part"):
        RunConfig.from_dict(old)


@pytest.mark.parametrize("value",[None,0,1,"true",[],{}])
def test_generate_golden_rejects_nonboolean_values(value):
    with pytest.raises(ValueError,match="boolean"):
        RunConfig(mode="build",generate_golden=value).to_dict()


def test_generate_golden_enabled_is_build_only():
    with pytest.raises(ValueError,match="build mode"):
        RunConfig(mode="optimize",generate_golden=True).to_dict()
    RunConfig(mode="optimize",generate_golden=False).validate()


@pytest.mark.parametrize("extra,enabled",[([],False),(["--generate-golden"],True)])
def test_build_cli_forwards_new_flag_and_preserves_independent_tb(monkeypatch,tmp_path,extra,enabled):
    orch=Mock(); orch.return_value.run.return_value={"status":"done"}
    monkeypatch.setattr(run,"Orchestrator",orch)
    assert run.main(["build","--spec","spec.json","--tb","independent.v",*extra])==0
    cfg=orch.call_args.args[0]
    assert cfg.generate_golden is enabled and cfg.testbench_path==Path("independent.v")


@pytest.mark.parametrize("command",[
    ["optimize","--design","m.v","--top","m"],
    ["bench","--tier","0"], ["resume","--run","somewhere"]])
def test_generate_golden_cli_option_is_rejected_outside_build(monkeypatch,command):
    orch=Mock(); monkeypatch.setattr(run,"Orchestrator",orch)
    with pytest.raises(SystemExit): run.main([*command,"--generate-golden"])
    orch.assert_not_called()


def make_entry(tmp_path,mode="build",enabled=True):
    entry=tmp_path/"curriculum/tier0/example"; entry.mkdir(parents=True)
    (entry/"spec.json").write_text("{}")
    (entry/"m.v").write_text("module m; endmodule")
    (entry/"tb.v").write_text("module m_tb; endmodule")
    meta={"mode":mode,"top":"m","tb":"tb.v","generate_golden":enabled}
    meta["spec" if mode=="build" else "design"]="spec.json" if mode=="build" else "m.v"
    (entry/"meta.yaml").write_text(yaml.safe_dump(meta))
    return entry,meta


@pytest.mark.parametrize("mode,value",[("build","true"),("build",1),("build",None),("optimize",True)])
def test_metadata_rejects_invalid_dual_verification_choice(tmp_path,mode,value):
    entry,_=make_entry(tmp_path,mode,value)
    with pytest.raises(ValueError,match="generate_golden"):
        runner._metadata(entry)


def test_curriculum_forwards_flag_and_changes_cohort_when_it_changes(tmp_path,monkeypatch):
    entry,meta=make_entry(tmp_path)
    root=entry.parents[1]
    monkeypatch.setattr(runner,"ROOT",root); monkeypatch.setattr(runner,"RESULTS",root/"results.jsonl")
    configurations=[]
    def construct(cfg,run_dir):
        configurations.append(cfg)
        run_dir.mkdir(parents=True)
        (run_dir/"runtime.json").write_text(json.dumps(frozen_runtime()))
        return Mock(run=Mock(return_value={"status":"done","best_metrics":successful_metrics()}))
    monkeypatch.setattr(runner,"Orchestrator",construct)
    assert runner.run_tier(0,output_root=tmp_path/"out")==0
    meta["generate_golden"]=False; (entry/"meta.yaml").write_text(yaml.safe_dump(meta))
    assert runner.run_tier(0,output_root=tmp_path/"out")==0
    rows=[json.loads(line) for line in runner.RESULTS.read_text().splitlines()]
    assert [cfg.generate_golden for cfg in configurations]==[True,False]
    assert [row["results"][0]["config"]["generate_golden"] for row in rows]==[True,False]
    assert rows[0]["cohort"]!=rows[1]["cohort"]
    assert rows[1]["consecutive_qualifying_runs"]==1


def test_resume_rejects_changing_saved_verification_choice(tmp_path):
    spec=tmp_path/"spec.json"; spec.write_text("{}")
    cfg=RunConfig(mode="build",spec_path=spec,generate_golden=True)
    o=Orchestrator(cfg,tmp_path/"run"); o._prepare_inputs()
    restored=RunConfig.load(o.state.run_dir/"config.json"); restored.generate_golden=False
    with pytest.raises(ValueError,match="Resume configuration changed: generate_golden"):
        Orchestrator(restored,o.state.run_dir)._prepare_inputs()


def test_skid_curriculum_requests_both_generated_and_independent_verification():
    root=Path(__file__).resolve().parents[1]
    meta=runner._metadata(root/"curriculum/tier2/skid_buffer_build")
    assert meta["generate_golden"] is True
    assert meta["mode"]=="build" and meta["tb"]=="skid_buffer_tb.v"
