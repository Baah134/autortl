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
    reports = sorted({path for pattern in ("*utilization*.rpt", "*timing*.rpt", "power.rpt")
                      for path in directory.glob(pattern) if path.is_file()})
    headers = [file_evidence(path, 1800) for path in reports]
    verification_logs = []
    for name in ("xvlog.log", "xelab.log", "sim_log.txt", "vivado_synth_output.log"):
        path = directory / name
        if path.is_file():
            item = file_evidence(path, 1800)
            full = path.read_bytes().decode("utf-8", errors="replace")
            verification_logs.append({"path": item["path"], "sha256": item["sha256"],
                "head": full[:1800], "tail": full[-1800:] if len(full) > 1800 else "",
                "truncated": len(full) > 3600,
                "preview_policy": "At most 1800 characters each from the start and end; "
                                  "hash covers the complete original file. "
                                  "Excerpts do not independently establish successful tool exit."})
    return {
        "flow_and_constraints": [file_evidence(directory / name) for name in
                                 ("synth.tcl", "timing.xdc", "timing_io.tcl")
                                 if (directory / name).is_file()],
        "report_manifest": [{"path": item["path"], "sha256": item["sha256"]}
                            for item in headers],
        "report_headers": headers,
        "verification_logs": verification_logs,
        "metric_provenance": "Structured metrics are parsed from retained reports; routed "
                             "utilization/timing reports take precedence when present. "
                             "The manifest identifies complete files by hash. Header excerpts "
                             "are bounded previews, not complete reports or an independent metric source.",
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


def render_fixed_optimize_contract(evidence: dict) -> str:
    """Render the harness's immutable optimize obligations without model negotiation.

    Source and testbench hashes identify the exact behavioral authority; report
    hashes and actual constraints identify the measurement environment. This is
    deliberately a fixed policy, not a model-authored set of acceptance goals.
    """
    objectives = {
        "minimize_luts": ("lut_used", "strictly lower"),
        "minimize_ffs": ("ff_used", "strictly lower"),
        "maximize_freq": ("wns_ns", "strictly higher at the same clock period"),
        "minimize_power": ("dynamic_power_w", "strictly lower"),
    }
    field, direction = objectives[evidence["objective"]]
    identity = lambda item: {"path": item["path"], "sha256": item["sha256"]}
    fixed = {
        "top_module": evidence["top_module"], "part": evidence["part"],
        "clock_period_ns": evidence["clock_period_ns"],
        "sources": [identity(item) for item in evidence["sources"]],
        "testbench": identity(evidence["testbench"]),
        "testbench_top": evidence["testbench_top"],
        "baseline_metrics": evidence["baseline_metrics"],
        "execution_context": evidence["execution_context"],
        "flow_and_constraints": evidence["flow_and_constraints"],
        "report_manifest": evidence["report_manifest"],
    }
    return ("# Fixed optimization contract\n\n"
        "This contract is rendered by the harness from immutable run evidence. "
        "Planner, generator and evaluator cannot amend its requirements.\n\n"
        "## Behavioral obligations\n\n"
        "Preserve the frozen source's ports, names, directions, widths, parameters "
        "and parameter defaults. Preserve reset polarity, synchronous/asynchronous "
        "behavior, priority, state initialization and every observable cycle of "
        "latency, throughput, flags and handshakes, including disabled cycles. "
        "Preserve supported parameter behavior and high-bit semantics. No new "
        "pipeline stages, extra clock cycles, interfaces or invented thresholds. "
        "For build mode, the integrated design remains subject to its module specs.\n\n"
        "## Verification gates\n\n"
        "Use the frozen testbench unchanged. Pass static/interface and declared "
        "latency checks, xvlog compilation, xelab elaboration and xsim -runall. "
        "Tool stages require successful exit codes; synthesis also requires the "
        "SYNTH_COMPLETE marker. Simulation requires the exact standalone TEST PASSED verdict and rejects "
        "TEST FAILED, missing verdicts, tool errors and timeouts. Provided testbench "
        "coverage is not formal equivalence. Require valid retained routed reports "
        "and metric integrity; setup WNS >= 0 and hold WHS >= 0 are both mandatory "
        "for promotion. Missing or unknown evidence is not success.\n\n"
        "## Objective and completion\n\n"
        f"Objective {evidence['objective']} maps to {field}: require {direction} "
        "than the previous verified best, under the same device, clock and "
        "constraints. No minimum percentage gain or extra slack margin is imposed. "
        "Final evaluator ACCEPT with zero failed criteria and all deterministic "
        "promotion gates are required. DONE describes a completed experiment; "
        "best_iteration 0 retains the baseline and claims no accepted improvement. "
        "Only a promoted best_iteration > 0 establishes an accepted gain.\n\n"
        "## Fixed measurement authority\n\n"
        "The JSON below records source/testbench identities, actual device, clock, "
        "tool context, constraints and retained report hashes. Numeric metrics are "
        "the parsed structured evidence, with routed reports preferred. The "
        "candidate's retained synthesis script records actual permitted retiming "
        "or physical optimization settings; these never change behavioral obligations.\n\n"
        "```json\n" + json.dumps(fixed, sort_keys=True, indent=2, allow_nan=False)
        + "\n```\n")
