"""Immutable evidence supplied to contract roles; model proposals cannot edit it."""
from __future__ import annotations
import hashlib
import json
import math
import re
from pathlib import Path
from .state import atomic_write_text


def file_evidence(path: Path, limit: int = 16000) -> dict:
    path = Path(path)
    data = path.read_bytes()
    content = data.decode("utf-8", errors="replace")
    return {"path": str(path.resolve()), "sha256": hashlib.sha256(data).hexdigest(),
            "text": content[:limit], "truncated": len(content) > limit}


_REQUIRED_TOOLS = ("xvlog", "xelab", "xsim", "vivado")


def _valid_tool_exit_record(record) -> bool:
    if not isinstance(record, dict):
        return False
    required = {"schema_version", "tool", "executable", "cwd", "pid", "status",
                "returncode", "driver_returncode", "elapsed_seconds", "output_log_path",
                "output_log_sha256"}
    if set(record) != required or type(record["schema_version"]) is not int or record["schema_version"] != 1:
        return False
    for name in ("executable", "cwd", "output_log_path"):
        if not isinstance(record[name], str) or not record[name]:
            return False
    if not isinstance(record["tool"], str) or not re.fullmatch(r"[a-z0-9_.-]+", record["tool"]):
        return False
    if record["status"] not in ("exited", "timed_out", "launch_failed", "cancelled"):
        return False
    if record["pid"] is not None and (type(record["pid"]) is not int or record["pid"] <= 0):
        return False
    for name in ("returncode", "driver_returncode"):
        if record[name] is not None and type(record[name]) is not int:
            return False
    elapsed = record["elapsed_seconds"]
    if type(elapsed) not in (int, float) or not math.isfinite(elapsed) or elapsed < 0:
        return False
    digest = record["output_log_sha256"]
    if digest is not None and (not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest)):
        return False
    if record["status"] == "launch_failed" and (record["returncode"] is not None or record["pid"] is not None
                                                  or record["driver_returncode"] not in (126, 127)):
        return False
    if record["status"] == "timed_out" and record["driver_returncode"] != 124:
        return False
    if record["status"] == "cancelled" and record["driver_returncode"] is not None:
        return False
    if record["status"] == "exited":
        if record["driver_returncode"] is None:
            return False
        if record["returncode"] is not None and record["returncode"] != record["driver_returncode"]:
            return False
    return True


def tool_exit_evidence(directory: Path) -> dict:
    """Expose actual process receipts; missing/malformed evidence stays unknown.

    No prior success is substituted for a later failure or malformed record.
    Full history remains in the hashed raw file; context includes at most 32.
    """
    path = Path(directory) / "tool_exit_records.log"
    result = {"path": str(path.resolve()), "sha256": None, "status": "missing",
              "schema_valid": False, "history_count": 0, "records": [], "truncated": False,
              "latest_by_tool": {}, "missing_required_tools": list(_REQUIRED_TOOLS)}
    if not path.is_file():
        return result
    data = path.read_bytes()
    result["sha256"] = hashlib.sha256(data).hexdigest()
    lines = data.splitlines()
    result["history_count"] = len(lines)
    result["truncated"] = len(lines) > 32
    try:
        records = [json.loads(line) for line in lines]
    except (ValueError, UnicodeError):
        result["status"] = "invalid"
        return result
    if not records or not all(_valid_tool_exit_record(item) for item in records):
        result["status"] = "invalid"
        return result
    latest_records = {item["tool"]: item for item in records if item["tool"] in _REQUIRED_TOOLS}
    latest = {}
    for name, item in latest_records.items():
        # Earlier invocations may legitimately overwrite the same log path.
        # Only the latest receipt per tool must match the retained current log.
        log_status = "missing_hash"
        if item["output_log_sha256"] is not None:
            output = Path(item["output_log_path"])
            if not output.is_file():
                log_status = "missing"
            else:
                try:
                    digest = hashlib.sha256(output.read_bytes()).hexdigest()
                    log_status = "verified" if digest == item["output_log_sha256"] else "mismatch"
                except OSError:
                    log_status = "unreadable"
        latest[name] = {"status": item["status"], "returncode": item["returncode"],
            "driver_returncode": item["driver_returncode"],
            "output_log_path": item["output_log_path"],
            "output_log_sha256": item["output_log_sha256"],
            "log_status": log_status, "log_verified": log_status == "verified",
            "successful": item["status"] == "exited" and item["returncode"] == 0
                          and item["driver_returncode"] == 0 and log_status == "verified"}
    result.update(status="recorded", schema_valid=True, records=records[-32:], latest_by_tool=latest,
                  missing_required_tools=[name for name in _REQUIRED_TOOLS if name not in latest])
    return result


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
        "tool_exit_evidence": tool_exit_evidence(directory),
        "metric_provenance": "Structured metrics are parsed from retained reports; routed "
                             "utilization/timing reports take precedence when present. "
                             "The manifest identifies complete files by hash. Header excerpts "
                             "are bounded previews, not complete reports or an independent metric source.",
    }


def run_evidence(cfg, baseline, sources, tb, directory, execution_context) -> dict:
    from .verilog_interface import infer_module
    directory = Path(directory)
    source_facts = [file_evidence(path) for path in sources]
    source_contract = infer_module(Path(sources[0]).read_text(), cfg.top_module)
    declared_latency = {
        "known": source_contract.latency_known,
        "cycles": source_contract.latency if source_contract.latency_known else None,
        "source_path": source_facts[0]["path"], "source_sha256": source_facts[0]["sha256"],
        "meaning": "A source annotation declares numeric latency only when present. "
                   "Unannotated numeric latency is UNKNOWN, not zero. Preserve the source's "
                   "exact observable cycles and registered behavior. Annotation presence or "
                   "absence alone is not independent proof of behavioral correctness; use the "
                   "fixed source contract and deterministic verification, without inventing a numeric requirement.",
    }
    return {
        "schema_version": 1,
        "authority": "Harness evidence is fixed. Proposed architectural goals cannot redefine it.",
        "top_module": cfg.top_module, "part": cfg.target_part,
        "objective": cfg.objective, "clock_period_ns": cfg.target_period_ns,
        "baseline_metrics": baseline.to_dict(),
        "sources": source_facts, "declared_latency": declared_latency,
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
        "declared_latency": evidence["declared_latency"],
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
        "latency checks when a numeric declaration is known, xvlog compilation, "
        "xelab elaboration and xsim -runall. Unannotated numeric latency is UNKNOWN, "
        "not zero; an annotation alone is not independent behavioral proof. "
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
