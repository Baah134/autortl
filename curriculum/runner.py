"""Measured curriculum runs and promotion of matching, consecutive cohorts."""
from __future__ import annotations
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import yaml
from autortl.config import RunConfig
from autortl.fsm import Orchestrator
from autortl.metrics_gate import validate, MetricsGateError
from autortl.report_parser import VivadoMetrics
from autortl.state import atomic_write_text

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results.jsonl"
OVERRIDES = {"vivado_bin", "xvlog_bin", "xelab_bin", "xsim_bin", "target_part",
             "target_freq_mhz", "objective", "max_iterations", "best_of_n",
             "max_llm_calls", "max_vivado_minutes", "max_wall_minutes", "max_infra_retries"}


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def _govern(history, tier, cohort, results, full):
    previous_runs = [r for r in history if r.get("tier") == tier]
    held_records = [r for r in previous_runs if full and r.get("full_tier") is True
                    and r.get("cohort") == cohort and r.get("held")]
    protected = {e["entry"] for r in held_records for e in r.get("results", []) if e.get("ok")}
    regressions = sorted(e["entry"] for e in results if not e["ok"] and e["entry"] in protected)
    qualified = bool(results) and sum(e["ok"] for e in results) / len(results) >= 0.8 and not regressions
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
    history = _history()
    records, cohort_inputs, prepared = [], [], []
    for entry in entries:
        meta = _metadata(entry)
        hashes = {str(p.relative_to(entry)): _hash(p) for p in sorted(entry.rglob("*"))
                  if p.is_file() and "__pycache__" not in p.parts}
        config = {"mode": meta.get("mode", "optimize"), "top_module": meta.get("top", ""),
                  "objective": meta.get("objective", "minimize_luts"),
                  "target_freq_mhz": meta.get("target_freq_mhz", 100.0),
                  "max_iterations": meta.get("iterations", 5)}
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
    for entry, meta, hashes, cfg, snapshot in prepared:
        run_dir = campaign / entry.name
        try:
            summary = Orchestrator(cfg, run_dir=run_dir).run()
            ok, reason = _accepted(summary, meta.get("pass_criteria", {}))
        except Exception as exc:
            ok, reason = False, type(exc).__name__ + ": " + str(exc)[:500]
            summary = {"status": "exception", "error": reason, "run_dir": str(run_dir)}
        winner = run_dir / f"{cfg.top_module}_best.v"
        record = {"entry": entry.name, "ok": ok, "reason": reason,
                  "source_sha256": hashes, "config": snapshot, "summary": summary,
                  "evidence_dir": str(run_dir),
                  "winner_sha256": _hash(winner) if winner.is_file() else None}
        records.append(record)
        atomic_write_text(campaign / "entries.json", json.dumps(records, indent=2, default=str))
        print(f"[bench] {entry.name}: {'PASS' if ok else 'FAIL'} ({reason})", flush=True)
    cohort = hashlib.sha256(json.dumps(cohort_inputs, sort_keys=True).encode()).hexdigest()
    governance = _govern(history, tier, cohort, records, selection is None)
    rec = {"ts": datetime.now(timezone.utc).isoformat(), "tier": tier, "cohort": cohort,
           "passed": sum(r["ok"] for r in records), "total": len(records),
           "results": records, "evidence_dir": str(campaign), **governance}
    atomic_write_text(campaign / "summary.json", json.dumps(rec, indent=2, default=str))
    atomic_write_text(RESULTS, "".join(json.dumps(r, default=str) + "\n" for r in history + [rec]))
    print(f"[bench] tier {tier}: {rec['passed']}/{rec['total']}; held={rec['held']}; streak={rec['consecutive_qualifying_runs']}")
    return 0 if rec["qualified"] else 1
