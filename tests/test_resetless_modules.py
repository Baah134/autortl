"""resetless_sequential_unrepresentable: typed support for modules without a reset port.

VerilogEval Prob147_circuit10 (clk, a, b -> q, state; no reset) could not be
typed: "reset": null crashed loading and tbgen demanded a reset port, so the
planner either gave up or invented an rst port. Text-level checks only.
"""
import hashlib
import json
from pathlib import Path

import pytest
import yaml

from autortl import prompts
from autortl.golden import GoldenModel, qualify_against_examples, validate_examples
from autortl.linter import lint_spec
from autortl.spec import DesignSpec, IOExample, ModuleSpec, Port, ResetSpec
from autortl.tbgen import (expected_outputs, gen_stimulus, generate, generate_fixed_latency_tb,
                           generate_scoreboard_tb, shape_errors)
from autortl.tbqual import qualification_mutations

ROOT = Path(__file__).resolve().parents[1]

# state <= a & b on every rising edge; q mirrors the register. One edge with
# a=b=0 defines state=0, whatever the power-up value.
AND_DFF_GOLDEN = """
def init():
    return {"s": 0}

def step(state, inputs):
    s = inputs.get("a", 0) & inputs.get("b", 0)
    return {"s": s}, {"q": s, "state": s}
"""

AND_DFF_RTL = """`timescale 1ns/1ps
// @latency 1
module and_dff (input wire clk, input wire a, input wire b, output reg q, output wire state);
always @(posedge clk) q <= a && b;
assign state = q;
endmodule
"""


def resetless_json(**module_overrides):
    module = {
        "name": "and_dff",
        "behavior": "On every rising edge state <= a & b; q equals state. No reset port: "
                    "one rising edge with a=0, b=0 defines state=0.",
        "ports": [{"name": "clk", "direction": "input", "width": 1},
                  {"name": "a", "direction": "input", "width": 1},
                  {"name": "b", "direction": "input", "width": 1},
                  {"name": "q", "direction": "output", "width": 1},
                  {"name": "state", "direction": "output", "width": 1}],
        "latency": 1, "compare_mode": "fixed_latency", "reset": None,
        "init_cycles": 1, "init_inputs": {"a": 0, "b": 0},
        "examples": [{"inputs": {"a": 1, "b": 1}, "expected": {"q": 1, "state": 1}, "after_cycles": 1},
                     {"inputs": {"a": 1, "b": 0}, "expected": {"q": 0, "state": 0}, "after_cycles": 2}],
    }
    module.update(module_overrides)
    return json.dumps({"top_name": "and_dff_top", "modules": [module],
                       "external_ports": [{"name": p["name"], "direction": p["direction"], "width": 1}
                                          for p in module["ports"]]})


def test_taxonomy_entry_precedes_benchmark_contract_entry():
    text = (ROOT / "data/taxonomy.yaml").read_text(encoding="utf-8")
    entries = list(yaml.safe_load(text)["harness_failures"])
    index = entries.index("resetless_sequential_unrepresentable")
    assert entries[index + 1] == "benchmark_artifact_contract_validation"
    assert "Prob147_circuit10" in text


def test_reset_null_loads_as_explicit_no_reset_and_lints_clean():
    spec = DesignSpec.from_json(resetless_json())
    module = spec.modules[0]
    assert module.reset == ResetSpec.none() and not module.reset.present
    assert ResetSpec().present
    assert lint_spec(spec) == []
    assert shape_errors(module) == []
    # Round trip keeps the null spelling and the init contract.
    again = DesignSpec.from_json(spec.to_json())
    assert json.loads(spec.to_json())["modules"][0]["reset"] is None
    assert again.modules[0] == module


def test_omitted_reset_keeps_legacy_default():
    raw = json.loads(resetless_json())
    del raw["modules"][0]["reset"]
    del raw["modules"][0]["init_cycles"]
    del raw["modules"][0]["init_inputs"]
    module = DesignSpec.from_json(json.dumps(raw)).modules[0]
    assert module.reset == ResetSpec()
    # Legacy strictness: a sequential module still needs its named reset port.
    assert any("requires clock and reset" in e for e in shape_errors(module))


def test_given_reset_must_still_name_a_valid_port_and_duration():
    for reset in ({"signal": "", "kind": "sync"}, {"signal": "rst", "duration_cycles": 0},
                  {"signal": "rst", "kind": "none"}, {"signal": "rst", "kind": "level"}):
        spec = DesignSpec.from_json(resetless_json(reset=reset, init_cycles=None, init_inputs={}))
        assert lint_spec(spec), reset
    # A sequential reset that names a missing port is still rejected by the
    # testbench shape check the build runs on every planner spec.
    module = DesignSpec.from_json(resetless_json(reset={"signal": "rst"}, init_cycles=None,
                                                 init_inputs={})).modules[0]
    assert any("requires clock and reset" in e for e in shape_errors(module))


