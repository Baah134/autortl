"""Golden model framework — the Python oracle every module is graded against.

A golden model is a plain function:  step(state, inputs) -> (state, outputs)
It is qualified against the spec's IOExamples BEFORE it becomes the oracle,
so a wrong oracle is caught at spec time, not after it grades everything.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
from .spec import ModuleSpec


class GoldenModel:
    """Wraps a user/LLM-supplied python file exposing:
         init() -> state
         step(state, inputs: dict) -> (state, outputs: dict)
    """
    def __init__(self, path: Path):
        spec = importlib.util.spec_from_file_location("golden", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if not hasattr(mod, "init") or not hasattr(mod, "step"):
            raise ValueError(f"{path}: golden model must define init() and step()")
        self._mod = mod

    def run(self, stimulus: list[dict]) -> list[dict]:
        state = self._mod.init()
        outs = []
        for inp in stimulus:
            state, out = self._mod.step(state, inp)
            outs.append(out)
        return outs


def qualify_against_examples(gm: GoldenModel, spec: ModuleSpec) -> list[str]:
    """Run the spec's concrete IO examples through the golden model."""
    errs = []
    for i, ex in enumerate(spec.examples):
        stim = [dict(ex.inputs)] + [dict(ex.inputs)] * max(0, ex.after_cycles - 1)
        outs = gm.run(stim)
        final = outs[-1] if outs else {}
        for k, v in ex.expected.items():
            if final.get(k) != v:
                errs.append(f"example {i}: expected {k}={v}, golden model gave "
                            f"{final.get(k)}")
    return errs
