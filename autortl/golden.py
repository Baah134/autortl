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
