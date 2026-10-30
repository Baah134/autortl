"""Post-build edit scope (taxonomy frozen_children_block_build_optimization).

With a trusted integration testbench the optimizer edits one unit holding every
generated child and the mechanical top; without one the children stay frozen.
No Vivado, no model: tools and roles are controlled fakes.
"""
import json
from pathlib import Path
from unittest.mock import Mock
import pytest
from autortl import fsm, companions
from autortl.config import RunConfig
from autortl.report_parser import VivadoMetrics
from autortl.roles import Evaluation
from autortl.triage import FailureKind
from tests.test_fsm_build import RTL, create

ROOT = Path(__file__).resolve().parents[1]
GATE = "`timescale 1ns/1ps\n// @latency 0\nmodule enable_gate(input enable, output en_q); assign en_q = enable; endmodule"
CORE = "`timescale 1ns/1ps\n" + RTL
# A whole-unit candidate: the children are merged and renamed; the top keeps its contract.
MERGED = ("`timescale 1ns/1ps\n"
          "module cnt_core(input clk,input rst,input enable,output reg [7:0] count); "
          "always @(posedge clk) if(rst) count<=0; else if(enable) count<=count+1'b1; endmodule\n"
          "module counter8(input wire clk, input wire rst, input wire enable, output wire [7:0] count);\n"
          "    cnt_core u_core(.clk(clk), .rst(rst), .enable(enable), .count(count));\n"
          "endmodule\n")


def two_module_spec(tmp_path):
    data = json.loads((ROOT / "curriculum/tier1/counter8_build/design_spec.json").read_text())
    data["modules"].insert(0, {
        "name": "enable_gate", "behavior": "en_q equals enable combinationally.",
        "ports": [{"name": "enable", "direction": "input", "width": 1},
                  {"name": "en_q", "direction": "output", "width": 1}],
        "latency": 0, "compare_mode": "fixed_latency",
        "reset": {"signal": "rst", "kind": "sync", "active_high": True},
        "examples": [{"inputs": {"enable": 1}, "expected": {"en_q": 1}}]})
    data["connections"] = [{"src_module": "enable_gate", "src_port": "en_q",
                            "dst_module": "counter8_core", "dst_port": "enable"}]
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(data))
    return path


def children(m, mdir):
    return GATE if m.name == "enable_gate" else CORE


def patch_roles(o, monkeypatch, generated=RTL, evaluation=None):
    monkeypatch.setattr(o, "_build_module", Mock(side_effect=children))
    generate = Mock(return_value=generated)
    monkeypatch.setattr(o.generator, "generate", generate)
    monkeypatch.setattr(o.generator, "fix", Mock(side_effect=AssertionError("no repair expected")))
    monkeypatch.setattr(o.planner, "plan", Mock(return_value="plan"))
    monkeypatch.setattr(o.evaluator, "evaluate", Mock(return_value=evaluation or Evaluation("REJECT", "REJECT", 1, 0)))
    return generate


def record_simulations(monkeypatch):
    calls = []
    original = fsm.vivado.xsim_run
    def simulate(files, tb, top, config, work, **kwargs):
        calls.append({"files": [Path(f).resolve() for f in files], "tb": Path(tb).resolve(), "work": Path(work)})
        return original(files, tb, top, config, work, **kwargs)
    monkeypatch.setattr(fsm.vivado, "xsim_run", simulate)
    return calls


def multi(tmp_path, monkeypatch, **kwargs):
    o, synthesis = create(tmp_path, monkeypatch)
    o.cfg.spec_path = two_module_spec(tmp_path)
    generate = patch_roles(o, monkeypatch, **kwargs)
    return o, synthesis, generate, record_simulations(monkeypatch)


def test_trusted_testbench_hands_one_editable_unit_without_companions(tmp_path, monkeypatch):
    o, synthesis, generate, sims = multi(tmp_path, monkeypatch)
    result = o.run()
    assert result["status"] == "done" and result["top_module"] == "counter8"
    assert result["edit_scope"] == "whole_design"
    run = o.state.run_dir
    unit = run / "modules" / "counter8_unit.v"
    text = unit.read_text()
    # Children first (spec order), the mechanical top last, the verified text unchanged.
    assert text == GATE + "\n" + CORE + "\n" + (run / "modules/counter8.v").read_text()
    assert text.index("module enable_gate") < text.index("module counter8_core") < text.index("module counter8 ")
    assert o.cfg.design_path == unit
    # Baseline and every candidate simulate the unit alone against the supplied testbench.
    baseline = [c for c in sims if c["work"] == run / "iter_000"]
    assert baseline and baseline[0]["files"] == [(run / "iter_000/counter8.v").resolve()]
    assert baseline[0]["tb"].name == "testbench_path.v"
    assert (run / "iter_000/counter8.v").read_text() == text
    facts = json.loads((run / "harness_facts.json").read_text())
    assert facts["edit_scope"]["mode"] == "whole_design"
    assert facts["edit_scope"]["children"] == ["enable_gate", "counter8_core"]
    assert facts["edit_scope"]["testbench_modules"] == []
    assert facts["execution_context"]["dependencies"] == []
    assert [Path(s["path"]).name for s in facts["sources"]] == ["counter8.v"]
    contract = o.state.read_contract()
    assert "## Edit boundary" in contract and "not evidence for changed children" in contract
    scope = o.generator.run_context
    assert "ONE unit holding every generated child module" in scope
    assert "Companion files/modules are frozen" not in scope
    assert '"frozen_companions": []' in scope
    # The generator edits the whole unit against the top's contract.
    contract_arg, seed = generate.call_args[0][:2]
    assert contract_arg.name == "counter8" and seed == text
    assert json.loads((run / "state.json").read_text())["edit_scope"]["mode"] == "whole_design"


