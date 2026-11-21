"""Compare one arm across two separately registered, graded benchmark attempts.

    python -m benchmark.compare --a SUMMARY --a-arm ARM --a-label TEXT \\
                                --b SUMMARY --b-arm ARM --b-label TEXT --out REPORT.md

Each SUMMARY is a `grades/summary.json` written by `benchmark.report.grade_attempt`.
The chosen arm's rows of run A and run B are relabelled into two arms and passed
to `benchmark.report.summarize`, so rates, intervals and the paired difference
use exactly the statistics of the single-attempt report. Writes REPORT.md (never
overwritten) and REPORT.json beside it. Standard library only.

Statistics (same protocol as benchmark/report.py):
- Intervals are 95% task-clustered bootstrap (same samples and seed as report.py);
  a per-cell Wilson interval is shown only when the bootstrap cannot vary.
- The difference is B minus A, paired by task, over tasks with a verdict in both
  runs. The two runs must cover the same task set; otherwise the comparison is
  refused.
- Missing submissions count as failures; cells stopped by infrastructure (model
  quota or authentication block, interruption) are excluded from every rate and
  counted separately. Their cost is still charged.
- The runs were registered separately and may differ in model, backend and
  date: the comparison is descriptive of these two runs, not a controlled
  experiment on a single factor.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .report import (BOOTSTRAP_SAMPLES, INFRA_TERMINATIONS, ReportError, _ci, _pct, _task_rates,
                     summarize)

# summarize() knows a fixed arm vocabulary; run A plays the base arm, run B the compared one.
SLOT = {"a": "single_call", "b": "full"}


def _take(rows: list[dict], arm: str, slot: str, name: str) -> list[dict]:
    mine = [dict(r, arm=SLOT[slot]) for r in rows if r.get("arm") == arm]
    if not mine:
        arms = sorted({str(r.get("arm")) for r in rows})
        raise ReportError(f"run {name} has no rows for arm {arm!r} (arms present: {', '.join(arms) or 'none'})")
    for row in mine:
        row.setdefault("trial", 0)  # pilot summaries graded before trials were recorded
    return mine


def compare(rows_a: list[dict], arm_a: str, rows_b: list[dict], arm_b: str,
            label_a: str = "A", label_b: str = "B", samples: int = BOOTSTRAP_SAMPLES) -> dict:
    """Per-run rates with intervals and the paired difference B minus A, by task."""
    a = _take(rows_a, arm_a, "a", label_a)
    b = _take(rows_b, arm_b, "b", label_b)
    tasks_a, tasks_b = {r["task"] for r in a}, {r["task"] for r in b}
    if tasks_a != tasks_b:
        only_a, only_b = sorted(tasks_a - tasks_b), sorted(tasks_b - tasks_a)
        raise ReportError(f"runs cover different tasks: {len(only_a)} only in {label_a} "
                          f"{only_a[:3]}, {len(only_b)} only in {label_b} {only_b[:3]}")
    inner = summarize(a + b, samples=samples)
    rates = {slot: _task_rates([r for r in rows if r.get("termination") not in INFRA_TERMINATIONS], SLOT[slot])
             for slot, rows in (("a", a), ("b", b))}
    per_task = []
    for task in sorted(tasks_a):
        ra, rb = rates["a"].get(task), rates["b"].get(task)
        per_task.append({"task": task, "a": ra, "b": rb,
                         "difference": None if ra is None or rb is None else rb - ra})
    return {"tasks": len(tasks_a),
            "a": {"label": label_a, "arm": arm_a, **inner["arms"][SLOT["a"]]},
            "b": {"label": label_b, "arm": arm_b, **inner["arms"][SLOT["b"]]},
            "paired": inner["paired"][f"{SLOT['b']}-{SLOT['a']}"],
            "per_task": per_task, "bootstrap": inner["bootstrap"]}


# ---------------------------------------------------------------- rendering
def _cell_rate(value: float | None) -> str:
    return "excluded" if value is None else _pct(value)


def render_markdown(result: dict, title: str | None = None) -> str:
    """A self-contained Markdown report of a compare() result."""
    a, b, p = result["a"], result["b"], result["paired"]
    title = title or f"{b['label']} versus {a['label']}"
    lines = [f"# {title}", "",
             f"One arm from each of two separately graded attempts on the same {result['tasks']} tasks "
             f"({a['label']}: arm `{a['arm']}`; {b['label']}: arm `{b['arm']}`), paired by task. Intervals are "
             f"95% task-clustered bootstrap ({result['bootstrap']['samples']} resamples, seed "
             f"{result['bootstrap']['seed']}). Missing submissions count as failures; cells stopped by "
             "infrastructure (model quota, interruption) are not verdicts and are excluded from rates.", "",
             "## Functional correctness (official testbench, upstream-compatible verdict)", "",
             "| Run | Arm | Pass | Rate | 95% CI | Always / never pass (tasks) | Missing | "
             "Excluded (infrastructure) | Model calls | Calls per pass |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    degenerate = False
    for run in (a, b):
        interval = _ci(run["ci95_task_bootstrap"])
        if run["ci95_task_bootstrap"][0] == run["ci95_task_bootstrap"][1]:
            interval, degenerate = _ci(run["ci95_wilson_per_cell_reference"]) + " (Wilson*)", True
        per = "n/a" if run["calls_per_pass"] is None else f"{run['calls_per_pass']:.1f}"
        lines.append(f"| {run['label']} | {run['arm']} | {run['passes']}/{run['cells']} | {_pct(run['pass_rate'])} | "
                     f"{interval} | {run['tasks_always_pass']} / {run['tasks_never_pass']} | {run['missing']} | "
                     f"{run['not_evaluable']} | {run['llm_calls']} | {per} |")
    if degenerate:
        lines += ["", "*All tasks had the same rate, so the bootstrap cannot vary; the per-cell Wilson interval "
                  "is shown and is optimistic if trials of a task are correlated."]
    lines += ["", "## Paired difference (tasks with a verdict in both runs; percentage points)", "",
              "| Comparison | Tasks compared | Mean difference | 95% CI | Tasks better / equal / worse |",
              "|---|---|---|---|---|",
              f"| {b['label']} minus {a['label']} | {p['tasks_compared']} | {100 * p['mean_difference']:+.1f} | "
              f"{100 * p['ci95_task_bootstrap'][0]:+.1f} to {100 * p['ci95_task_bootstrap'][1]:+.1f} | "
              f"{p['tasks_better']} / {p['tasks_equal']} / {p['tasks_worse']} |",
              "", "An interval that includes 0 does not show a difference.", "",
              "## Tasks where the runs differ", ""]
    differing = [t for t in result["per_task"] if t["difference"] != 0]
    if differing:
        lines += [f"| Task | {a['label']} | {b['label']} | Difference (points) |", "|---|---|---|---|"]
        for t in differing:
            diff = "n/a" if t["difference"] is None else f"{100 * t['difference']:+.1f}"
            lines.append(f"| {t['task']} | {_cell_rate(t['a'])} | {_cell_rate(t['b'])} | {diff} |")
    else:
        lines.append("None: every task has the same pass rate in both runs.")
    lines += ["", "Limits: the two runs were registered and run separately and may use different models, "
              "backends and dates, so a difference is not attributable to a single factor; public tasks do "
              "not exclude training contamination; functional correctness only, no area or timing claim.", ""]
    return "\n".join(lines)


# ---------------------------------------------------------------------- CLI
def _load(path: Path) -> list[dict]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ReportError(f"{path} is not a list of graded rows")
    return rows


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m benchmark.compare")
    for slot in ("a", "b"):
        parser.add_argument(f"--{slot}", required=True, type=Path, help="graded summary.json")
        parser.add_argument(f"--{slot}-arm", required=True)
        parser.add_argument(f"--{slot}-label", required=True)
    parser.add_argument("--title")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    result = compare(_load(args.a), args.a_arm, _load(args.b), args.b_arm, args.a_label, args.b_label)
    with args.out.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(render_markdown(result, args.title))
    args.out.with_suffix(".json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    print(json.dumps({"report": str(args.out), "a": result["a"]["pass_rate"], "b": result["b"]["pass_rate"],
                      "difference": result["paired"]["mean_difference"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
