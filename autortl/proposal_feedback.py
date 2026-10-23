"""Bounded advisory proposal history; no acceptance or tool decisions live here."""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

from .cache import code_hash

_METRICS = ("sim_passed", "timing_met", "wns_ns", "whs_ns", "lut_used", "ff_used",
            "dsp_used", "bram_used", "dynamic_power_w", "total_power_w")
_IDENTITIES = ("input_source", "trial_source", "prior_flow_script", "trial_flow_script")
_HEADER = (
    "Previous proposal observations (advisory; frozen contracts and verification gates still apply).\n"
    "Standard candidate measurements and Doctor trials are separate. Exact source identity is distinct "
    "from normalized code identity. Same RTL with different physical settings can be valid; repetition "
    "is not prohibited. Use the actual prior outcome to propose a concrete next experiment.\n"
)


def _text(value, limit):
    return value[:limit] if isinstance(value, str) else ""


def _digest(value, length=64):
    return value if isinstance(value, str) and re.fullmatch(r"[0-9a-f]{%d}" % length, value) else None


def source_identity(text):
    """Exact SHA-256 of UTF-8 text; CRLF and LF remain different identities."""
    if not isinstance(text, str):
        raise TypeError("source text must be a string")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _metrics(values):
    if not isinstance(values, dict):
        return {}
    result = {}
    for key in _METRICS:
        value = values.get(key)
        if key in ("sim_passed", "timing_met"):
            if type(value) is bool:
                result[key] = value
        elif type(value) in (int, float) and abs(value) <= 1e100 and math.isfinite(value):
            result[key] = value
    return result


def _identity(value):
    if not isinstance(value, dict):
        return None
    digest = _digest(value.get("sha256"))
    if digest is None:
        return None
    path = value.get("path")
    if not isinstance(path, str) or not path:
        return None
    try:
        return {"path": str(Path(path).resolve()), "sha256": digest}
    except (OSError, ValueError):
        return None