def test_without_trusted_top_testbench_children_stay_frozen(tmp_path, monkeypatch):
    o, synthesis, generate, sims = multi(tmp_path, monkeypatch)
    # A supplied testbench that never instantiates the top cannot verify changed children.
    tb = tmp_path / "child_only_tb.v"
    tb.write_text("`timescale 1ns/1ps\nmodule counter8_tb; reg clk=0; wire [7:0] count;\n"
                  "counter8_core dut(.clk(clk),.rst(1'b0),.enable(1'b1),.count(count));\nendmodule\n")
    o.cfg.testbench_path = tb
    result = o.run()
    assert result["status"] == "done" and result["edit_scope"] == "frozen_children"
    run = o.state.run_dir
    assert not (run / "modules/counter8_unit.v").exists()
    assert (run / "iter_000/counter8.v").read_text() == (run / "modules/counter8.v").read_text()
    baseline = [c for c in sims if c["work"] == run / "iter_000"][0]
    assert baseline["files"] == [(run / p).resolve() for p in
                                 ("iter_000/counter8.v", "modules/enable_gate/enable_gate.v",
                                  "modules/counter8_core/counter8_core.v")]
    facts = json.loads((run / "harness_facts.json").read_text())
    assert facts["edit_scope"]["mode"] == "frozen_children"
    assert "does not instantiate the top counter8" in facts["edit_scope"]["reason"]
    assert len(facts["execution_context"]["dependencies"]) == 2
    assert "Companion files/modules are frozen" in o.generator.run_context
    assert "Reason: The supplied testbench does not instantiate" in o.state.read_contract()


def test_single_module_build_without_supplied_testbench_keeps_frozen_child(tmp_path, monkeypatch):
    from tests.test_golden_reset_protocol import COUNTER
    o, synthesis = create(tmp_path, monkeypatch)
    o.cfg.testbench_path = None
    monkeypatch.setattr(o.generator, "golden_model", Mock(return_value=COUNTER.replace('"count": 99', '"count": 0')))
    result = o.run()
    assert result["status"] == "done" and result["edit_scope"] == "frozen_children"
    facts = json.loads((o.state.run_dir / "harness_facts.json").read_text())
    assert "No trusted independent integration testbench" in facts["edit_scope"]["reason"]
    assert "Companion files/modules are frozen" in o.generator.run_context


@pytest.mark.parametrize("candidate,reason", [
    (GATE + "\n" + CORE, "module name mismatch"),                       # top dropped
    (MERGED.replace("module counter8(", "module counter9("), "module name mismatch"),   # top renamed
])
def test_candidate_without_the_top_is_rejected_before_tools(tmp_path, monkeypatch, candidate, reason):
    o, synthesis, generate, sims = multi(tmp_path, monkeypatch, generated=candidate)
    result = o.run()
    assert result["status"] == "done" and result["best_iteration"] == 0
    assert synthesis.call_count == 1
    assert not [c for c in sims if "cand_" in str(c["work"])]
    outcome = json.loads((o.state.run_dir / "iter_001/proposal_outcome.json").read_text())
    assert outcome["candidates"][0]["status"] == "design_rejected"
    assert reason in outcome["candidates"][0]["reason"]


def accepting(tmp_path, monkeypatch):
    o, synthesis, generate, sims = multi(tmp_path, monkeypatch, generated=MERGED,
                                         evaluation=Evaluation("ACCEPT", "ACCEPT", 1, 0))
    def metrics(work):
        lut = 5 if "cand_" in str(work) else 6
        return VivadoMetrics(sim_passed=True, lut_used=lut, lut_total=20800, ff_used=8, ff_total=41600,
                             wns_ns=7, whs_ns=0.2, timing_met=True)
    monkeypatch.setattr(fsm.vivado, "full_metrics", Mock(side_effect=metrics))
    return o, synthesis, generate, sims


def test_changed_children_are_verified_by_trusted_testbench_and_best_holds_all_modules(tmp_path, monkeypatch):
    o, synthesis, generate, sims = accepting(tmp_path, monkeypatch)
    result = o.run()
    assert result["status"] == "done" and result["best_iteration"] == 1
    run = o.state.run_dir
    candidate = [c for c in sims if "cand_" in str(c["work"])][0]
    assert candidate["files"] == [(candidate["work"] / "counter8.v").resolve()]
    assert candidate["tb"].name == "testbench_path.v"
    best = (run / "counter8_best.v").read_text()
    assert best == MERGED
    assert "module cnt_core" in best and "module counter8(" in best
    assert result["best_code_hash"]
    designs = [json.loads(line) for line in (run / "designs.jsonl").read_text().splitlines()]
    assert designs[-1]["is_best"] is True and designs[-1]["lut_used"] == 5
    resumed = fsm.Orchestrator(RunConfig.load(run / "config.json"), run)
    assert resumed.run() == result


