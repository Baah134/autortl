"""Instruction and sampling-contract regressions, not a model-success study.

save_live_controls(output) materializes RTL/TBs for a later real simulator
control: combinational0 passes, the same clocked RTL passes at1 and fails at0.
No simulator/model is invoked here; pure tests cannot establish prompt benefit.
"""
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from autortl import roles
from autortl.golden import GoldenModel
from autortl.spec import ModuleSpec, Port, ResetSpec
from autortl.tbgen import expected_outputs, generate_fixed_latency_tb, shape_errors


STIMULUS = [{"amount": n} for n in (0, 1, 7, 3)]
CLOCKED_ORACLE = '''def init():
    return {"total": 0}
def step(state, inputs):
    state["total"] = 0 if inputs.get("rst", 0) else (state["total"] + inputs.get("amount", 0)) & 255
    return state, {"total": state["total"]}
'''
COMB_ORACLE = '''def init():
    return {}
def step(state, inputs):
    return state, {"total": inputs.get("amount", 0)}
'''
CLOCKED_RTL = '''`timescale 1ns/1ps
module accumulated_cell(input clk, input rst, input [7:0] amount, output reg [7:0] total);
always @(posedge clk) begin
    if (rst) total <= 0;
    else total <= total + amount;
end
endmodule
'''
COMB_RTL = '''`timescale 1ns/1ps
module accumulated_cell(input clk, input rst, input [7:0] amount, output [7:0] total);
assign total = amount;
endmodule
'''


def cell(latency):
    return ModuleSpec("accumulated_cell", "A defined observable transition.",
                      [Port("clk", "input", 1), Port("rst", "input", 1),
                       Port("amount", "input", 8), Port("total", "output", 8)],
                      latency=latency, reset=ResetSpec())


def rendered_prompt(monkeypatch):
    # Assert the text reaches the actual planner call, including the repair path.
    request = Mock(return_value='{"top_name":"unused"}')
    monkeypatch.setattr(roles, "ask", request)
    cfg = SimpleNamespace(target_part="xc7a35tcpg236-1", target_freq_mhz=100,
                          objective="minimize_luts")
    roles.Planner().make_spec("Build a renamed clocked accumulator.", cfg, None,
                             feedback="Preserve the request's exact edge behavior.")
    assert request.call_count == 1
    assert request.call_args.args[0] == "planner"
    return " ".join(request.call_args.args[1].split())


def test_planner_receives_explicit_fixed_latency_sampling_semantics(monkeypatch):
    prompt = rendered_prompt(monkeypatch)
    assert "latency 0 is checked before the next rising edge" in prompt
    assert "latency 1 is checked just after that rising edge" in prompt
    assert "first-word-fall-through does not by itself determine this observation phase" in prompt
    assert "Do not infer latency from the mere presence of clk" in prompt
    assert "scoreboard latency is the minimum accepted-transfer age" in prompt


def test_planner_defines_invalid_data_without_inventing_output_masks(monkeypatch):
    prompt = rendered_prompt(monkeypatch)
    assert "fixed_latency compares every protocol none output on every sampled row" in prompt
    assert "Define deterministic empty/invalid data values in behavior and examples" in prompt
    assert "no per-cycle don't-care or output-mask field" in prompt


@pytest.mark.parametrize("latency", [0, 1])
def test_driver_observation_matches_existing_edge_contract(tmp_path, latency):
    oracle = tmp_path / "golden.py"
    oracle.write_text(CLOCKED_ORACLE, encoding="utf-8")
    spec = cell(latency)
    expected = expected_outputs(spec, GoldenModel(oracle), STIMULUS)
    assert expected == [{"total": n} for n in (0, 1, 8, 11)]
    tb = generate_fixed_latency_tb(spec, STIMULUS, expected)
    loop = tb[tb.index("for (_autortl_cycle=0;"):tb.index('if (_autortl_errors == 0)')]
    drive = loop.index("amount = _autortl_stim_amount[_autortl_cycle];")
    compare = loop.index("if (total !== _autortl_exp_total[_autortl_index])")
    if latency:
        assert drive < loop.index("@(posedge _autortl_clk);") < loop.index("#1;") < compare
    else:
        assert "@(posedge _autortl_clk);" not in loop
        assert drive < loop.index("#1;") < compare
    # Independent state trace explains the failed UART/FIFO child unit checks.
    # This is a Python schedule analysis, not RTL simulation or model evidence.
    pre_edge = [0, 0, 1, 8]
    post_edge = [0, 1, 8, 11]
    observed = post_edge if latency else pre_edge
    assert sum(actual != want["total"] for actual, want in zip(observed, expected)) == (0 if latency else 3)


def test_clock_bearing_combinational_zero_stays_supported(tmp_path):
    spec = cell(0)
    assert spec.validate() == [] and shape_errors(spec) == []
    source = tmp_path / "golden.py"
    source.write_text(COMB_ORACLE, encoding="utf-8")
    expected = expected_outputs(spec, GoldenModel(source), STIMULUS)
    assert expected == [{"total": n} for n in (0, 1, 7, 3)]
    text = generate_fixed_latency_tb(spec, STIMULUS, expected)
    assert "accumulated_cell dut" in text
    assert "amount = _autortl_stim_amount[_autortl_cycle];" in text


def save_live_controls(output):
    """Write independent control RTL/TBs; return explicit later-vendor metadata.

    All tool exits must be zero. A negative case requires actual `FAIL index=`
    assertions plus TEST FAILED; watchdog/no-verdict/tool failures do not count.
    The two clocked controls use byte-identical RTL, oracle and input rows.
    """
    output = Path(output).resolve()
    manifest = []
    for name, latency, clocked, passed in (("combinational0", 0, False, True),
                                           ("clocked1", 1, True, True),
                                           ("clocked0_mismatch", 0, True, False)):
        directory = output / name
        directory.mkdir(parents=True, exist_ok=True)
        rtl = directory / "accumulated_cell.v"
        oracle = directory / "golden.py"
        rtl.write_text(CLOCKED_RTL if clocked else COMB_RTL, encoding="utf-8")
        oracle.write_text(CLOCKED_ORACLE if clocked else COMB_ORACLE, encoding="utf-8")
        spec = cell(latency)
        expected = expected_outputs(spec, GoldenModel(oracle), STIMULUS)
        tb = directory / "accumulated_cell_tb.v"
        tb.write_text(generate_fixed_latency_tb(spec, STIMULUS, expected), encoding="utf-8")
        (directory / "stimulus.json").write_text(json.dumps({"stimulus": STIMULUS, "expected": expected}, indent=2))
        manifest.append({"name": name, "sources": [str(rtl)], "testbench": str(tb),
                         "top": "accumulated_cell_tb", "expected_pass": passed,
                         "required_zero_exits": ["xvlog", "xelab", "xsim"],
                         "required_assertions": [] if passed else ["FAIL index=1 signal=total",
                                                                    "FAIL index=2 signal=total",
                                                                    "FAIL index=3 signal=total"],
                         "watchdog_or_no_verdict_accepted": False})
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def test_materialized_controls_hold_source_oracle_and_stimulus_constant(tmp_path):
    rows = save_live_controls(tmp_path)
    assert [row["expected_pass"] for row in rows] == [True, True, False]
    assert all(Path(row["testbench"]).is_file() for row in rows)
    for filename in ("accumulated_cell.v", "golden.py", "stimulus.json"):
        assert (tmp_path / "clocked1" / filename).read_bytes() == (tmp_path / "clocked0_mismatch" / filename).read_bytes()
    assert rows[-1]["required_assertions"] and rows[-1]["required_zero_exits"]
