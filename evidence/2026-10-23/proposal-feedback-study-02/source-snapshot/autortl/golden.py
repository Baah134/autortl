"""Golden model framework — the Python oracle every module is graded against.

A golden model is a plain function:  step(state, inputs) -> (state, outputs)
It is qualified against the spec's IOExamples BEFORE it becomes the oracle,
so a wrong oracle is caught at spec time, not after it grades everything.
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from .spec import ModuleSpec
from .golden_worker import validate_source


class GoldenModel:
    """Wraps a user/LLM-supplied python file exposing:
         init() -> state
         step(state, inputs: dict) -> (state, outputs: dict)
    """
    def __init__(self, path: Path, timeout_s: float = 5):
        self.source = Path(path).read_text(encoding="utf-8")
        self.work_parent = Path(path).resolve().parent
        validate_source(self.source)
        if timeout_s <= 0 or timeout_s > 30:
            raise ValueError("golden deadline must be in (0, 30] seconds")
        self.timeout_s = timeout_s

    def run(self, stimulus: list[dict]) -> list[dict]:
        if not isinstance(stimulus, list) or len(stimulus) > 10000 or not all(
            isinstance(row, dict) and all(isinstance(k, str) and type(v) is int
                                         for k, v in row.items()) for row in stimulus
        ):
            raise ValueError("golden stimulus must be bounded integer dictionaries")
        request = json.dumps({"source": self.source, "stimulus": stimulus})
        if len(request) > 1000000:
            raise ValueError("golden request exceeds size limit")
        worker = Path(__file__).with_name("golden_worker.py").resolve()
        # Do not forward PATH, HOME, provider tokens, PYTHONPATH, or other secrets.
        environment = {k: os.environ[k] for k in ("SYSTEMROOT", "WINDIR") if k in os.environ}
        with tempfile.TemporaryDirectory(prefix="autortl-golden-", dir=self.work_parent) as directory:
            environment.update(TEMP=directory, TMP=directory)
            try:
                result = subprocess.run([sys.executable, "-I", "-S", str(worker)],
                                        input=request, text=True, encoding="utf-8",
                                        errors="replace", capture_output=True,
                                        timeout=self.timeout_s, cwd=directory,
                                        env=environment, shell=False)
            except subprocess.TimeoutExpired as exc:
                raise ValueError("golden execution timed out") from exc
        try:
            response = json.loads(result.stdout)
        except (ValueError, TypeError) as exc:
            raise ValueError("golden worker returned invalid output") from exc
        if result.returncode != 0 or "outputs" not in response:
            raise ValueError(response.get("error", "golden worker failed"))
        outputs = response["outputs"]
        if len(outputs) != len(stimulus):
            raise ValueError("golden output count differs from stimulus")
        return outputs


def validate_examples(spec: ModuleSpec, *, require_anchors=False) -> list[str]:
    """Validate before allocating repeated stimulus or launching any oracle worker."""
    errors = []
    examples = spec.examples
    if not isinstance(examples, list) or len(examples) > 100:
        return ["examples must be a list with at most 100 entries"]
    if require_anchors and not examples:
        return ["generated oracle requires at least one concrete specification example"]
    inputs = {p.name:p for p in spec.ports if p.direction == "input" and p.name != "clk"}
    outputs = {p.name:p for p in spec.ports if p.direction == "output" and p.protocol == "none"}
    steps = 0
    for index, example in enumerate(examples):
        label = f"example {index}"
        cycles = getattr(example, "after_cycles", None)
        if type(cycles) is not int or not 1 <= cycles <= 10000:
            errors.append(label + ": after_cycles must be an integer in 1..10000")
        else:
            steps += cycles
        given, expected = getattr(example, "inputs", None), getattr(example, "expected", None)
        if not isinstance(given, dict) or not set(given).issubset(inputs):
            errors.append(label + ": inputs must contain only declared non-clock input ports")
        if not isinstance(expected, dict) or not expected or set(expected) != set(outputs):
            errors.append(label + ": expected must cover exactly all data output ports and be nonempty")
        for mapping, ports, kind in ((given,inputs,"input"),(expected,outputs,"expected")):
            if isinstance(mapping, dict):
                for name, value in mapping.items():
                    if name in ports and (type(value) is not int or not 0 <= value < (1 << ports[name].width)):
                        errors.append(f"{label}: {kind} {name} must be a masked port integer")
    if steps > 10000:
        errors.append("combined example execution exceeds 10000 steps")
    return errors


def qualify_against_examples(gm: GoldenModel, spec: ModuleSpec) -> list[str]:
    """Run the spec's concrete IO examples through the golden model."""
    errs = validate_examples(spec)
    if errs:
        return errs
    for i, ex in enumerate(spec.examples):
        stim = [dict(ex.inputs)] + [dict(ex.inputs)] * max(0, ex.after_cycles - 1)
        outs = gm.run(stim)
        final = outs[-1] if outs else {}
        for k, v in ex.expected.items():
            if final.get(k) != v:
                errs.append(f"example {i}: expected {k}={v}, golden model gave "
                            f"{final.get(k)}")
    return errs