def test_resetless_clocked_module_requires_init_cycles():
    for cycles in (None, 0, 65, True):
        spec = DesignSpec.from_json(resetless_json(init_cycles=cycles))
        errors = lint_spec(spec)
        assert any("must declare init_cycles" in e for e in errors), cycles
        assert shape_errors(spec.modules[0])
    # latency 0 with a clock still has state to define.
    spec = DesignSpec.from_json(resetless_json(latency=0, init_cycles=None, init_inputs={}))
    assert any("must declare init_cycles" in e for e in lint_spec(spec))


def test_init_fields_rejected_where_they_do_not_apply():
    with_reset = json.loads(resetless_json(reset={"signal": "rst"}))
    with_reset["modules"][0]["ports"].insert(1, {"name": "rst", "direction": "input", "width": 1})
    with_reset["external_ports"].insert(1, {"name": "rst", "direction": "input", "width": 1})
    errors = lint_spec(DesignSpec.from_json(json.dumps(with_reset)))
    assert any("apply only to a module without a reset port" in e for e in errors)
    bad_inputs = lint_spec(DesignSpec.from_json(resetless_json(init_inputs={"a": 2, "q": 0})))
    assert any("non-data-input ports ['q']" in e for e in bad_inputs)
    assert any("init_inputs a must be a masked port integer" in e for e in bad_inputs)


def test_resetless_scoreboard_rejected_explicitly():
    spec = DesignSpec.from_json(resetless_json(compare_mode="scoreboard"))
    assert any("scoreboard compare_mode requires a reset port" in e for e in lint_spec(spec))
    assert any("scoreboard compare_mode requires a reset port" in e for e in shape_errors(spec.modules[0]))


def test_generated_tb_has_no_reset_drive_and_inits_before_comparing(tmp_path):
    module = DesignSpec.from_json(resetless_json(init_cycles=3, init_inputs={"a": 0, "b": 1})).modules[0]
    golden = tmp_path / "golden.py"
    golden.write_text(AND_DFF_GOLDEN)
    text = generate(module, GoldenModel(golden), tmp_path, n_random=6).read_text()
    assert "rst" not in text and "reset =" not in text
    assert "and_dff dut (.clk(_autortl_clk), .a(a), .b(b), .q(q), .state(state));" in text
    init = text.index("// resetless init: 3 unchecked rising edge(s)")
    loop = text.index("for (_autortl_cycle=0;")
    assert init < text.index("a = 1'd0;", init) < text.index("b = 1'd1;", init) \
        < text.index("repeat (3) @(posedge _autortl_clk);") < loop
    assert text.index("!==") > loop                      # every comparison follows init
    data = json.loads((tmp_path / "stimulus.json").read_text())
    rows = data["stimulus"]
    assert data["expected"] == [{"q": r["a"] & r["b"], "state": r["a"] & r["b"]} for r in rows]
    assert "#{}".format((len(rows) + 0 + 3 + 20) * 10) in text   # watchdog covers init


def test_oracle_replays_init_prefix():
    module = DesignSpec.from_json(resetless_json(init_cycles=2, init_inputs={"a": 1, "b": 1})).modules[0]

    class Recorder:
        def run(self, rows):
            self.rows = rows
            return [{"q": 0, "state": 0} for _ in rows]
    recorder = Recorder()
    stimulus = gen_stimulus(module, n_random=2, seed=3)
    assert len(expected_outputs(module, recorder, stimulus)) == len(stimulus)
    assert recorder.rows[:2] == [{"a": 1, "b": 1}, {"a": 1, "b": 1}]
    assert recorder.rows[2:] == stimulus


def test_examples_validate_from_post_init_state(tmp_path):
    module = DesignSpec.from_json(resetless_json()).modules[0]
    golden = tmp_path / "golden.py"
    golden.write_text(AND_DFF_GOLDEN)
    assert validate_examples(module, require_anchors=True) == []
    assert qualify_against_examples(GoldenModel(golden), module) == []
    # An oracle whose state is only defined by the init prefix still matches the
    # examples, because examples start after initialization.
    toggly = tmp_path / "toggly.py"
    toggly.write_text(AND_DFF_GOLDEN.replace('return {"s": 0}', 'return {"s": 1}'))
    assert qualify_against_examples(GoldenModel(toggly), module) == []
    # A wrong oracle is still caught.
    wrong = tmp_path / "wrong.py"
    wrong.write_text(AND_DFF_GOLDEN.replace('inputs.get("a", 0) & inputs.get("b", 0)',
                                            'inputs.get("a", 0) | inputs.get("b", 0)'))
    assert any("example 1: expected q=0" in e for e in qualify_against_examples(GoldenModel(wrong), module))
    # The init prefix counts against the shared example budget.
    long = DesignSpec.from_json(resetless_json(init_cycles=64)).modules[0]
    long.examples = [IOExample({"a": 1, "b": 1}, {"q": 1, "state": 1}, 9990)]
    assert any("exceeds 10000 steps" in e for e in validate_examples(long))


