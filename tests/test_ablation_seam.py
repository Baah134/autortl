"""Benchmark arm B seam (ablation_policy_seam_absent).

verification_policy=skip_generated_tb_mutations skips only the bug-injection
qualification of generated module testbenches, records the skip, and keeps
candidate simulation gating. The default and every shipped flow is "full".
"""
import json
from unittest.mock import Mock

import pytest

import run
from autortl import fsm
from autortl.config import VERIFICATION_POLICIES, RunConfig
from tests.test_fsm_build import create
from tests.test_golden_reset_protocol import COUNTER


def test_default_policy_is_full():
    assert RunConfig(mode="build").verification_policy == "full"
    assert RunConfig(mode="optimize").verification_policy == "full"
    assert VERIFICATION_POLICIES == ("full", "skip_generated_tb_mutations")


@pytest.mark.parametrize("value", ["", "skip", "none", "FULL", None, True])
def test_invalid_policy_rejected(value):
    with pytest.raises(ValueError, match="verification_policy"):
        RunConfig(mode="build", verification_policy=value).validate()


def test_config_round_trip_and_legacy_default(tmp_path):
    cfg = RunConfig(mode="build", verification_policy="skip_generated_tb_mutations", work_dir=tmp_path)
    cfg.save(tmp_path / "config.json")
    saved = json.loads((tmp_path / "config.json").read_text())
    assert saved["verification_policy"] == "skip_generated_tb_mutations"
    assert RunConfig.load(tmp_path / "config.json").verification_policy == "skip_generated_tb_mutations"
    saved.pop("verification_policy")  # a config.json written before the seam existed
    assert RunConfig.from_dict(saved).verification_policy == "full"
    saved["verification_policy"] = "skip_everything"
    with pytest.raises(ValueError, match="verification_policy"):
        RunConfig.from_dict(saved)


def test_cli_flag_for_build_and_optimize_only(tmp_path, monkeypatch):
    seen = []

    class Fake:
        def __init__(self, cfg, run_dir=None):
            seen.append(cfg)
            self.state = Mock(run_dir=tmp_path)

        def run(self):
            return {"status": "done"}

    monkeypatch.setattr(run, "Orchestrator", Fake)
    monkeypatch.setattr("llm.client.check_model", lambda model: None)
    spec = tmp_path / "spec.md"; spec.write_text("x")
    design = tmp_path / "d.v"; design.write_text("module d; endmodule")
    assert run.main(["build", "--spec", str(spec)]) == 0
    assert run.main(["build", "--spec", str(spec), "--verification-policy", "skip_generated_tb_mutations"]) == 0
    assert run.main(["optimize", "--design", str(design), "--top", "d",
                     "--verification-policy", "skip_generated_tb_mutations"]) == 0
    assert [c.verification_policy for c in seen] == ["full", "skip_generated_tb_mutations",
                                                      "skip_generated_tb_mutations"]
    with pytest.raises(SystemExit):
        run.main(["build", "--spec", str(spec), "--verification-policy", "partial"])
    with pytest.raises(SystemExit):
        run.main(["bench", "--tier", "0", "--verification-policy", "skip_generated_tb_mutations"])


def generated_build(tmp_path, monkeypatch, policy):
    """The controlled typed build with a generated oracle/testbench (no --tb)."""
    o, synthesis = create(tmp_path, monkeypatch)
    o.cfg.testbench_path = None
    o.cfg.verification_policy = policy
    monkeypatch.setattr(o.generator, "golden_model", Mock(return_value=COUNTER.replace('"count": 99', '"count": 0')))
    sims = []
    original_sim = fsm.vivado.xsim_run

    def sim(files, tb, top, config, work, **kwargs):
        sims.append(work)
        return original_sim(files, tb, top, config, work, **kwargs)

    monkeypatch.setattr(fsm.vivado, "xsim_run", sim)
    qualify = Mock(wraps=o._qualify_source)
    monkeypatch.setattr(o, "_qualify_source", qualify)
    legacy = Mock(side_effect=AssertionError("journaled run must not use direct qualify_tb"))
    monkeypatch.setattr(fsm, "qualify_tb", legacy)
    return o, synthesis, qualify, sims


