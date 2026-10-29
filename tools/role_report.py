"""Per-role report for AutoRTL runs: how each agent role performed.

Reads only the files a run already writes (events.jsonl, designs.jsonl,
run_summary.json, budget.json) and never the model responses themselves.
For each run it reports, per role method, the calls that completed, the
attempts that started but never completed (failed or interrupted), and
retries; then the iteration outcomes the deterministic gates and the
evaluator produced.

    python tools/role_report.py <run-or-campaign-dir> [...] [--json]

A campaign directory is any folder whose subfolders hold run_summary.json
(for example a bench output tier1_xxxx/ or an archived evidence run/ folder).
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys

REPAIR_METHODS = {"generator.fix": "generator repairs", "generator.golden_model": "golden-model attempts",
                  "planner.make_spec": "planner spec attempts"}


def _jsonl(path):
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
    return rows


def _json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def runs(paths):
    """Run folders under the given paths, in a stable order."""
    found = []
    for path in map(Path, paths):
        if (path / "run_summary.json").is_file() or (path / "events.jsonl").is_file():
            found.append(path)
        else:
            found.extend(sorted(p.parent for p in path.rglob("run_summary.json")))
    return list(dict.fromkeys(found))


def role_calls(events):
    """{role.method: {"completed", "unfinished", "retries"}} from stage events."""
    attempts = defaultdict(dict)
    for event in events:
        parts = str(event.get("stage", "")).split(":")
        if len(parts) < 3 or parts[1] != "model":
            continue
        key = (event["stage"], event.get("attempt", 1))
        attempts[parts[2]][key] = attempts[parts[2]].get(key) == "COMPLETE" or event.get("outcome") == "COMPLETE"
    calls = {}
    for method, seen in sorted(attempts.items()):
        calls[method] = {"completed": sum(seen.values()), "unfinished": sum(not ok for ok in seen.values()),
                         "retries": sum(attempt > 1 for _, attempt in seen)}
    return calls


def summarize(run):
    summary, budget = _json(run / "run_summary.json"), _json(run / "budget.json")
    designs = _jsonl(run / "designs.jsonl")
    calls = role_calls(_jsonl(run / "events.jsonl"))
    iterations = [{"iteration": d.get("iteration"), "verdict": d.get("recommendation"),
                   "sim_passed": d.get("sim_passed"), "lut": d.get("lut_used"), "ff": d.get("ff_used"),
                   "wns_ns": d.get("wns_ns"), "best": bool(d.get("is_best")),
                   "error": (d.get("sim_error") or d.get("synth_error") or "").splitlines()[0][:160]
                   if (d.get("sim_error") or d.get("synth_error")) else ""} for d in designs]
    verdicts = Counter(i["verdict"] for i in iterations if i["iteration"] not in (0, None))
    baseline = summary.get("baseline_metrics") or {}
    best = summary.get("best_metrics") or {}
    return {"run": run.name, "path": str(run), "status": summary.get("status", "unknown"),
            "errors": summary.get("errors") or ([summary["error"]] if summary.get("error") else []),
            "model_calls": budget.get("llm_calls"), "vivado_seconds": budget.get("vivado_seconds"),
            "baseline_lut": baseline.get("lut_used"), "best_lut": best.get("lut_used"),
            "best_iteration": summary.get("best_iteration"), "roles": calls,
            "repairs": {label: calls.get(method, {}).get("completed", 0)
                        for method, label in REPAIR_METHODS.items() if method in calls},
            "verdicts": dict(verdicts), "iterations": iterations}


def render(reports):
    lines = ["# Role report", "",
             "| Run | Status | Model calls | Baseline LUT | Best LUT | Evaluator verdicts | Repairs |",
             "|---|---|---:|---:|---:|---|---|"]
    for r in reports:
        verdicts = ", ".join(f"{k} {v}" for k, v in sorted(r["verdicts"].items())) or "—"
        repairs = ", ".join(f"{k} {v}" for k, v in r["repairs"].items() if v) or "—"
        lines.append(f"| {r['run']} | {r['status']} | {r['model_calls'] if r['model_calls'] is not None else '—'} | "
                     f"{r['baseline_lut'] if r['baseline_lut'] is not None else '—'} | "
                     f"{r['best_lut'] if r['best_lut'] is not None else '—'} | {verdicts} | {repairs} |")
    for r in reports:
        lines += ["", f"## {r['run']}: {r['status']}"]
        lines += [f"- error: {e}" for e in r["errors"]]
        lines += ["", "| Role method | Completed | Unfinished | Retries |", "|---|---:|---:|---:|"]
        lines += [f"| {m} | {c['completed']} | {c['unfinished']} | {c['retries']} |" for m, c in r["roles"].items()]
        if r["iterations"]:
            lines += ["", "| Iteration | Verdict | Sim | LUT | FF | WNS ns | Best | Error |",
                      "|---:|---|---|---:|---:|---:|---|---|"]
            lines += [f"| {i['iteration']} | {i['verdict']} | {i['sim_passed']} | {i['lut']} | {i['ff']} | "
                      f"{i['wns_ns']} | {'yes' if i['best'] else ''} | {i['error']} |" for i in r["iterations"]]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    found = runs(args.paths)
    if not found:
        print("no runs found", file=sys.stderr)
        return 1
    reports = [summarize(run) for run in found]
    # The report is UTF-8 (it uses em dashes), whatever the console's code page.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.stdout.write(json.dumps(reports, indent=2) + "\n" if args.json else render(reports))
    return 0


if __name__ == "__main__":
    sys.exit(main())
