"""Immutable evidence supplied to contract roles; model proposals cannot edit it."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from .state import atomic_write_text


def file_evidence(path: Path, limit: int = 16000) -> dict:
    path = Path(path)
    data = path.read_bytes()
    content = data.decode("utf-8", errors="replace")
    return {"path": str(path.resolve()), "sha256": hashlib.sha256(data).hexdigest(),
            "text": content[:limit], "truncated": len(content) > limit}


def flow_evidence(directory) -> dict:
    directory = Path(directory)
    return {
        "flow_and_constraints": [file_evidence(directory / name) for name in
                                 ("synth.tcl", "timing.xdc", "timing_io.tcl")
                                 if (directory / name).is_file()],
        "report_headers": [file_evidence(path, 1800) for path in
                           sorted(directory.glob("*utilization*.rpt"))],
    }


def run_evidence(cfg, baseline, sources, tb, directory, execution_context) -> dict:
    directory = Path(directory)
    return {
        "schema_version": 1,
        "authority": "Harness evidence is fixed. Proposed architectural goals cannot redefine it.",
        "top_module": cfg.top_module, "part": cfg.target_part,
        "objective": cfg.objective, "clock_period_ns": cfg.target_period_ns,
        "baseline_metrics": baseline.to_dict(),
        "sources": [file_evidence(path) for path in sources],
        "testbench": file_evidence(tb), "testbench_top": cfg.top_module + "_tb",
        "simulation": {"tools": ["xvlog", "xelab", "xsim -runall"],
                       "required_verdict": "TEST PASSED", "failure_verdict": "TEST FAILED",
                       "scope": "Provided testbench checks; not a formal equivalence proof."},
        "execution_context": execution_context,
        **flow_evidence(directory),
        "allowed_flow_variations": "The harness may enable retiming or physical optimization. "
                                   "The candidate's retained synthesis script is authoritative for its actual settings.",
        "hard_gates": [
            "Preserve ports, parameter defaults, reset behavior and observable cycle behavior.",
            "Use the fixed provided testbench, tools, device and constraints without modification.",
            "Static/interface checks, compile, simulation and real routed metric integrity must pass.",
            "Timing closure requires setup slack >= 0 and hold slack >= 0.",
            "Unknown or absent evidence cannot count as success.",
        ],
        "objective_policy": "Seek measured improvement against baseline; a completed experiment may find none. "
                            "Do not invent mandatory savings, slack margins, tool versions, timing corners, "
                            "new tests, thresholds, code-style quotas or external environment requirements.",
    }


def save_evidence(path: Path, evidence: dict) -> str:
    payload = json.dumps(evidence, sort_keys=True, indent=2, allow_nan=False)
    if path.exists():
        if path.read_text(encoding="utf-8") != payload:
            raise ValueError("Contract evidence changed since checkpoint: " + str(path))
    else:
        atomic_write_text(path, payload)
    return payload