def test_resume_keeps_whole_design_mode(tmp_path, monkeypatch):
    o, synthesis, generate, sims = accepting(tmp_path, monkeypatch)
    monkeypatch.setattr(o.evaluator, "evaluate", Mock(side_effect=KeyboardInterrupt("interrupted")))
    with pytest.raises(KeyboardInterrupt):
        o.run()
    run = o.state.run_dir
    assert json.loads((run / "state.json").read_text())["edit_scope"]["mode"] == "whole_design"
    contract = o.state.read_contract()
    resumed = fsm.Orchestrator(RunConfig.load(run / "config.json"), run)
    generate = patch_roles(resumed, monkeypatch, generated="", evaluation=Evaluation("ACCEPT", "ACCEPT", 1, 0))
    generate.side_effect = AssertionError("completed generation must replay")
    result = resumed.run()
    assert result["status"] == "done" and result["edit_scope"] == "whole_design"
    assert resumed.cfg.design_path == run / "modules/counter8_unit.v"
    assert resumed.state.read_contract() == contract
    assert (run / "counter8_best.v").read_text() == MERGED


def test_resume_rejects_a_changed_edit_scope(tmp_path, monkeypatch):
    o, synthesis, generate, sims = multi(tmp_path, monkeypatch)
    monkeypatch.setattr(o.evaluator, "evaluate", Mock(side_effect=KeyboardInterrupt("interrupted")))
    monkeypatch.setattr(o.generator, "generate", Mock(return_value=MERGED))
    with pytest.raises(KeyboardInterrupt):
        o.run()
    run = o.state.run_dir
    saved = json.loads((run / "state.json").read_text())
    saved["edit_scope"]["mode"] = "frozen_children"
    (run / "state.json").write_text(json.dumps(saved))
    resumed = fsm.Orchestrator(RunConfig.load(run / "config.json"), run)
    patch_roles(resumed, monkeypatch)
    with pytest.raises(ValueError, match="edit scope changed"):
        resumed.run()


@pytest.mark.parametrize("scope", ["whole_design", "frozen_children"])
def test_done_binds_generated_children_in_both_scopes(tmp_path, monkeypatch, scope):
    o, synthesis, generate, sims = multi(tmp_path, monkeypatch)
    if scope == "frozen_children":
        tb = tmp_path / "child_only_tb.v"
        tb.write_text("module counter8_tb; endmodule\n")
        o.cfg.testbench_path = tb
    result = o.run()
    assert result["status"] == "done" and result["edit_scope"] == scope
    child = o.state.run_dir / "modules/enable_gate/enable_gate.v"
    child.write_bytes(child.read_bytes() + b"\n// changed child identity\n")
    resumed = fsm.Orchestrator(RunConfig.load(o.state.run_dir / "config.json"), o.state.run_dir)
    with pytest.raises(ValueError, match="Completed"):
        resumed.run()


# --- the boundary gate on its own -----------------------------------------------------------------

TOP = ("module top(input clk, input a, output y);\n"
       "    wire w;\n    child u(.clk(clk), .a(a), .y(w));\n    assign y = w;\nendmodule\n")
CHILD = "module child(input clk, input a, output reg y); always @(posedge clk) y <= a; endmodule\n"


def test_unit_gate_accepts_any_children_when_testbench_tests_only_the_top():
    assert companions.unit_violation(CHILD + TOP, "top", [], Path("tb.v")) == ""
    inlined = "module top(input clk, input a, output reg y); always @(posedge clk) y <= a; endmodule\n"
    assert companions.unit_violation(inlined, "top", [], Path("tb.v")) == ""


def test_unit_gate_rejects_missing_or_duplicated_top():
    assert "no longer defines the top module top" in companions.unit_violation(CHILD, "top", [], Path("tb.v"))
    assert "more than once" in companions.unit_violation(CHILD + TOP + TOP, "top", [], Path("tb.v"))


def test_unit_gate_keeps_testbench_instantiated_modules_live_under_top():
    assert companions.unit_violation(CHILD + TOP, "top", ["child"], Path("tb.v")) == ""
    inlined = CHILD + "module top(input clk, input a, output reg y); always @(posedge clk) y <= a; endmodule\n"
    assert "no longer defines or instantiates child" in companions.unit_violation(inlined, "top", ["child"], Path("tb.v"))
    dead = CHILD + ("module top(input clk, input a, output reg y);\n    wire w;\n    child u(.clk(clk), .a(a), .y(w));\n"
                    "    always @(posedge clk) y <= a;\nendmodule\n")
    assert "dead, conditional or disconnected" in companions.unit_violation(dead, "top", ["child"], Path("tb.v"))
