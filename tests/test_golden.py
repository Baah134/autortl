from autortl.spec import ModuleSpec, Port, IOExample
from autortl.golden import GoldenModel, qualify_against_examples

GOOD = """
def init():
    return {"acc": 0}
def step(state, inputs):
    state["acc"] = (state["acc"] + inputs.get("x", 0)) & 0xFF
    return state, {"y": state["acc"]}
"""

BAD = GOOD.replace("+ inputs", "- inputs")


def spec_with_examples():
    return ModuleSpec(
        name="acc", behavior="accumulator",
        ports=[Port("clk", "input", 1), Port("rst", "input", 1),
               Port("x", "input", 8), Port("y", "output", 8)],
        examples=[IOExample(inputs={"x": 5}, expected={"y": 10}, after_cycles=2)])


def test_good_golden_qualifies(tmp_path):
    p = tmp_path / "g.py"; p.write_text(GOOD)
    assert qualify_against_examples(GoldenModel(p), spec_with_examples()) == []


def test_bad_golden_caught(tmp_path):
    p = tmp_path / "g.py"; p.write_text(BAD)
    errs = qualify_against_examples(GoldenModel(p), spec_with_examples())
    assert errs and "expected y=10" in errs[0]


def test_missing_step_rejected(tmp_path):
    p = tmp_path / "g.py"; p.write_text("def init():\n    return {}")
    import pytest
    with pytest.raises(ValueError):
        GoldenModel(p)
