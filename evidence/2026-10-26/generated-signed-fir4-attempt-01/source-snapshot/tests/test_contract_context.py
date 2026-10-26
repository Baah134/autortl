"""Contract roles share exact evidence without changing the grading environment."""
import hashlib
import json
from pathlib import Path
from unittest.mock import Mock
import pytest
from autortl import fsm, roles
from autortl.contract_context import file_evidence, flow_evidence, run_evidence, save_evidence, render_fixed_optimize_contract
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


@pytest.mark.parametrize("target", ["contract.md", "harness_facts.json", "iter_001/evaluation_facts.json"])
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


def test_timing_reports_have_complete_file_identity_and_bounded_preview(tmp_path):
    report = tmp_path / "timing_routed.rpt"
    report.write_text("Timing Summary\n" + "x" * 3000)
    context = flow_evidence(tmp_path)
    assert context["report_manifest"] == [{"path": str(report.resolve()),
        "sha256": hashlib.sha256(report.read_bytes()).hexdigest()}]
    assert context["report_headers"][0]["truncated"] is True
    assert len(context["report_headers"][0]["text"]) == 1800
    assert "routed" in context["metric_provenance"]
    assert "not complete reports" in context["metric_provenance"]


@pytest.mark.parametrize("role,method", [("planner", "plan"), ("evaluator", "evaluate")])
def test_model_failure_is_blocked_and_resume_retries_only_failed_call(tmp_path, monkeypatch, role, method):
    from autortl.config import RunConfig
    from llm.client import ModelCallError
    o = fsm.Orchestrator(configuration(tmp_path), tmp_path / "run")
    install_models(o)
    install_tools(monkeypatch)
    def fail(*args, **kwargs):
        o.budget.charge_llm()
        raise ModelCallError(role, "CODEX_QUOTA", {"returncode": 1}, "quota exhausted")
    setattr(getattr(o, role), method, fail)
    summary = o.run()
    assert summary["status"] == "model_blocked"
    assert summary["failure_kind"] == "infra"
    assert summary["best_iteration"] == 0
    assert summary["role"] == role and summary["error_code"] == "CODEX_QUOTA"
    assert summary["diagnostics"]["returncode"] == 1
    assert [entry["iteration"] for entry in o.state.read_designs()] == [0]
    assert "REJECT" not in o.state.read_progress()
    assert o.state.load_fsm()["phase"] == "MODEL_BLOCKED"
    assert o.state.read_events()[-1]["outcome"] == "INFRA_FAIL"
    assert json.loads((o.state.run_dir / "run_summary.json").read_text()) == summary
    calls = o.budget.llm_calls
    resumed = fsm.Orchestrator(RunConfig.load(o.state.run_dir / "config.json"), o.state.run_dir)
    models = install_models(resumed)
    tools = install_tools(monkeypatch)
    assert resumed.run()["best_iteration"] == 1
    assert models[(role, method)].call_count == 1
    if role == "evaluator":
        assert not tools
        assert resumed.budget.llm_calls == calls + 1
        assert models[("generator", "generate")].call_count == 0
    else:
        assert resumed.budget.llm_calls == calls + 3


def test_unsupported_parallel_execution_is_explicit(tmp_path):
    cfg = configuration(tmp_path)
    cfg.parallel_candidates = True
    with pytest.raises(ValueError, match="unsupported"):
        cfg.to_dict()
    cfg.parallel_candidates = False
    assert cfg.to_dict()["parallel_candidates"] is False


def test_power_metric_report_provenance_is_retained(tmp_path):
    report = tmp_path / "power.rpt"
    report.write_text("Total On-Chip Power (W) | 0.1")
    context = flow_evidence(tmp_path)
    assert context["report_manifest"][0]["sha256"] == hashlib.sha256(report.read_bytes()).hexdigest()
    assert context["report_headers"][0]["text"] == report.read_text()


def test_budget_exhaustion_after_model_block_preserves_verified_best(tmp_path, monkeypatch):
    from autortl.config import RunConfig
    from llm.client import ModelCallError
    cfg = configuration(tmp_path)
    cfg.max_llm_calls = 1
    o = fsm.Orchestrator(cfg, tmp_path / "run")
    install_models(o)
    install_tools(monkeypatch)
    def fail(*args, **kwargs):
        o.budget.charge_llm()
        raise ModelCallError("planner", "CODEX_QUOTA")
    o.planner.plan = fail
    assert o.run()["best_iteration"] == 0
    resumed = fsm.Orchestrator(RunConfig.load(o.state.run_dir / "config.json"), o.state.run_dir)
    install_models(resumed)
    tools = install_tools(monkeypatch)
    resumed.planner.plan = Mock(side_effect=RuntimeError("LLM_BUDGET: exhausted"))
    result = resumed.run()
    assert result["status"] == "budget_exhausted" and result["best_iteration"] == 0
    assert resumed.state.load_fsm()["best_iteration"] == 0
    assert resumed.budget.llm_calls == 1 and not tools
    assert [row["iteration"] for row in resumed.state.read_designs()] == [0]