def _file_identity(path):
    try:
        if path.is_file():
            return {"path": str(path.resolve()),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    except (OSError, ValueError):
        pass
    return None


def doctor_summary(feedback):
    """Project trial observations only; never retain RTL, reports or report text."""
    if not isinstance(feedback, dict):
        return None
    result = {"status": _text(feedback.get("status"), 32),
              "action": _text(feedback.get("action"), 64),
              "reason": _text(feedback.get("reason"), 600),
              "tools_ran": feedback.get("tools_ran") is True,
              "measured_metrics": _metrics(feedback.get("measured_metrics"))}
    result["adopted"] = result["status"] == "ADOPTED"
    for key in _IDENTITIES:
        identity = _identity(feedback.get(key))
        if identity is not None:
            result[key] = identity
    result["identity_count"] = sum(key in result for key in _IDENTITIES)
    digest = _digest(feedback.get("proposed_source_text_sha256"))
    if digest is not None:
        result["proposed_source_text_sha256"] = digest
    return result


def record_candidate(candidate, generated_source, instruction, iteration, *, cache_hit=False):
    """Snapshot standard-flow evidence BEFORE a Doctor can mutate the winner.

    A matching source file is identified uniquely; unrelated companion files
    cannot silently become the candidate source. Returned dictionaries share no
    mutable metric references with the candidate.
    """
    final_source = candidate.verilog
    rungs = getattr(candidate, "ladder_rungs_passed", 0)
    rungs = rungs if type(rungs) is int and 0 <= rungs <= 5 else 0
    reason = _text(getattr(candidate, "fail_reason", ""), 600)
    metrics = _metrics(getattr(candidate, "metrics", None))
    alive = getattr(candidate, "alive", False) is True
    if reason.lower().startswith("infra:") or alive and rungs < 5:
        status = "infra_blocked"
    elif not alive and reason.lower().startswith("duplicate of "):
        status = "duplicate_skipped"
    elif not alive:
        status = "design_rejected"
    elif rungs >= 5 and metrics:
        status = "measured"
    else:
        status = "infra_blocked"
    result = {
        "iteration": iteration,
        "mutation": _text(getattr(candidate, "mutation", ""), 64),
        "instruction": _text(instruction, 600),
        "generated_source_sha256": source_identity(generated_source),
        "final_source_sha256": source_identity(final_source),
        "generated_code_hash": code_hash(generated_source),
        "final_code_hash": code_hash(final_source),
        "rungs": rungs, "status": status, "reason": reason,
        "metrics": metrics if status == "measured" else {},
        "cache_hit": cache_hit is True,
    }
    directory = getattr(candidate, "artifact_dir", None)
    if directory is not None:
        directory = Path(directory)
        result["artifact_dir"] = str(directory.resolve())
        script = _file_identity(directory / "synth.tcl")
        if script is not None:
            result["flow_script"] = script
        try:
            matches = []
            for index, path in enumerate(directory.glob("*.v")):
                if index >= 64:
                    matches = []
                    break
                if path.read_text(encoding="utf-8") == final_source.replace("\r\n", "\n").replace("\r", "\n"):
                    matches.append(path)
            if len(matches) == 1:
                identity = _file_identity(matches[0])
                if identity is not None:
                    result["source"] = identity
        except (OSError, UnicodeError, ValueError):
            pass
    return result


def _render_candidate(candidate, seed_sha, seed_code):
    if not isinstance(candidate, dict):
        return None
    result = {"mutation": _text(candidate.get("mutation"), 64),
              "rungs": candidate.get("rungs") if type(candidate.get("rungs")) is int and 0 <= candidate["rungs"] <= 5 else None,
              "status": _text(candidate.get("status"), 32),
              "reason": _text(candidate.get("reason"), 400),
              "cache_hit": candidate.get("cache_hit") is True,
              "metrics": _metrics(candidate.get("metrics"))}
    for prefix in ("generated", "final"):
        digest = _digest(candidate.get(prefix + "_source_sha256"))
        normalized = _digest(candidate.get(prefix + "_code_hash"), 16)
        result[prefix + "_source_sha256"] = digest
        result[prefix + "_equals_current_seed"] = digest == seed_sha if digest is not None else None
        result[prefix + "_code_hash"] = normalized
        result[prefix + "_code_equals_current_seed"] = normalized == seed_code if normalized is not None else None
    for key in ("source", "flow_script"):
        identity = _identity(candidate.get(key))
        if identity is not None:
            result[key] = {**identity, "path": identity["path"][:320]}
    result["artifact_dir"] = _text(candidate.get("artifact_dir"), 320)
    return result


def _render_doctor(feedback):
    result = doctor_summary(feedback)
    if result is not None:
        for key in _IDENTITIES:
            if key in result:
                result[key]["path"] = result[key]["path"][:320]
    return result


def render_feedback(records, current_seed, before_iteration):
    """Render the most recent three prior iterations, at most twelve candidates.

    Future/current observations are excluded. Output is capped at 16000 chars;
    older candidate detail is dropped first, never sliced into misleading JSON.
    """
    if type(before_iteration) is not int:
        raise ValueError("before_iteration must be an integer")
    recent = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        iteration = record.get("iteration")
        if type(iteration) is int and 0 <= iteration < before_iteration:
            recent[iteration] = record
            if len(recent) > 3:
                del recent[min(recent)]
    if not recent:
        return ""
    seed_sha, seed_code = source_identity(current_seed), code_hash(current_seed)
    rows, remaining = [], 12
    for iteration in sorted(recent, reverse=True):
        record = recent[iteration]
        candidates = record.get("candidates")
        candidates = candidates[-remaining:] if isinstance(candidates, list) and remaining else []
        projected = [_render_candidate(candidate, seed_sha, seed_code) for candidate in candidates]
        projected = [candidate for candidate in projected if candidate is not None]
        remaining -= len(projected)
        selected = _digest(record.get("selected_source_sha256"))
        rows.append({"iteration": iteration, "instruction": _text(record.get("instruction"), 600),
                     "standard_candidates": projected, "doctor_trial": _render_doctor(record.get("doctor")),
                     "recommendation": _text(record.get("recommendation"), 32),
                     "is_best": record.get("is_best") is True,
                     "selected_source_sha256": selected,
                     "selected_equals_current_seed": selected == seed_sha if selected is not None else None})
    rows.reverse()
    while True:
        rendered = _HEADER + json.dumps({"current_seed_sha256": seed_sha, "iterations": rows},
                                       ensure_ascii=False, sort_keys=True, allow_nan=False)
        if len(rendered) <= 16000:
            return rendered
        populated = next((row for row in rows if row["standard_candidates"]), None)
        if populated is not None:
            populated["standard_candidates"].pop(0)
        else:
            rows.pop(0)
