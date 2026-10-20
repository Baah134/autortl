"""Regression for a real generated counter oracle requiring explicit reset keys."""
import copy
from unittest.mock import Mock
import pytest
from autortl.spec import ModuleSpec, Port, ResetSpec
from autortl.golden import GoldenModel
from autortl.tbgen import expected_outputs, generate
from autortl import roles

COUNTER = """
def init():
    return {"count": 99}
def step(state, inputs):
    if inputs["rst"] == 1:
        count = 0
    elif inputs["enable"]:
        count = (state["count"] + 1) & 255
    else:
        count = state["count"]
    return {"count": count}, {"count": count}
"""

def counter_spec():
    return ModuleSpec("counter", "registered counter", [Port("clk","input",1),
        Port("rst","input",1),Port("enable","input",1),Port("count","output",8)],latency=1)


def test_strict_reset_reference_receives_initialization_and_deassertion(tmp_path):
    path=tmp_path/"oracle.py";path.write_text(COUNTER,encoding="utf-8")
    stimulus=[{"enable":1},{"enable":0},{"enable":1}]
    original=copy.deepcopy(stimulus)
    assert expected_outputs(counter_spec(),GoldenModel(path),stimulus)==[{"count":1},{"count":1},{"count":2}]
    assert stimulus==original


@pytest.mark.parametrize("active_high,duration",[(True,1),(True,3),(False,2)])
def test_reset_rows_match_polarity_and_duration(active_high,duration):
    spec=counter_spec();spec.reset=ResetSpec(signal="rst",active_high=active_high,duration_cycles=duration)
    gm=Mock();gm.run.side_effect=lambda rows:[{"count":i} for i in range(len(rows))]
    assert expected_outputs(spec,gm,[{"enable":1}])==[{"count":duration}]
    assert gm.run.call_args.args[0]==[{"enable":0,"rst":int(active_high)}]*duration+[{"enable":1,"rst":1-int(active_high)}]


def test_combinational_reference_without_reset_gets_original_data_only():
    spec=ModuleSpec("comb","identity",[Port("a","input",8),Port("y","output",8)])
    gm=Mock();gm.run.return_value=[{"y":7}]
    assert expected_outputs(spec,gm,[{"a":7}])==[{"y":7}]
    gm.run.assert_called_once_with([{"a":7}])


def stream_spec():
    return ModuleSpec("elastic","identity transactions",[Port("clk","input",1),Port("rst","input",1),
        Port("data","input",8),Port("out_data","output",8),
        Port("in_valid","input",1,protocol="valid_ready"),Port("in_ready","output",1,protocol="valid_ready"),
        Port("out_valid","output",1,protocol="valid_ready"),Port("out_ready","input",1,protocol="valid_ready")],
        latency=1,compare_mode="scoreboard")


def test_scoreboard_oracle_gets_accepted_transactions_and_reset():
    spec=stream_spec();gm=Mock()
    gm.run.side_effect=lambda rows:[{"out_data":row["data"]} for row in rows]
    assert expected_outputs(spec,gm,[{"data":9},{"data":17}])==[{"out_data":9},{"out_data":17}]
    rows=gm.run.call_args.args[0]
    prefix=spec.reset.duration_cycles
    assert rows[:prefix]==[{"data":0,"rst":1,"in_valid":0,"out_ready":0}]*prefix
    assert rows[prefix:]==[{"data":9,"rst":0,"in_valid":1,"out_ready":1},{"data":17,"rst":0,"in_valid":1,"out_ready":1}]


def test_generated_counter_tb_uses_reset_initialized_expected_sequence(tmp_path):
    path=tmp_path/"oracle.py";path.write_text(COUNTER,encoding="utf-8")
    tb=generate(counter_spec(),GoldenModel(path),tmp_path,n_random=0)
    import json
    facts=json.loads((tmp_path/"stimulus.json").read_text())
    assert facts["expected"]==[{"count":0},{"count":1},{"count":2}]
    assert all(set(row)=={"enable"} for row in facts["stimulus"])
    assert "TEST PASSED" in tb.read_text()


@pytest.mark.parametrize("spec",[counter_spec(),stream_spec()])
def test_actual_golden_prompt_explains_temporal_and_control_protocol(monkeypatch,spec):
    ask=Mock(return_value="```python\ndef init(): return {}\ndef step(s,i): return s,{}\n```")
    monkeypatch.setattr(roles,"ask",ask)
    roles.Generator().golden_model(spec,None)
    prompt=ask.call_args.args[1]
    assert "Comparison mode: "+spec.compare_mode in prompt
    assert "The clock edge\nis implicit" in prompt
    assert "ONE ACCEPTED input transaction" in prompt
    assert "do\nnot add a separate pipeline-delay queue" in prompt
    assert "data outputs:" in prompt and "active_high 'rst'" in prompt


def test_reset_prefix_counts_toward_golden_execution_bound():
    gm=Mock()
    with pytest.raises(ValueError,match="including reset exceeds"):
        expected_outputs(counter_spec(),gm,[{"enable":0}]*10000)
    gm.run.assert_not_called()


def test_random_stimulus_budget_reserves_reset_steps_before_allocation():
    from autortl.tbgen import gen_stimulus
    spec = counter_spec()
    assert len(gen_stimulus(spec, n_random=9992)) + spec.reset.duration_cycles == 10000
    with pytest.raises(ValueError, match="including reset prefix"):
        gen_stimulus(spec, n_random=9993)


def test_retry_prompt_contains_bounded_actual_diagnostic(monkeypatch):
    ask = Mock(return_value="def init(): return {}")
    monkeypatch.setattr(roles, "ask", ask)
    roles.Generator().golden_model(counter_spec(), None, feedback="SyntaxError: " + "x" * 3000)
    prompt = ask.call_args.args[1]
    assert "previous Python reference failed validation" in prompt
    assert "SyntaxError: " + "x" * 1787 in prompt
    assert "x" * 1800 not in prompt
