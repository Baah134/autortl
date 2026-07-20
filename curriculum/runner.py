"""Curriculum runner: `python run.py bench --tier N`.

Executes every entry in curriculum/tierN/, appends to results.jsonl.
A tier is HELD when 3 consecutive runs pass >= 80% of its entries.
Regressions on held tiers block harness changes.
"""
from __future__ import annotations
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results.jsonl"


def run_tier(tier: int) -> int:
    tier_dir = ROOT / f"tier{tier}"
    entries = sorted(d for d in tier_dir.iterdir() if d.is_dir()) \
        if tier_dir.exists() else []
    if not entries:
        print(f"[bench] tier {tier}: no entries")
        return 1
    sys.path.insert(0, str(ROOT.parent))
    from autortl.config import RunConfig
    from autortl.fsm import Orchestrator

    results = []
    for e in entries:
        meta = yaml.safe_load((e / "meta.yaml").read_text()) if yaml else {}
        mode = meta.get("mode", "optimize")
        print(f"\n[bench] {e.name} ({mode})")
        try:
            if mode == "optimize":
                cfg = RunConfig(mode="optimize",
                                top_module=meta["top"],
                                design_path=e / meta["design"],
                                testbench_path=(e / meta["tb"]) if meta.get("tb") else None,
                                objective=meta.get("objective", "minimize_luts"),
                                target_freq_mhz=meta.get("target_freq_mhz", 100.0),
                                max_iterations=meta.get("iterations", 5))
            else:
                cfg = RunConfig(mode="build", spec_path=e / meta["spec"],
                                objective=meta.get("objective", "minimize_luts"),
                                target_freq_mhz=meta.get("target_freq_mhz", 100.0),
                                max_iterations=meta.get("iterations", 5))
            summary = Orchestrator(cfg).run()
            ok = summary.get("status") == "done"
            crit = meta.get("pass_criteria", {})
            bm = summary.get("best_metrics", {})
            if ok and "max_luts" in crit:
                ok = bm.get("lut_used", 10**9) <= crit["max_luts"]
            if ok and crit.get("timing_met"):
                ok = bm.get("timing_met", False)
        except Exception as ex:
            ok, summary = False, {"error": str(ex)[:200]}
        results.append({"entry": e.name, "ok": ok})
        print(f"[bench] {e.name}: {'PASS' if ok else 'FAIL'}")

    passed = sum(r["ok"] for r in results)
    rec = {"ts": datetime.now().isoformat(), "tier": tier,
           "passed": passed, "total": len(results), "results": results}
    with open(RESULTS, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    frac = passed / len(results)
    print(f"\n[bench] tier {tier}: {passed}/{len(results)} "
          f"({'HELD threshold met' if frac >= 0.8 else 'below 80%'})")
    return 0 if frac >= 0.8 else 1