def test_mutation_probes_remain_detectable_after_init(tmp_path):
    module = DesignSpec.from_json(resetless_json()).modules[0]
    golden = tmp_path / "golden.py"
    golden.write_text(AND_DFF_GOLDEN)
    generate(module, GoldenModel(golden), tmp_path, n_random=20)
    expected = json.loads((tmp_path / "stimulus.json").read_text())["expected"]
    labels = [label for label, _, _ in qualification_mutations(AND_DFF_RTL, "and_dff")]
    assert labels == ["mutant", "stuck_zero", "stuck_one"]
    # Compared rows contain both values, so stuck-at outputs always mismatch.
    assert {row["q"] for row in expected} == {0, 1}


def test_spec_prompt_documents_reset_null_and_forbids_invented_reset():
    text = prompts.SPEC_PROMPT
    assert "NEVER add a reset port" in text
    assert '"reset": null' in text and "init_cycles" in text and "init_inputs" in text
    prompts.SPEC_PROMPT.format(intent="x", target_part="p", target_freq_mhz=1, objective="o")
    assert "Reset none means there is no reset port" in prompts.GOLDEN_MODEL


class _Accumulator:
    def run(self, rows):
        out, acc = [], 0
        for row in rows:
            acc = (acc + row.get("a", 0) + row.get("b", 0)) & 0x1FF
            if row.get("rst", 0):
                acc = 0
            out.append({"y": acc})
        return out


def _legacy_specs():
    seq = ModuleSpec(name="adder", behavior="b", ports=[
        Port("clk", "input", 1), Port("rst", "input", 1), Port("a", "input", 8),
        Port("b", "input", 8), Port("y", "output", 9)], latency=1, reset=ResetSpec())
    comb = ModuleSpec(name="addc", behavior="b", ports=[
        Port("a", "input", 8), Port("b", "input", 8), Port("y", "output", 9)], latency=0)
    lat3 = ModuleSpec(name="adder3", behavior="b", ports=[
        Port("clk", "input", 1), Port("rst_n", "input", 1), Port("a", "input", 8),
        Port("b", "input", 8), Port("y", "output", 9)], latency=3,
        reset=ResetSpec(signal="rst_n", kind="async", active_high=False, duration_cycles=2))
    sb = ModuleSpec(name="sb", behavior="b", compare_mode="scoreboard", latency=2, ports=[
        Port("clk", "input", 1), Port("rst", "input", 1), Port("a", "input", 8),
        Port("b", "input", 8), Port("y", "output", 9),
        Port("in_valid", "input", 1, protocol="valid_ready"),
        Port("in_ready", "output", 1, protocol="valid_ready"),
        Port("out_valid", "output", 1, protocol="valid_ready"),
        Port("out_ready", "input", 1, protocol="valid_ready")])
    return [("seq", seq, generate_fixed_latency_tb), ("comb", comb, generate_fixed_latency_tb),
            ("lat3", lat3, generate_fixed_latency_tb), ("sb", sb, generate_scoreboard_tb)]


# Captured from base 2f06f2063 before this change: reset-based and legacy
# combinational testbench text and contract hashes must be byte-identical.
LEGACY_SNAPSHOTS = {
    "seq": ("6665d8256db9d0e5a59b4652d5e4beee60242f2b1f2272876dd88591a858c03b", "2a280873e265e0c0"),
    "comb": ("6d17c655e82aad38854c6883a5f2546c65234a6ec6fa2f401809d205007378ba", "123b1946e7140c8d"),
    "lat3": ("517762d7c95b546da3e128387d7f390311ba7324ccd6304c224f31276f6d5334", "0762e04ea75bf8c9"),
    "sb": ("5a297fc9aee20bbef801a91deaf963e1901ae73dbe5bace41ab924588fcfe056", "b38f659e5e6d0aa8"),
}


@pytest.mark.parametrize("name,spec,generator", _legacy_specs(), ids=[s[0] for s in _legacy_specs()])
def test_reset_based_testbenches_and_hashes_unchanged(name, spec, generator):
    stimulus = gen_stimulus(spec, n_random=7, seed=5)
    text = generator(spec, stimulus, expected_outputs(spec, _Accumulator(), stimulus))
    assert (hashlib.sha256(text.encode()).hexdigest(), spec.contract_hash()) == LEGACY_SNAPSHOTS[name]


def test_reset_based_spec_json_has_no_new_keys():
    module = _legacy_specs()[0][1]
    data = json.loads(DesignSpec("adder_top", [module]).to_json())["modules"][0]
    assert "init_cycles" not in data and "init_inputs" not in data
    assert data["reset"] == {"signal": "rst", "kind": "sync", "active_high": True, "duration_cycles": 5}
