"""Assembled prompts use top latency evidence without inventing wrapper metadata."""
import json
from pathlib import Path
from unittest.mock import Mock
import pytest
from autortl import prompts, roles
from autortl.candidate_context import candidate_scope
from autortl.config import RunConfig
from autortl.contract_context import run_evidence, render_fixed_optimize_contract
from autortl.report_parser import VivadoMetrics
from autortl.verilog_interface import infer_module


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ("module sync_fifo(input clk,input rst,input [7:0] in_data,input in_valid,"
          "output in_ready,output [7:0] out_data,output out_valid,input out_ready); endmodule")


def context(tmp_path, mode, known):
    # Interface-only prompt fixture, not evidence of RTL compilation or behavior.
    text = ("// @latency 1\n" if known else "") + SOURCE
    source = tmp_path / "sync_fifo.v"; source.write_text(text, encoding="utf-8")
    tb = tmp_path / "sync_fifo_tb.v"; tb.write_text("// controlled prompt fixture", encoding="utf-8")
    cfg = RunConfig(mode=mode, top_module="sync_fifo", design_path=source, testbench_path=tb)
    kwargs = {}
    if mode == "build":
        spec = tmp_path / "design_spec.json"
        spec.write_bytes((ROOT / "curriculum/tier2/sync_fifo_build/design_spec.json").read_bytes())
        cfg.spec_path = spec
        kwargs["build_spec_path"] = spec
    metric = VivadoMetrics(sim_passed=True, timing_met=True, wns_ns=.318, whs_ns=.050)
    facts = run_evidence(cfg, metric, [source], tb, tmp_path, {}, **kwargs)
    return cfg, text, metric, facts, render_fixed_optimize_contract(facts)


@pytest.mark.parametrize("mode", ["build", "optimize"])
@pytest.mark.parametrize("known", [False, True])
@pytest.mark.parametrize("method", ["plan", "restart_plan", "propose_contract", "review_contract", "evaluate", "generate"])
def test_assembled_roles_use_authoritative_top_annotation_policy(tmp_path, monkeypatch, mode, known, method):
    cfg, source, metric, facts, contract = context(tmp_path, mode, known)
    ask = Mock(return_value="```verilog\n" + source + "\n```")
    monkeypatch.setattr(roles, "ask", ask)
    planner, generator, evaluator = roles.Planner(), roles.Generator(), roles.Evaluator()
    for role in (planner, generator, evaluator):
        role.run_context = json.dumps(facts, sort_keys=True) + "\n" + candidate_scope("sync_fifo", [])
    calls = {
        "plan": lambda: planner.plan(2, contract, "progress", [], metric, [], None),
        "restart_plan": lambda: planner.restart_plan(contract, 3, "prior attempts", metric, None),
        "propose_contract": lambda: planner.propose_contract(mode, cfg, metric, source, None),
        "review_contract": lambda: evaluator.review_contract(contract, None),
        "evaluate": lambda: evaluator.evaluate(2, contract, "static, compile and sim passed", metric, "", 0, 3, None),
        "generate": lambda: generator.generate(infer_module(source, "sync_fifo"), source, "preserve behavior", "standard", None),
    }
    calls[method]()
    assembled = ask.call_args.args[1] + "\n" + ask.call_args.kwargs["system"]
    assert prompts.LATENCY_AUTHORITY in ask.call_args.kwargs["system"]
    assert "Child typed-module latency metadata does not create a numeric annotation" in assembled
    assert "minimum transfer" in assembled and "deterministic gates" in assembled
    assert facts["declared_latency"]["known"] is known
    assert facts["declared_latency"]["cycles"] == (1 if known else None)
    if known:
        assert "require a matching // @latency 1 annotation" in contract
        if method == "generate":
            assert "Include a '// @latency 1' header matching" in assembled
    else:
        assert "missing @latency annotation is neither FAIL nor INVESTIGATE" in contract
        assert "require a matching // @latency" not in contract
        if method == "generate":
            assert "UNKNOWN numeric latency" in assembled
            assert "Include a '// @latency 1' header matching" not in assembled
    if mode == "build":
        child = facts["build_spec"]["resolved_spec"]["modules"][0]
        assert child["latency"] == 1
        assert "minimum age 1" in child["behavior"]
        assert "Invalid out_data is unspecified." in assembled
        assert "Typed child module contracts require an explicit numeric latency" in " ".join(assembled.split())
    else:
        assert facts["build_spec"] is None
        assert "Standalone optimization has no typed build" in contract


def test_unknown_aggregate_child_metadata_is_not_a_top_annotation_requirement(tmp_path):
    _, _, _, facts, contract = context(tmp_path, "build", False)
    assert facts["build_spec"]["resolved_spec"]["modules"][0]["latency"] == 1
    assert facts["declared_latency"]["known"] is False
    assert "Only known=true requires a matching numeric top annotation" in facts["declared_latency"]["meaning"]
    assert "must not block ACCEPT" in contract
    assert "minimum transfer age" in contract and "all deterministic checks remain mandatory" in contract


def test_evaluator_cannot_fail_unknown_top_for_annotation_alone():
    assert "missing top annotation is neither FAIL nor INVESTIGATE" in prompts.EVALUATOR_SYSTEM
    assert "only when declared_latency.known=true" in prompts.GENERATOR_SYSTEM
    assert "do not reject or demand investigation solely because the top has" in prompts.EVALUATE
