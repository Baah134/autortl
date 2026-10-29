"""Frozen companions that a trusted testbench tests directly must stay in use
(taxonomy: stale_companion_masks_inlined_candidate)."""
import json
from unittest.mock import Mock

from autortl import candidate_context, companions, fsm
from autortl.bestofn import Candidate
from autortl.config import RunConfig
from autortl.triage import FailureKind

CORE = """module uart_tx_core #(parameter DIV = 868) (input wire clk, input wire rst, output reg tx);
    always @(posedge clk) tx <= rst;
endmodule
"""
# The mechanical top: instantiates the companion.
TOP = """module uart_tx (input wire clk, input wire rst, output wire tx);
    uart_tx_core u_core(.clk(clk), .rst(rst), .tx(tx));
endmodule
"""
# The real run-03 shape: the core's logic inlined into the top.
INLINED = """// a comment naming uart_tx_core u(); is not an instance
module uart_tx (input wire clk, input wire rst, output wire tx);
    reg tx_reg; assign tx = tx_reg;
    always @(posedge clk) tx_reg <= rst;   // "uart_tx_core x(" in a string-free comment
endmodule
"""
TB_NAMES_CORE = """module uart_tx_tb;
    reg clk = 0, rst = 1; wire tx_a, tx_b;
    uart_tx dut_a(.clk(clk), .rst(rst), .tx(tx_a));
    uart_tx_core #(.DIV(3)) dut_b(.clk(clk), .rst(rst), .tx(tx_b));
endmodule
"""
TB_TOP_ONLY = """module uart_tx_tb;
    reg clk = 0, rst = 1; wire tx;
    uart_tx dut(.clk(clk), .rst(rst), .tx(tx));
endmodule
"""


def files(tmp_path, tb_text):
    core = tmp_path / "uart_tx_core.v"
    core.write_text(CORE)
    tb = tmp_path / "uart_tx_tb.v"
    tb.write_text(tb_text)
    return [core], tb


def test_testbench_instantiation_is_found_only_for_companions(tmp_path):
    extra, tb = files(tmp_path, TB_NAMES_CORE)
    assert companions.required_by_testbench(tb, extra) == ["uart_tx_core"]
    extra, tb = files(tmp_path, TB_TOP_ONLY)
    assert companions.required_by_testbench(tb, extra) == []
    assert companions.required_by_testbench(None, extra) == []
    assert companions.required_by_testbench(tb, []) == []


def test_instantiation_ignores_comments_strings_and_declarations():
    names = {"uart_tx_core"}
    assert companions.instantiated(INLINED, names) == set()
    assert companions.instantiated(CORE, names) == set()            # its own declaration is not an instance
    assert companions.instantiated(TOP, names) == names
    assert companions.instantiated("x #(.A(1)) y(); uart_tx_core #(.DIV(4)) u(.clk(c));", names) == names
    assert companions.instantiated("uart_tx_core u_arr [3:0] (.clk(c));", names) == names
    assert companions.instantiated('initial $display("uart_tx_core u(");', names) == set()
    assert companions.instantiated("wire uart_tx_core_done; assign uart_tx_core_done = 1;", names) == set()


def test_reachability_through_helpers_and_companions(tmp_path):
    extra, tb = files(tmp_path, TB_NAMES_CORE)
    assert companions.unreachable(TOP, "uart_tx", extra, ["uart_tx_core"]) == []
    assert companions.unreachable(INLINED, "uart_tx", extra, ["uart_tx_core"]) == ["uart_tx_core"]
    # Reached through a helper the candidate defines itself.
    helper = """module uart_tx (input wire clk, input wire rst, output wire tx);
        wrap w(.clk(clk), .rst(rst), .tx(tx)); endmodule
    module wrap (input wire clk, input wire rst, output wire tx);
        uart_tx_core c(.clk(clk), .rst(rst), .tx(tx)); endmodule"""
    assert companions.unreachable(helper, "uart_tx", extra, ["uart_tx_core"]) == []
    # A helper that is defined but never instantiated does not count.
    orphan = INLINED + "\nmodule spare(); uart_tx_core c(); endmodule\n"
    assert companions.unreachable(orphan, "uart_tx", extra, ["uart_tx_core"]) == ["uart_tx_core"]


