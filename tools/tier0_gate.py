"""Fresh full tier0 merge gate on the current harness source.

The same gate as Codex's campaign13/14 runners, rebuilt for a changed
harness. campaign14 could not launch after bc959cc and e062271 because it
asserts the old 230-file source freeze, and those commits changed the
harness on purpose. This runner:

1. Freezes the current runtime source identity, the same selection as
   validate_seed_binding_live.identities(): every .py/.v/.sv/.json/.yaml/.md
   under autortl, llm, tests, curriculum, scripts, data and .claude, plus
   run.py. tools/ is outside that set, so this file does not change it.
2. Runs the full pytest suite as the receipt, and requires exit 0 with the
   source unchanged before and after.
3. Runs `run.py bench --tier 0` with campaign14's exact budgets and
   arguments, and requires the source, router statistics and curriculum
   history prefixes to be unchanged afterwards.

    python tools/tier0_gate.py --name contract-campaign-15 [--python PY] [--tier 1]

--tier 1 runs the same discipline on curriculum tier 1 with TIER_BUDGETS[1].

Outputs go to logs/<name>* (ignored) and are archived under evidence/
afterwards. It refuses to overwrite an earlier attempt.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
SELECTION = ("autortl", "llm", "tests", "curriculum", "scripts", "data", ".claude")
SUFFIXES = (".py", ".v", ".sv", ".json", ".yaml", ".md")
VIVADO = "C:/AMDDesignTools/2025.2/Vivado/bin/"
BUDGETS = {"iterations": 1, "best_of_n": 1, "model_calls": 16, "tool_minutes": 20, "wall_minutes": 30,
           "infra_retries": 1}
# Per-tier budgets. Tier 0 keeps campaign14's exactly. Tier 1 leaves iterations
# to each entry's meta.yaml (None omits --iterations) and allows for build mode's
# planner, oracle and testbench calls.
TIER_BUDGETS = {0: BUDGETS,
                1: {"iterations": None, "best_of_n": 1, "model_calls": 30, "tool_minutes": 40, "wall_minutes": 60,
                    "infra_retries": 1}}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def identities(root=ROOT):
    """The runtime source identity (same selection as campaign13/14)."""
    result = {}
    for name in SELECTION:
        for path in (root / name).rglob("*"):
            if path.is_file() and path.suffix in SUFFIXES and "__pycache__" not in path.parts:
                result[path.relative_to(root).as_posix()] = sha(path)
    result["run.py"] = sha(root / "run.py")
    return dict(sorted(result.items()))


def bench_command(python, out, tier=0, model=None):
    budgets = TIER_BUDGETS[tier]
    args = [python, "run.py", "bench", "--tier", str(tier)]
    if budgets["iterations"] is not None:
        args += ["--iterations", str(budgets["iterations"])]
    args += ["--best-of-n", str(budgets["best_of_n"]), "--max-llm-calls", str(budgets["model_calls"]),
             "--max-vivado-minutes", str(budgets["tool_minutes"]), "--max-wall-minutes", str(budgets["wall_minutes"]),
             "--max-infra-retries", str(budgets["infra_retries"]), "--target-part", "xc7a35tcpg236-1",
             "--target-freq-mhz", "100", "--output-dir", str(out)]
    for name in ("vivado", "xvlog", "xelab", "xsim"):
        args += ["--" + name, VIVADO + name + ".bat"]
    if model:
        args += ["--model", model]
    return args


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--name", required=True)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--tier", type=int, choices=sorted(TIER_BUDGETS), default=0)
    parser.add_argument("--model", default=None,
                        help="model alias pinned for every role (recorded in the cohort); default: the CLI default")
    args = parser.parse_args(argv)
    logs = ROOT / "logs"
    run, freeze_path = logs / args.name, logs / f"{args.name}-source-freeze.json"
    tests_path, pre, launch = logs / f"{args.name}-tests.json", logs / f"{args.name}-prelaunch.json", \
        logs / f"{args.name}-launch-result.json"
    for path in (run, freeze_path, tests_path, pre, launch):
        if path.exists():
            raise SystemExit(f"{path} exists: an earlier attempt is never overwritten")
    sys.path.insert(0, str(ROOT))
    from curriculum.runner import _history
    if any(record["tier"] > args.tier and record["held"] for record in _history()):
        raise SystemExit("a higher held tier requires its own gate")

    source = identities()
    freeze_path.write_text(json.dumps(source, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"source_files": len(source), "freeze": str(freeze_path)}), flush=True)

    tick = time.monotonic()
    pytest = subprocess.run([args.python, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"], cwd=ROOT,
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
    receipt = {"exit_code": pytest.returncode, "seconds": time.monotonic() - tick,
               "summary": pytest.stdout.strip().splitlines()[-1] if pytest.stdout.strip() else "",
               "source_unchanged": identities() == source, "source_files": len(source),
               "source_freeze_sha256": sha(freeze_path)}
    tests_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt), flush=True)
    if receipt["exit_code"] != 0 or not receipt["source_unchanged"]:
        raise SystemExit("full test receipt failed; the bench gate was not launched")

    history_path, stats = ROOT / "curriculum/results.jsonl", ROOT / "llm/router_stats.jsonl"
    history_before = history_path.read_bytes() if history_path.exists() else b""
    stats_before = stats.read_bytes() if stats.exists() else b""
    command = bench_command(args.python, run, args.tier, args.model)
    budgets = TIER_BUDGETS[args.tier]
    plan = {"git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "runtime_source": source, "source_freeze_sha256": sha(freeze_path),
            "full_test_receipt_sha256": sha(tests_path), "command": command,
            "started_utc": datetime.now(timezone.utc).isoformat(), "python_version": sys.version,
            "python_executable_sha256": sha(Path(args.python)), "helper_sha256": sha(Path(__file__)),
            "router_stats_offset": len(stats_before), "router_stats_prefix_sha256": hashlib.sha256(stats_before).hexdigest(),
            "history_offset": len(history_before), "history_prefix_sha256": hashlib.sha256(history_before).hexdigest(),
            "tier": args.tier, "model": args.model, "budgets_per_entry": budgets, "no_higher_held_tier": True,
            "scope": (f"Fresh full tier0 runtime merge gate on {len(source)} source identities after harness changes; "
                      "campaign14's budgets and arguments. Ideal zero min/max I/O, no higher held tier.") if args.tier == 0
            else (f"Fresh full tier{args.tier} runtime gate on {len(source)} source identities; per-tier budgets, "
                  "iterations from each entry's meta.yaml. Ideal zero min/max I/O, no higher held tier.")}
    pre.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"prelaunch": str(pre), "budgets_per_entry": budgets}), flush=True)
    tick, code = time.monotonic(), None
    try:
        code = subprocess.call(command, cwd=ROOT)
    finally:
        result = {"exit_code": code, "wall_seconds": time.monotonic() - tick,
                  "source_unchanged": identities() == source,
                  "router_stats_prefix_unchanged": (stats.read_bytes() if stats.exists() else b"")[:len(stats_before)] == stats_before,
                  "history_prefix_unchanged": history_path.is_file()
                  and history_path.read_bytes()[:len(history_before)] == history_before,
                  "ended_utc": datetime.now(timezone.utc).isoformat()}
        launch.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result), flush=True)
    ok = result["source_unchanged"] and result["router_stats_prefix_unchanged"] and result["history_prefix_unchanged"]
    return code if ok and code is not None else (code or 1)


if __name__ == "__main__":
    sys.exit(main())