@pytest.mark.parametrize("objective,field,direction", [
    ("minimize_luts", "lut_used", "strictly lower"),
    ("minimize_ffs", "ff_used", "strictly lower"),
    ("maximize_freq", "wns_ns", "strictly higher"),
    ("minimize_power", "dynamic_power_w", "strictly lower"),
])
def test_fixed_contract_is_stable_and_maps_actual_objective(tmp_path, objective, field, direction):
    cfg = configuration(tmp_path)
    cfg.objective = objective
    (tmp_path / "timing.xdc").write_text("create_clock -period 10 [get_ports clk]")
    (tmp_path / "timing_routed.rpt").write_text("actual timing report")
    facts = run_evidence(cfg, VivadoMetrics(), [cfg.design_path], cfg.testbench_path,
                         tmp_path, {"tools": "actual tool identity"})
    contract = render_fixed_optimize_contract(facts)
    assert contract == render_fixed_optimize_contract(json.loads(json.dumps(facts)))
    assert field in contract and direction in contract
    assert facts["sources"][0]["sha256"] in contract
    assert facts["testbench"]["sha256"] in contract
    assert facts["report_manifest"][0]["sha256"] in contract
    assert "actual tool identity" in contract and cfg.target_part in contract
    assert "create_clock -period 10" in contract
    assert "WNS >= 0" in contract and "WHS >= 0" in contract
    assert "previous verified best" in contract and "best_iteration 0" in contract


@pytest.mark.parametrize("tamper", ["change", "delete"])
def test_non_done_resume_rejects_altered_fixed_contract_before_new_model_calls(tmp_path, monkeypatch, tamper):
    from autortl.config import RunConfig
    o = fsm.Orchestrator(configuration(tmp_path), tmp_path / "run")
    install_models(o)
    install_tools(monkeypatch, fail_compile=True)
    with pytest.raises(KeyboardInterrupt):
        o.run()
    path = o.state.run_dir / "contract.md"
    if tamper == "delete":
        path.unlink()
    else:
        path.write_text("weaken all gates")
    resumed = fsm.Orchestrator(RunConfig.load(o.state.run_dir / "config.json"), o.state.run_dir)
    install_models(resumed, forbidden=True)
    tools = install_tools(monkeypatch)
    with pytest.raises(ValueError, match="Fixed optimization contract (changed|missing)"):
        resumed.run()
    assert not tools


@pytest.mark.parametrize("name,marker", [
    ("xvlog.log", "xvlog completed"), ("xelab.log", "xelab completed"),
    ("sim_log.txt", "TEST PASSED"), ("vivado_synth_output.log", "SYNTH_COMPLETE"),
])
def test_verification_log_preview_preserves_final_markers_and_full_hash(tmp_path, name, marker):
    path = tmp_path / name
    path.write_text("tool header\n" + "x" * 8000 + "\n" + marker + "\n")
    item, = flow_evidence(tmp_path)["verification_logs"]
    assert item["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert item["path"] == str(path.resolve())
    assert item["head"].startswith("tool header") and marker in item["tail"]
    assert len(item["head"]) == len(item["tail"]) == 1800
    assert item["truncated"] is True
    assert "do not independently" in item["preview_policy"]


def test_short_verification_log_is_not_truncated(tmp_path):
    (tmp_path / "sim_log.txt").write_text("TEST PASSED\n")
    item, = flow_evidence(tmp_path)["verification_logs"]
    assert item["head"] == (tmp_path / "sim_log.txt").read_bytes().decode("utf-8")
    assert item["tail"] == ""
    assert item["truncated"] is False


@pytest.mark.parametrize("annotation,known,cycles", [("", False, None), ("// @latency 0\n", True, 0), ("// @latency 2\n", True, 2)])
def test_run_evidence_latency_is_source_declared_not_assumed_zero(tmp_path, annotation, known, cycles):
    cfg = configuration(tmp_path)
    cfg.design_path.write_text(annotation + cfg.design_path.read_text())
    facts = run_evidence(cfg, VivadoMetrics(), [cfg.design_path], cfg.testbench_path, tmp_path, {})
    latency = facts["declared_latency"]
    assert latency["known"] is known and latency["cycles"] == cycles
    assert latency["source_sha256"] == hashlib.sha256(cfg.design_path.read_bytes()).hexdigest()
    assert "UNKNOWN, not zero" in latency["meaning"]
    assert "not independent proof" in latency["meaning"]
    contract = render_fixed_optimize_contract(facts)
    assert '"declared_latency"' in contract and "Unannotated numeric latency is UNKNOWN" in contract