def test_violation_message_names_the_companion_and_the_fix(tmp_path):
    extra, tb = files(tmp_path, TB_NAMES_CORE)
    message = companions.violation(INLINED, "uart_tx", extra, tb)
    assert message.startswith("ERROR:") and "uart_tx_core" in message and "Keep instantiating uart_tx_core" in message
    assert companions.violation(TOP, "uart_tx", extra, tb) == ""
    extra, tb = files(tmp_path, TB_TOP_ONLY)
    assert companions.violation(INLINED, "uart_tx", extra, tb) == ""     # inlining is fine when nothing names the child


def setup(tmp_path, monkeypatch, tb_text, source, fixed):
    o = fsm.Orchestrator(RunConfig(mode="optimize", top_module="uart_tx", max_fix_attempts=1), tmp_path / "run")
    extra, tb = files(tmp_path, tb_text)
    candidate = Candidate(source, "standard")
    repair = Mock(return_value=fixed)
    monkeypatch.setattr(o.generator, "fix", repair)
    tools = []
    monkeypatch.setattr(o, "_tool", lambda name, *args, **kwargs: (tools.append(name), (True, "", FailureKind.DESIGN))[1])
    return o, candidate, o._infer_contract(TOP, "uart_tx"), extra, tb, repair, tools


def test_inlined_candidate_is_repaired_before_any_tool_runs(tmp_path, monkeypatch):
    o, c, contract, extra, tb, repair, tools = setup(tmp_path, monkeypatch, TB_NAMES_CORE, INLINED, TOP)
    errors = []
    o._verify_optimization_candidate(c, contract, tb, extra, o.state.iter_dir(1), errors)
    assert repair.call_count == 1 and "Keep instantiating uart_tx_core" in errors[0]
    assert "uart_tx_core" in repair.call_args.args[2]                    # the error reaches the generator
    assert c.alive and c.ladder_rungs_passed == 4 and c.verilog == TOP
    assert tools == ["xvlog_check", "xsim_run"]                          # only the repaired source was compiled


def test_inlined_candidate_fails_when_repair_keeps_inlining(tmp_path, monkeypatch):
    o, c, contract, extra, tb, repair, tools = setup(tmp_path, monkeypatch, TB_NAMES_CORE, INLINED, INLINED)
    o._verify_optimization_candidate(c, contract, tb, extra, o.state.iter_dir(1), [])
    assert not c.alive and "uart_tx_core" in c.fail_reason and c.ladder_rungs_passed == 1
    assert tools == []


def test_inlining_is_allowed_when_the_testbench_only_uses_the_top(tmp_path, monkeypatch):
    o, c, contract, extra, tb, repair, tools = setup(tmp_path, monkeypatch, TB_TOP_ONLY, INLINED, TOP)
    o._verify_optimization_candidate(c, contract, tb, extra, o.state.iter_dir(1), [])
    repair.assert_not_called()
    assert c.alive and c.ladder_rungs_passed == 4 and tools == ["xvlog_check", "xsim_run"]


def test_candidate_context_names_required_companions_only_when_needed(tmp_path):
    extra, tb = files(tmp_path, TB_NAMES_CORE)
    plain = candidate_context.candidate_scope("uart_tx", extra)
    assert "must_keep_instantiating" not in plain
    assert candidate_context.candidate_scope("uart_tx", extra, []) == plain   # unchanged prompts elsewhere
    scoped = candidate_context.candidate_scope("uart_tx", extra, ["uart_tx_core"])
    body = json.loads(scoped[scoped.index("{"):])
    assert body["must_keep_instantiating"]["modules"] == ["uart_tx_core"]


def test_taxonomy_records_the_failure_before_the_fix():
    import yaml
    from autortl.taxonomy import Taxonomy
    path = fsm.Path(fsm.__file__).resolve().parents[1] / "data" / "taxonomy.yaml"
    entries = yaml.safe_load(path.read_text(encoding="utf-8"))["harness_failures"]
    for key in ("stale_companion_masks_inlined_candidate", "checkpoint_replace_denied",
                "golden_budget_long_period_examples"):
        assert set(entries[key]) == {"meaning", "repair"}
    Taxonomy(path)                                   # the edited file still loads
