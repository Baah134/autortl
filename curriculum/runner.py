"""Measured curriculum runs and promotion of matching, consecutive cohorts."""
from __future__ import annotations
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
import re
from pathlib import Path
import tempfile
import yaml
from autortl.config import RunConfig
from autortl.fsm import Orchestrator
from autortl.metrics_gate import validate, MetricsGateError
from autortl.report_parser import VivadoMetrics
from autortl.state import CheckpointLockedError, atomic_write_text

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results.jsonl"
OVERRIDES = {"proposal_feedback", "vivado_bin", "xvlog_bin", "xelab_bin", "xsim_bin", "target_part",
             "target_freq_mhz", "objective", "max_iterations", "best_of_n",
             "max_llm_calls", "max_vivado_minutes", "max_wall_minutes", "max_infra_retries", "model"}
EXECUTOR = ProcessPoolExecutor  # for --jobs > 1; separate processes keep per-tool timing apart


def _run_entry(cfg, run_dir):
    """Run one entry; an exception becomes an "exception" summary, as before."""
    try:
        return Orchestrator(cfg, run_dir=run_dir).run()
    except CheckpointLockedError as exc:
        # Infrastructure: the run resumes from its last checkpoint (infra_outcomes_missing_failure_kind).
        return {"status": "infra_blocked", "failure_kind": "infra", "error": str(exc)[:500],
                "run_dir": str(run_dir)}
    except Exception as exc:
        return {"status": "exception", "error": type(exc).__name__ + ": " + str(exc)[:500],
                "run_dir": str(run_dir)}


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _runtime_identity(run_dir):
    """Read evidence frozen by Orchestrator, without guessing the CLI model."""
    path = run_dir / "runtime.json"
    try:
        runtime = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(runtime, dict) or runtime.get("schema_version") != 1:
            raise ValueError("unsupported runtime manifest")
        implementation = runtime.get("implementation")
        if (not isinstance(implementation, dict) or "autortl/fsm.py" not in implementation
                or any(not isinstance(name, str) or not isinstance(digest, str)
                       or re.fullmatch(r"[0-9a-f]{64}", digest) is None
                       for name, digest in implementation.items())):
            raise ValueError("missing or invalid frozen implementation hashes")
        if not isinstance(runtime.get("python"), str) or not runtime["python"].strip():
            raise ValueError("missing frozen Python identity")
        tools = runtime.get("tools")
        if not isinstance(tools, dict) or set(tools) != {"vivado_bin", "xvlog_bin", "xelab_bin", "xsim_bin"}:
            raise ValueError("missing frozen tool identity")
        for tool in tools.values():
            if not isinstance(tool, dict) or set(tool) != {"path", "sha256"}:
                raise ValueError("invalid frozen tool identity")
            if not isinstance(tool["path"], str) or not tool["path"]:
                raise ValueError("missing frozen tool path")
            if tool["sha256"] is None:
                raise ValueError("unavailable frozen tool hash")
            if not isinstance(tool["sha256"], str) or re.fullmatch(r"[0-9a-f]{64}", tool["sha256"]) is None:
                raise ValueError("invalid frozen tool hash")
        digest = hashlib.sha256(json.dumps(runtime, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        return {"status": "known", "sha256": digest, "manifest_sha256": _hash(path),
                "model_identity": None, "model_identity_status": "unobserved_cli_default"}
    except (OSError, ValueError, TypeError) as exc:
        return {"status": "unknown", "sha256": None, "reason": str(exc)[:300],
                "model_identity": None, "model_identity_status": "unobserved_cli_default"}


def _accepted(summary, criteria):
    if summary.get("status") != "done":
        return False, "run did not complete successfully"
    try:
        m = VivadoMetrics.from_dict(summary.get("best_metrics", {}))
        validate(m, synthesis_ran=True)
        if m.sim_passed is not True or m.sim_error or m.synth_error:
            return False, "mandatory simulation or synthesis evidence failed"
        if m.timing_met is not True or m.wns_ns < 0 or m.whs_ns < 0:
            return False, "timing closure failed"
        for limit, field in (("max_luts", "lut_used"), ("max_ffs", "ff_used")):
            if limit in criteria and getattr(m, field) > criteria[limit]:
                return False, limit + " exceeded"
    except (TypeError, ValueError, AttributeError, MetricsGateError) as exc:
        return False, "invalid metrics: " + str(exc)[:300]
    return True, "mandatory gates passed"


def _metadata(entry):
    meta = yaml.safe_load((entry / "meta.yaml").read_text(encoding="utf-8"))
    if not isinstance(meta, dict):
        raise ValueError(f"{entry.name}: metadata must be an object")
    mode = meta.get("mode", "optimize")
    required = ("design", "tb", "top") if mode == "optimize" else ("spec",)
    if mode not in ("build", "optimize") or any(not meta.get(key) for key in required):
        raise ValueError(f"{entry.name}: invalid mode or missing required metadata")
    if "generate_golden" in meta:
        if type(meta["generate_golden"]) is not bool:
            raise ValueError(f"{entry.name}: generate_golden must be boolean")
        if meta["generate_golden"] and mode != "build":
            raise ValueError(f"{entry.name}: generate_golden=True requires build mode")
    for name in ("design", "tb", "spec"):
        if name in meta:
            if not isinstance(meta[name], str):
                raise ValueError(f"{entry.name}: {name} must name a file")
            path = (entry / meta[name]).resolve()
            if not path.is_relative_to(entry.resolve()) or not path.is_file():
                raise ValueError(f"{entry.name}: {name} missing or outside entry directory")
    criteria = meta.get("pass_criteria", {})
    if not isinstance(criteria, dict) or set(criteria) - {"max_luts", "max_ffs", "timing_met"}:
        raise ValueError(f"{entry.name}: unsupported pass criteria")
    for name in ("max_luts", "max_ffs"):
        if name in criteria and (type(criteria[name]) is not int or criteria[name] < 0):
            raise ValueError(f"{entry.name}: invalid resource limit")
    if "timing_met" in criteria and criteria["timing_met"] is not True:
        raise ValueError(f"{entry.name}: mandatory timing gate cannot be disabled")
    return meta


class HistoryConflictError(RuntimeError):
    """Another bench changed the curriculum history during this campaign."""


def _history_bytes() -> bytes:
    return RESULTS.read_bytes() if RESULTS.exists() else b""


def _commit_history(expected: bytes, history, record) -> None:
    """Write history + record only if nobody changed the history meanwhile.

    Benches read the history when they start and rewrite it when they end, so
    two at once would drop one record (concurrent_bench_drops_history). A short
    exclusive lock covers the compare and the write; a conflict fails closed and
    leaves this campaign's record in its own summary.json.
    """
    lock = RESULTS.with_name(RESULTS.name + ".lock")
    try:
        os.close(os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    except FileExistsError as exc:
        raise HistoryConflictError(f"{lock} exists: another bench is writing the history "
                                   "(if no bench is running, a crashed one left it; delete it)") from exc
    try:
        if _history_bytes() != expected:
            raise HistoryConflictError("curriculum history changed during this campaign; "
                                       "run benches one at a time")
        atomic_write_text(RESULTS, "".join(json.dumps(r, default=str) + "\n" for r in history + [record]))
    finally:
        lock.unlink(missing_ok=True)


def _history():
    records = []
    if not RESULTS.exists():
        return records
    for number, line in enumerate(RESULTS.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            if not isinstance(record, dict) or type(record.get("tier")) is not int:
                raise ValueError("invalid tier")
            if not isinstance(record.get("cohort"), str) or not record["cohort"]:
                raise ValueError("missing cohort")
            if any(type(record.get(key)) is not bool for key in ("qualified", "held", "full_tier")):
                raise ValueError("invalid governance flags")
            if not isinstance(record.get("results"), list) or not record["results"]:
                raise ValueError("missing results")
            for result in record["results"]:
                if not isinstance(result, dict) or not isinstance(result.get("entry"), str) or type(result.get("ok")) is not bool:
                    raise ValueError("invalid entry result")
            if record["held"] and (not record["full_tier"] or not record["qualified"]):
                raise ValueError("invalid held claim")
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Malformed curriculum history at line {number}: {exc}") from exc
        records.append(record)
    return records


def _govern(history, tier, cohort, results, full, provenance_known=True):
    previous_runs = [r for r in history if r.get("tier") == tier]
    held_records = [r for r in previous_runs if full and r.get("full_tier") is True
                    and r.get("cohort") == cohort and r.get("held")]
    protected = {e["entry"] for r in held_records for e in r.get("results", []) if e.get("ok")}
    regressions = sorted(e["entry"] for e in results if not e["ok"] and e["entry"] in protected)
    qualified = provenance_known and bool(results) and sum(e["ok"] for e in results) / len(results) >= 0.8 and not regressions
    streak = 1 if qualified else 0
    if qualified:
        for previous in reversed(previous_runs):
            if (previous.get("cohort") != cohort or not previous.get("qualified")
                    or previous.get("full_tier") is not full):
                break
            streak += 1
    return {"qualified": qualified, "consecutive_qualifying_runs": streak,
            "held_before": bool(held_records), "held": full and streak >= 3,
            "held_regressions": regressions, "full_tier": full}


def run_tier(tier: int, **overrides) -> int:
    """Overrides are per-design budgets. Subsets cannot promote a full tier."""
    if type(tier) is not int or tier < 0:
        raise ValueError("tier must be a nonnegative integer")
    output_root = Path(overrides.pop("output_root", ROOT.parent / "logs" / "curriculum")).resolve()
    selection = overrides.pop("entries", None)
    jobs = overrides.pop("jobs", 1)
    if type(jobs) is not int or jobs < 1:
        raise ValueError("jobs must be a positive integer")
    unknown = set(overrides) - OVERRIDES
    if unknown:
        raise ValueError("Unsupported curriculum overrides: " + ", ".join(sorted(unknown)))
    tier_dir = ROOT / f"tier{tier}"
    all_entries = sorted(p for p in tier_dir.iterdir() if p.is_dir() and p.name != "__pycache__") if tier_dir.exists() else []
    if any(not (entry / "meta.yaml").is_file() for entry in all_entries):
        raise ValueError("Curriculum entry directory is missing meta.yaml")
    if selection is not None and (not isinstance(selection, list) or
                                  any(not isinstance(e, str) for e in selection) or
                                  len(selection) != len(set(selection))):
        raise ValueError("Entry selection must be a list of unique names")
    if selection is not None and (not selection or set(selection) - {p.name for p in all_entries}):
        raise ValueError("Unknown or empty curriculum entry selection")
    entries = [p for p in all_entries if selection is None or p.name in selection]
    if not entries:
        print(f"[bench] tier {tier}: no entries")
        return 1
    history_bytes = _history_bytes()
    history = _history()
    governance_sha256 = _hash(Path(__file__).resolve())
    records, cohort_inputs, prepared = [], [], []
    for entry in entries:
        meta = _metadata(entry)
        hashes = {str(p.relative_to(entry)): _hash(p) for p in sorted(entry.rglob("*"))
                  if p.is_file() and "__pycache__" not in p.parts}
        config = {"mode": meta.get("mode", "optimize"), "top_module": meta.get("top", ""),
                  "objective": meta.get("objective", "minimize_luts"),
                  "target_freq_mhz": meta.get("target_freq_mhz", 100.0),
                  "max_iterations": meta.get("iterations", 5),
                  "generate_golden": meta.get("generate_golden", False)}
        for key, field in (("design", "design_path"), ("tb", "testbench_path"), ("spec", "spec_path")):
            if meta.get(key):
                config[field] = (entry / meta[key]).resolve()
        config.update(overrides)
        cfg = RunConfig(**config)
        cfg.validate()
        snapshot = json.loads(json.dumps(asdict(cfg), default=str))
        cohort_config = {k: v for k, v in snapshot.items() if k not in
                         {"work_dir", "design_path", "testbench_path", "spec_path"}}
        cohort_inputs.append({"entry": entry.name, "sources": hashes, "config": cohort_config})
        prepared.append((entry, meta, hashes, cfg, snapshot))
    output_root.mkdir(parents=True, exist_ok=True)
    campaign = Path(tempfile.mkdtemp(prefix=f"tier{tier}_", dir=output_root))
    if jobs > 1:
        # Entries are independent runs (own run_dir, budget and journal), so they
        # can run as separate processes; records are still assembled in entry order.
        with EXECUTOR(max_workers=jobs) as pool:
            futures = {pool.submit(_run_entry, cfg, campaign / entry.name): entry.name
                       for entry, _, _, cfg, _ in prepared}
            summaries = {}
            for future in as_completed(futures):
                try:
                    summaries[futures[future]] = future.result()
                except BaseException as exc:  # a dead worker process still yields a record
                    summaries[futures[future]] = {"status": "exception", "error": type(exc).__name__ + ": " + str(exc)[:500]}
                print(f"[bench] {futures[future]}: finished ({len(summaries)}/{len(prepared)})", flush=True)
    for entry, meta, hashes, cfg, snapshot in prepared:
        run_dir = campaign / entry.name
        summary = summaries[entry.name] if jobs > 1 else _run_entry(cfg, run_dir)
        if summary.get("status") == "exception":
            ok, reason = False, summary["error"]
        else:
            try:
                ok, reason = _accepted(summary, meta.get("pass_criteria", {}))
            except Exception as exc:
                ok, reason = False, type(exc).__name__ + ": " + str(exc)[:500]
        # Build mode rewrites top_module inside the run, which a worker process keeps to
        # itself, so take it from the summary (parallel_build_winner_digest_lost).
        winner = run_dir / f"{summary.get('top_module') or cfg.top_module}_best.v"
        record = {"entry": entry.name, "ok": ok, "reason": reason,
                  "source_sha256": hashes, "config": snapshot, "summary": summary,
                  "runtime_identity": _runtime_identity(run_dir),
                  "evidence_dir": str(run_dir),
                  "winner_sha256": _hash(winner) if winner.is_file() else None}
        records.append(record)
        atomic_write_text(campaign / "entries.json", json.dumps(records, indent=2, default=str))
        print(f"[bench] {entry.name}: {'PASS' if ok else 'FAIL'} ({reason})", flush=True)
    frozen_identities = [r["runtime_identity"] for r in records]
    governance_unchanged = governance_sha256 == _hash(Path(__file__).resolve())
    known = (governance_unchanged and all(r["status"] == "known" for r in frozen_identities)
             and len({r["sha256"] for r in frozen_identities}) == 1)
    identity = {"schema_version": 1, "status": "known" if known else "unknown",
                "runtime_sha256": frozen_identities[0]["sha256"] if known else None,
                "governance_sha256": governance_sha256,
                "model_identity": None, "model_identity_status": "unobserved_cli_default"}
    requested = {cfg.model for _, _, _, cfg, _ in prepared}
    if len(requested) == 1 and None not in requested:
        # The model the run named for every role; the CLI does not report one back.
        identity.update(model_identity=requested.pop(), model_identity_status="requested")
        from llm import endpoints
        endpoint = endpoints.load().get(identity["model_identity"].partition(".")[0])
        if endpoint is not None:
            # A user endpoint is configuration outside the frozen source; its
            # definition is part of the cohort, so editing it starts a new one.
            identity["model_endpoint_sha256"] = endpoints.digest(endpoint)
    if not known:
        identity["reason"] = ("governance implementation changed during campaign" if not governance_unchanged
                              else "runtime provenance missing, invalid or inconsistent across entries")
    cohort_material = {"entries": cohort_inputs, "runtime_identity": identity}
    cohort = hashlib.sha256(json.dumps(cohort_material, sort_keys=True).encode()).hexdigest()
    governance = _govern(history, tier, cohort, records, selection is None, provenance_known=known)
    rec = {"ts": datetime.now(timezone.utc).isoformat(), "tier": tier, "cohort": cohort,
           "runtime_identity": identity,
           "passed": sum(r["ok"] for r in records), "total": len(records),
           "results": records, "evidence_dir": str(campaign), **governance}
    blocked = sorted(r["entry"] for r in records if r["summary"].get("failure_kind") == "infra"
                     or r["summary"].get("status") in ("infra_blocked", "model_blocked"))
    if blocked:
        # Infrastructure never enters the history (infra_blocked_entry_enters_history):
        # the campaign gets no verdict and its record stays in summary.json.
        rec["infra_blocked_entries"] = blocked
        atomic_write_text(campaign / "summary.json", json.dumps(rec, indent=2, default=str))
        print(f"[bench] tier {tier}: no verdict; infrastructure-blocked: {', '.join(blocked)}; "
              f"record kept in {campaign / 'summary.json'}")
        return 3
    atomic_write_text(campaign / "summary.json", json.dumps(rec, indent=2, default=str))
    try:
        _commit_history(history_bytes, history, rec)
    except HistoryConflictError as exc:
        # Infrastructure: nothing enters the history; the record stays in summary.json.
        print(f"[bench] history not updated: {exc}; record kept in {campaign / 'summary.json'}")
        return 3
    print(f"[bench] tier {tier}: {rec['passed']}/{rec['total']}; held={rec['held']}; streak={rec['consecutive_qualifying_runs']}")
    return 0 if rec["qualified"] else 1
