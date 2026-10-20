"""Contract roles share exact evidence without changing the grading environment."""
import hashlib
import json
from pathlib import Path
from unittest.mock import Mock
import pytest
from autortl import fsm, roles
from autortl.contract_context import file_evidence, flow_evidence, run_evidence, save_evidence
from autortl.roles import Evaluation
from autortl.report_parser import VivadoMetrics
from tests.test_fsm_resume import configuration, install_models, install_tools


def test_context_records_actual_sources_testbench_and_constraints(tmp_path):
    cfg = configuration(tmp_path)
    report = tmp_path / "utilization_routed.rpt"
    report.write_text("Tool Version : actual local version\n")
    (tmp_path / "timing_io.tcl").write_text("set_input_delay -clock clk 0 [all_inputs]")
    metrics = VivadoMetrics(sim_passed=True, lut_used=20, ff_used=8, wns_ns=1, whs_ns=.1)
    context = run_evidence(cfg, metrics, [cfg.design_path], cfg.testbench_path, tmp_path, {"tools": "known"})
    assert context["top_module"] == "m"
    assert context["sources"][0]["sha256"] == hashlib.sha256(cfg.design_path.read_bytes()).hexdigest()
    assert context["sources"][0]["text"] == cfg.design_path.read_text()
    assert context["testbench_top"] == "m_tb"
    assert context["simulation"]["required_verdict"] == "TEST PASSED"
    assert "actual local version" in context["report_headers"][0]["text"]
    assert context["flow_and_constraints"][0]["path"].endswith("timing_io.tcl")


def test_truncation_is_explicit_and_hash_still_covers_all_bytes(tmp_path):
    path = tmp_path / "source.v"
    path.write_text("x" * 20000)
    evidence = file_evidence(path, 100)
    assert len(evidence["text"]) == 100 and evidence["truncated"]
    assert evidence["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()


def test_saved_context_is_idempotent_and_tamper_fails(tmp_path):
    path = tmp_path / "facts.json"
    first = save_evidence(path, {"fixed": 1})
    assert save_evidence(path, {"fixed": 1}) == first
    with pytest.raises(ValueError, match="changed since checkpoint"):
        save_evidence(path, {"fixed": 2})
    path.write_text("{}")
    with pytest.raises(ValueError, match="changed since checkpoint"):
        save_evidence(path, {"fixed": 1})


def test_every_contract_call_gets_same_facts_and_evaluation_gets_candidate(tmp_path, monkeypatch):
    prompts = []
    monkeypatch.setattr(roles, "ask", lambda role, prompt, **kwargs: prompts.append((role, prompt)) or "ACCEPT")
    cfg = configuration(tmp_path)
    metrics = VivadoMetrics(sim_passed=True)
    planner, evaluator = roles.Planner(), roles.Evaluator()
    planner.run_context = evaluator.run_context = '{"fixed_tool": "2025.2"}'
    evaluator.candidate_context = '{"candidate": "exact RTL"}'
    planner.propose_contract("optimize", cfg, metrics, "source" * 1500, None)
    planner.refine_contract("contract", "feedback", None)
    evaluator.review_contract("contract", None)
    evaluator.evaluate(1, "contract", "passed", metrics, "", 0, 3, None)
    assert len(prompts) == 4
    assert all('{"fixed_tool": "2025.2"}' in p for _, p in prompts)
    assert "source" * 1500 in prompts[0][1]
    assert '{"candidate": "exact RTL"}' in prompts[-1][1]


def test_fsm_persists_current_and_previous_evaluation_evidence(tmp_path, monkeypatch):
    o = fsm.Orchestrator(configuration(tmp_path), tmp_path / "run")
    install_models(o)
    install_tools(monkeypatch)
    assert o.run()["best_iteration"] == 1
    run = o.state.run_dir
    baseline = json.loads((run / "harness_facts.json").read_text())
    candidate = json.loads((run / "iter_001/evaluation_facts.json").read_text())
    assert baseline["baseline_metrics"]["lut_used"] == 20
    assert candidate["candidate_metrics"]["lut_used"] == 10
    assert candidate["previous_best_metrics"]["lut_used"] == 20
    assert candidate["measured_improvement"] is True
    assert o.planner.run_context == o.evaluator.run_context


@pytest.mark.parametrize("target", ["harness_facts.json", "iter_001/evaluation_facts.json"])
def test_done_resume_rejects_altered_contract_evidence(tmp_path, monkeypatch, target):
    o = fsm.Orchestrator(configuration(tmp_path), tmp_path / "run")
    install_models(o)
    install_tools(monkeypatch)
    o.run()
    (o.state.run_dir / target).write_text("{}")
    with pytest.raises(ValueError, match="report evidence"):
        o.run()


def test_accept_with_failed_criteria_cannot_promote(tmp_path, monkeypatch):
    o = fsm.Orchestrator(configuration(tmp_path), tmp_path / "run")
    install_models(o)
    install_tools(monkeypatch)
    o.evaluator.evaluate = Mock(return_value=Evaluation("contradictory", "ACCEPT", 1, 1))
    assert o.run()["best_iteration"] == 0


def test_actual_candidate_flow_is_recorded(tmp_path):
    (tmp_path / "synth.tcl").write_text("synth_design -retiming\nphys_opt_design")
    assert "-retiming" in flow_evidence(tmp_path)["flow_and_constraints"][0]["text"]


@pytest.mark.parametrize("fixture", ["evaluation_missing_summary.md", "evaluation_contradiction.md"])
def test_malformed_or_contradictory_evaluation_rejects(fixture):
    raw = (Path(__file__).parent / "fixtures" / fixture).read_text(encoding="utf-8")
    evaluation = Evaluation.parse(raw)
    assert evaluation.recommendation == "REJECT" and evaluation.failed > 0


def test_complete_valid_evaluation_accepts():
    raw = (Path(__file__).parent / "fixtures/evaluation_valid.md").read_text(encoding="utf-8")
    assert Evaluation.parse(raw).recommendation == "ACCEPT"
    assert Evaluation.parse(raw.replace("Passed: 3 of 3", "Passed: 2 of 3")).recommendation == "REJECT"


def test_investigation_does_not_count_as_success():
    raw = (Path(__file__).parent / "fixtures/evaluation_contradiction.md").read_text(encoding="utf-8")
    assert Evaluation.parse(raw.replace("FAIL", "INVESTIGATE")).recommendation == "REJECT"
