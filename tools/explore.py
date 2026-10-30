"""Exploratory tier runs that never touch the curriculum history.

A bench (`run.py bench`) records a verdict in curriculum/results.jsonl, so two
benches cannot share a machine without one losing its verdict. Exploration
only needs each entry's run records (to triage the roles), so this runs every
entry of a tier directly through `run.py build` / `run.py optimize`, several
at a time, each in its own output folder:

    python tools/explore.py --tier 2 --name explore-tier2-01 --jobs 2 --model gpt-6-luna

Budgets match the tier gate for that tier (tools/tier0_gate.py TIER_BUDGETS,
with iterations from each entry's meta.yaml). Output: logs/<name>/<entry>/,
plus logs/<name>/explore.json summarizing every entry. Nothing here is a
curriculum verdict.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import tier0_gate  # noqa: E402

BUDGETS = {"best_of_n": 1, "model_calls": 30, "tool_minutes": 40, "wall_minutes": 60, "infra_retries": 1}


def entry_command(python, entry: Path, out: Path, model=None, vivado=None):
    meta = yaml.safe_load((entry / "meta.yaml").read_text(encoding="utf-8"))
    mode = meta.get("mode", "optimize")
    args = [python, "run.py", mode]
    if mode == "optimize":
        args += ["--design", str(entry / meta["design"]), "--tb", str(entry / meta["tb"]), "--top", meta["top"]]
    else:
        args += ["--spec", str(entry / meta["spec"])]
        if meta.get("tb"):
            args += ["--tb", str(entry / meta["tb"])]
        if meta.get("top"):
            args += ["--top", meta["top"]]
        if meta.get("generate_golden"):
            args += ["--generate-golden"]
    args += ["--iterations", str(meta.get("iterations", 5)), "--best-of-n", str(BUDGETS["best_of_n"]),
             "--objective", meta.get("objective", "minimize_luts"),
             "--max-llm-calls", str(BUDGETS["model_calls"]), "--max-vivado-minutes", str(BUDGETS["tool_minutes"]),
             "--max-wall-minutes", str(BUDGETS["wall_minutes"]), "--max-infra-retries", str(BUDGETS["infra_retries"]),
             "--target-part", "xc7a35tcpg236-1", "--target-freq-mhz", str(meta.get("target_freq_mhz", 100)),
             "--output-dir", str(out)]
    folder = tier0_gate.vivado_bin(vivado)
    for name in ("vivado", "xvlog", "xelab", "xsim"):
        args += ["--" + name, folder + name + ".bat"]
    if model:
        args += ["--model", model]
    return args


def run_entry(python, entry, out, model, vivado):
    tick = time.monotonic()
    with open(out.parent / f"{entry.name}.console.txt", "w", encoding="utf-8") as console:
        code = subprocess.call(entry_command(python, entry, out, model, vivado), cwd=ROOT,
                               stdout=console, stderr=subprocess.STDOUT)
    summary = {}
    try:
        summary = json.loads((out / "run_summary.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    result = {"entry": entry.name, "exit_code": code, "seconds": round(time.monotonic() - tick),
              "status": summary.get("status"), "failure_kind": summary.get("failure_kind")}
    print(json.dumps(result), flush=True)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tier", type=int, required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--entries", nargs="+")
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--model", default=None)
    parser.add_argument("--vivado-bin", default=None)
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args(argv)
    if args.jobs < 1:
        parser.error("--jobs must be at least 1")
    base = ROOT / "logs" / args.name
    if base.exists():
        raise SystemExit(f"{base} exists: an earlier exploration is never overwritten")
    entries = sorted(p for p in (ROOT / "curriculum" / f"tier{args.tier}").iterdir()
                     if (p / "meta.yaml").is_file() and (not args.entries or p.name in args.entries))
    if not entries:
        raise SystemExit("no entries")
    base.mkdir(parents=True)
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:  # each entry is its own process
        results = list(pool.map(lambda e: run_entry(args.python, e, base / e.name, args.model, args.vivado_bin),
                                entries))
    (base / "explore.json").write_text(json.dumps({"tier": args.tier, "model": args.model,
                                                    "results": results}, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
