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



def test_invalid_examples_are_rejected_before_any_oracle_call():
    from unittest.mock import Mock
    from autortl.golden import validate_examples
    for cycles in (0,-1,True,10001,10**12,"1"):
        spec=spec_with_examples(); spec.examples[0].after_cycles=cycles
        gm=Mock()
        assert validate_examples(spec)
        assert qualify_against_examples(gm,spec)
        gm.run.assert_not_called()


def test_generated_oracle_requires_nonempty_complete_bounded_anchors():
    from autortl.golden import validate_examples
    spec=spec_with_examples(); spec.examples=[]
    assert validate_examples(spec,require_anchors=True)
    assert validate_examples(spec)==[]
    for example in (IOExample({"x":1},{}),IOExample({"x":1},{"bad":2}),
                    IOExample({"unknown":1},{"y":2}),IOExample({"x":-1},{"y":2}),
                    IOExample({"x":1},{"y":256})):
        spec.examples=[example]
        assert validate_examples(spec,require_anchors=True)
    spec.examples=[IOExample({"x":1},{"y":2},after_cycles=6000)]*2
    assert any('combined' in error for error in validate_examples(spec))
