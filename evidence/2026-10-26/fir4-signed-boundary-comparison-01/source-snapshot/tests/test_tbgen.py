import pytest
from pathlib import Path
from autortl.spec import ModuleSpec, Port, ResetSpec
from autortl.golden import GoldenModel
from autortl.tbgen import gen_stimulus, generate_fixed_latency_tb, generate

GOLDEN_SRC = """
def init():
    return {}
def step(state, inputs):
    return state, {"y": (inputs.get("a", 0) + inputs.get("b", 0)) & 0x1FF}
"""


def adder_spec():
    return ModuleSpec(
        name="adder", behavior="registered adder",
        ports=[Port("clk", "input", 1), Port("rst", "input", 1),
               Port("a", "input", 8), Port("b", "input", 8),
               Port("y", "output", 9)],
        latency=1, reset=ResetSpec())


def test_stimulus_deterministic_with_corners():
    s1 = gen_stimulus(adder_spec(), n_random=10, seed=42)
    s2 = gen_stimulus(adder_spec(), n_random=10, seed=42)
    assert s1 == s2
    assert s1[0] == {"a": 0, "b": 0}
    assert s1[1] == {"a": 255, "b": 255}


def test_fixed_latency_tb_structure(tmp_path):
    g = tmp_path / "golden.py"
    g.write_text(GOLDEN_SRC)
    gm = GoldenModel(g)
    tb = generate(adder_spec(), gm, tmp_path, n_random=5)
    text = tb.read_text()
    assert "module adder_tb" in text
    assert "TEST PASSED" in text and "TEST FAILED" in text
    assert "adder dut" in text
    assert "!==" in text                     # 4-state compare
    # expected values actually computed by the golden model
    assert "exp_y" in text


def test_scoreboard_mode_selected(tmp_path):
    spec = adder_spec()
    spec.compare_mode = "scoreboard"
    spec.ports += [Port("in_valid", "input", 1, protocol="valid_ready"),
                   Port("in_ready", "output", 1, protocol="valid_ready"),
                   Port("out_valid", "output", 1, protocol="valid_ready"),
                   Port("out_ready", "input", 1, protocol="valid_ready")]
    g = tmp_path / "golden.py"
    g.write_text(GOLDEN_SRC)
    tb = generate(spec, GoldenModel(g), tmp_path, n_random=5)
    text = tb.read_text()
    assert "backpressure" in text or "backoff" in text


def test_pulse_mode_raises(tmp_path):
    spec = adder_spec()
    spec.compare_mode = "pulse"
    g = tmp_path / "golden.py"; g.write_text(GOLDEN_SRC)
    import pytest
    with pytest.raises(Exception):
        generate(spec, GoldenModel(g), tmp_path)


@pytest.mark.parametrize("known", [False, 0, 1, "true", "false", None])
@pytest.mark.parametrize("entry", ["stimulus", "fixed_tb", "generate"])
def test_direct_testbench_apis_reject_unknown_or_nonboolean_latency(tmp_path, known, entry):
    spec = adder_spec()
    spec.latency = 0
    spec.latency_known = known
    with pytest.raises(ValueError, match="requires latency_known to be True"):
        if entry == "stimulus":
            gen_stimulus(spec, n_random=0)
        elif entry == "fixed_tb":
            generate_fixed_latency_tb(spec, [{"a": 1, "b": 2}], [{"y": 3}])
        else:
            generate(spec, None, tmp_path, n_random=0)