def test_skip_policy_skips_only_generated_tb_qualification_and_records_it(tmp_path, monkeypatch):
    o, synthesis, qualify, sims = generated_build(tmp_path, monkeypatch, "skip_generated_tb_mutations")
    result = o.run()
    assert result["status"] == "done"
    qualify.assert_not_called()
    folder = o.state.run_dir / "modules/counter8_core"
    assert not (folder / "tbqual").exists()
    # Candidate simulation against the unqualified generated testbench still ran.
    assert any("candidate" in part for work in sims for part in work.parts)
    events = [e for e in o.state.read_events() if e.get("stage") == "tb_qualification"]
    assert len(events) == 1
    assert events[0]["outcome"] == "skipped_by_policy"
    assert events[0]["module"] == "counter8_core"
    assert events[0]["verification_policy"] == "skip_generated_tb_mutations"
    assert result["verification_policy"] == "skip_generated_tb_mutations"
    saved = json.loads((o.state.run_dir / "run_summary.json").read_text())
    assert saved["verification_policy"] == "skip_generated_tb_mutations"
    assert json.loads((o.state.run_dir / "config.json").read_text())["verification_policy"] == "skip_generated_tb_mutations"


def test_skip_policy_candidate_simulation_still_gates(tmp_path, monkeypatch):
    o, synthesis, qualify, sims = generated_build(tmp_path, monkeypatch, "skip_generated_tb_mutations")

    def failing(files, tb, top, config, work, **kwargs):
        work.mkdir(parents=True, exist_ok=True)
        (work / "sim_log.txt").write_text("FAIL wrong count\nTEST FAILED: 1 errors\n", encoding="utf-8")
        return False, "Testbench failures:\nFAIL wrong count", fsm.FailureKind.DESIGN

    monkeypatch.setattr(fsm.vivado, "xsim_run", failing)
    monkeypatch.setattr(o.generator, "fix", Mock(return_value=o.generator.generate.return_value))
    result = o.run()
    assert result["status"] != "done"
    assert result["verification_policy"] == "skip_generated_tb_mutations"
    qualify.assert_not_called()
    synthesis.assert_not_called()
    assert not (o.state.run_dir / "counter8_best.v").exists()


def test_full_policy_qualifies_generated_tb(tmp_path, monkeypatch):
    o, synthesis, qualify, sims = generated_build(tmp_path, monkeypatch, "full")
    result = o.run()
    assert result["status"] == "done"
    qualify.assert_called_once()
    assert "verification_policy" not in result
    assert not [e for e in o.state.read_events() if e.get("stage") == "tb_qualification"]
    assert (o.state.run_dir / "modules/counter8_core/tbqual/qualification.json").is_file()


def test_skip_policy_still_qualifies_supplied_trusted_tb(tmp_path, monkeypatch):
    o, synthesis = create(tmp_path, monkeypatch)
    o.cfg.verification_policy = "skip_generated_tb_mutations"
    qualify = Mock(wraps=o._qualify_source)
    monkeypatch.setattr(o, "_qualify_source", qualify)
    result = o.run()
    assert result["status"] == "done"
    qualify.assert_called_once()
    assert not [e for e in o.state.read_events() if e.get("stage") == "tb_qualification"]


def test_resume_refuses_policy_change(tmp_path, monkeypatch):
    o, synthesis, qualify, sims = generated_build(tmp_path, monkeypatch, "full")
    assert o.run()["status"] == "done"
    cfg = RunConfig.load(o.state.run_dir / "config.json")
    assert cfg.verification_policy == "full"
    cfg.verification_policy = "skip_generated_tb_mutations"
    with pytest.raises(ValueError, match="Resume configuration changed: verification_policy"):
        fsm.Orchestrator(cfg, o.state.run_dir).run()
