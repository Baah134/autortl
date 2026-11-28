"""Grade a sealed benchmark attempt and report it with uncertainty.

    python -m benchmark.report grade  --manifest M.json --dataset D --attempt DIR [--iverilog P --vvp P]
    python -m benchmark.report render --summary DIR/grades/summary.json --catalog C.json --out REPORT.md

`grade` refuses to start until every registered cell is sealed (run.json), so no
verdict can leak into a run that is still generating. `render` is pure: it
turns graded rows into per-arm rates, intervals, paired differences, false
acceptance and cost. Standard library only.

Statistics (protocol: evidence/2026-11-06/parallel-diagnoses-01):
- The unit of independence is the task, not the cell: trials of one task are
  correlated, so intervals come from a task-clustered bootstrap (deterministic
  seed). A per-cell Wilson interval is shown only as a labelled reference.
- Arm differences are paired by task (same tasks in every arm).
- The primary endpoint is the upstream-compatible verdict (`upstream_pass`);
  the strict exit-based status and their disagreements are reported beside it.
- A missing submission counts as a failure in pass rates (intention to treat),
  except cells stopped by infrastructure (model quota or authentication block,
  interruption): those are not verdicts, are excluded from every rate and are
  counted separately. Their cost is still charged.
- False acceptance: internally accepted but externally failing, over all
  internally accepted submissions of that arm.

Opt-in arm full_xcheck (V1, docs/V1_REGISTRATION_DRAFT.md): the full harness with
the request cross-check. Only when its rows are present does the summary add the
paired comparison full_xcheck-full, a paired false-acceptance difference (per
evaluable cell) and the cross-check outcome counts; a run without it is
summarized and rendered exactly as before.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path
from autortl.fileio import read_json

ARMS = ("single_call", "ablation", "full", "full_xcheck")
ARM_LABEL = {"single_call": "A single call", "ablation": "B ablation", "full": "C full harness",
             "full_xcheck": "C-xcheck full harness + request cross-check"}
# Paired comparisons (better, base), in report order; each appears only when both arms do.
PAIRS = (("full", "single_call"), ("full", "ablation"), ("ablation", "single_call"), ("full_xcheck", "full"))
BOOTSTRAP_SAMPLES = 10_000
BOOTSTRAP_SEED = 20261115
# Infrastructure never counts as a design verdict (AGENTS.md hard rule 4): cells that
# ended on a model quota/auth block or an interruption are excluded from rates.
INFRA_TERMINATIONS = ("model_blocked", "interrupted")
ROW_KEYS = ("task", "arm", "trial", "termination", "internal", "status", "upstream_code",
            "upstream_pass", "mismatches", "samples", "run_status", "llm_calls", "input_tokens",
            "output_tokens", "seconds", "tool_seconds")
# full_xcheck rows only: the run summary's spec_cross_check policy and the outcome of
# each recorded check in revision order (autortl/fsm.py _record_cross_check); None
# when the run wrote no such record (no run summary, or a stop before planning).
XCHECK_ROW_KEYS = ("cross_check_policy", "cross_check_outcomes")


class ReportError(ValueError):
    """The attempt or its graded rows are incomplete or inconsistent."""


# ------------------------------------------------------------------ grading
def grade_attempt(manifest: dict, dataset: Path, attempt: Path, **tools) -> list[dict]:
    """Grade every registered cell of a fully sealed attempt; write grades/summary.json."""
    from . import pilot
    from . import verilogeval as ve

    attempt = Path(attempt)
    cells = [(c["task"], c["arm"], c["trial"]) for c in manifest["cells"]]
    runs = {cell: attempt / "runs" / f"{cell[0]}-{cell[1]}-{cell[2]}" for cell in cells}
    unsealed = [f"{t}-{a}-{n}" for (t, a, n), d in runs.items() if not (d / "run.json").is_file()]
    if unsealed:
        raise ReportError(f"{len(unsealed)} of {len(cells)} cells are not sealed; first: {unsealed[0]}")
    grades = attempt / "grades"
    grades.mkdir(exist_ok=False)
    rows = []
    for (task_id, arm, trial), run_dir in runs.items():
        record = read_json((run_dir / "run.json"))
        verdict = pilot.grade_run(manifest, ve.load_task(dataset, task_id), run_dir,
                                  grades / f"{task_id}-{arm}-{trial}", **tools)
        accounting = record["accounting"]
        tokens = accounting.get("tokens") or {}
        rows.append({"task": task_id, "arm": arm, "trial": trial, "termination": record["termination"],
                     "internal": verdict.get("internal_status"), "status": verdict["status"],
                     "upstream_code": verdict.get("upstream_code"),
                     "upstream_pass": bool(verdict.get("upstream_pass", False)),
                     "mismatches": verdict.get("mismatches"), "samples": verdict.get("samples"),
                     "run_status": accounting.get("run_status"), "llm_calls": accounting.get("llm_calls"),
                     "input_tokens": tokens.get("input_tokens"), "output_tokens": tokens.get("output_tokens"),
                     "seconds": accounting.get("seconds"), "tool_seconds": accounting.get("tool_seconds")})
        if arm == "full_xcheck":
            rows[-1].update(cross_check_fields(accounting.get("spec_cross_check")))
    (grades / "summary.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    return rows


def cross_check_fields(recorded) -> dict:
    """Row fields from a run summary's spec_cross_check {"policy", "checks"} (or None)."""
    if not isinstance(recorded, dict):
        return {"cross_check_policy": None, "cross_check_outcomes": None}
    checks = recorded.get("checks")
    return {"cross_check_policy": recorded.get("policy"),
            "cross_check_outcomes": None if not isinstance(checks, list)
            else [c.get("outcome") for c in checks if isinstance(c, dict)]}


# --------------------------------------------------------------- statistics
def wilson(successes: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion; (0, 1) when n is 0."""
    if n <= 0:
        return (0.0, 1.0)
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def _percentile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        raise ReportError("no bootstrap values")
    position = q * (len(sorted_values) - 1)
    low, high = math.floor(position), math.ceil(position)
    return sorted_values[low] + (sorted_values[high] - sorted_values[low]) * (position - low)


def cluster_bootstrap(per_task: dict[str, float], samples: int = BOOTSTRAP_SAMPLES,
                      seed: int = BOOTSTRAP_SEED) -> tuple[float, float]:
    """95% percentile interval for the mean of per-task values, resampling tasks."""
    tasks = sorted(per_task)
    if not tasks:
        raise ReportError("no tasks to resample")
    values = [per_task[t] for t in tasks]
    rng = random.Random(seed)
    n = len(values)
    means = sorted(sum(values[rng.randrange(n)] for _ in range(n)) / n for _ in range(samples))
    return (_percentile(means, 0.025), _percentile(means, 0.975))


def _check_rows(rows: list[dict]) -> None:
    if not rows:
        raise ReportError("no graded rows")
    seen = set()
    for row in rows:
        missing = [k for k in ("task", "arm", "trial", "status", "upstream_pass") if k not in row]
        if missing:
            raise ReportError(f"row lacks {missing}")
        if row["arm"] not in ARMS:
            raise ReportError(f"unknown arm {row['arm']!r}")
        key = (row["task"], row["arm"], row["trial"])
        if key in seen:
            raise ReportError(f"duplicate cell {key}")
        seen.add(key)


def _task_rates(rows: list[dict], arm: str) -> dict[str, float]:
    """Per-task pass fraction over that arm's evaluable trials (missing counts as failure)."""
    by_task: dict[str, list[int]] = {}
    for row in rows:
        if row["arm"] == arm:
            by_task.setdefault(row["task"], []).append(1 if row["upstream_pass"] else 0)
    return {task: sum(v) / len(v) for task, v in by_task.items()}


def summarize(rows: list[dict], catalog: dict | None = None, samples: int = BOOTSTRAP_SAMPLES) -> dict:
    """Per-arm rates with intervals, paired differences, false acceptance, cost, categories."""
    _check_rows(rows)
    arms = [a for a in ARMS if any(r["arm"] == a for r in rows)]
    tasks = sorted({r["task"] for r in rows})
    out: dict = {"tasks": len(tasks), "cells": len(rows), "arms": {}, "paired": {}, "categories": {},
                 "bootstrap": {"samples": samples, "seed": BOOTSTRAP_SEED, "unit": "task"}}
    rates = {}
    registered = {}
    for arm in arms:
        every = [r for r in rows if r["arm"] == arm]
        registered[arm] = {r["task"] for r in every}
        mine = [r for r in every if r.get("termination") not in INFRA_TERMINATIONS]
        if not mine:
            raise ReportError(f"arm {arm} has no evaluable cell")
        rates[arm] = _task_rates(mine, arm)
        passes = sum(r["upstream_pass"] for r in mine)
        accepted = [r for r in mine if r.get("internal") == "accepted"]
        false_accepts = [r for r in accepted if not r["upstream_pass"]]
        calls = sum(r.get("llm_calls") or 0 for r in every)
        out["arms"][arm] = {
            "cells": len(mine), "passes": passes, "pass_rate": passes / len(mine),
            "ci95_task_bootstrap": cluster_bootstrap(rates[arm], samples),
            "ci95_wilson_per_cell_reference": wilson(passes, len(mine)),
            "strict_passes": sum(r["status"] == "pass" for r in mine),
            "grader_disagreements": sum((r["status"] == "pass") != bool(r["upstream_pass"])
                                        for r in mine if r["status"] != "missing"),
            "missing": sum(r["status"] == "missing" for r in mine),
            "not_evaluable": len(every) - len(mine),
            "not_evaluable_cells": sorted(f"{r['task']}#{r['trial']}" for r in every if r not in mine),
            "terminations": _count(r.get("termination") for r in every),
            "internally_accepted": len(accepted), "false_acceptances": len(false_accepts),
            "false_acceptance_rate": len(false_accepts) / len(accepted) if accepted else None,
            "false_acceptance_cells": sorted(f"{r['task']}#{r['trial']}" for r in false_accepts),
            "tasks_always_pass": sum(v == 1.0 for v in rates[arm].values()),
            "tasks_never_pass": sum(v == 0.0 for v in rates[arm].values()),
            "llm_calls": calls, "input_tokens": sum(r.get("input_tokens") or 0 for r in every),
            "output_tokens": sum(r.get("output_tokens") or 0 for r in every),
            "seconds": sum(r.get("seconds") or 0 for r in every),
            "calls_per_pass": calls / passes if passes else None,
        }
    for better, base in PAIRS:
        if better in rates and base in rates:
            if registered[better] != registered[base]:
                raise ReportError(f"arms {better} and {base} cover different tasks")
            common = set(rates[better]) & set(rates[base])  # tasks with a verdict in both arms
            if not common:
                raise ReportError(f"arms {better} and {base} share no evaluable task")
            diff = {t: rates[better][t] - rates[base][t] for t in common}
            out["paired"][f"{better}-{base}"] = {
                "tasks_compared": len(common),
                "mean_difference": sum(diff.values()) / len(diff),
                "ci95_task_bootstrap": cluster_bootstrap(diff, samples),
                "tasks_better": sum(v > 0 for v in diff.values()),
                "tasks_worse": sum(v < 0 for v in diff.values()),
                "tasks_equal": sum(v == 0 for v in diff.values())}
    if catalog:
        for arm in arms:
            for task, rate in rates[arm].items():
                category = catalog.get(task, {}).get("category", "uncategorised")
                entry = out["categories"].setdefault(category, {}).setdefault(arm, {"tasks": 0, "sum": 0.0})
                entry["tasks"] += 1
                entry["sum"] += rate
        for per_arm in out["categories"].values():
            for entry in per_arm.values():
                entry["pass_rate"] = entry.pop("sum") / entry["tasks"]
    if "full_xcheck" in rates:
        if "full" in rates:
            out["paired_false_acceptance"] = {"full_xcheck-full": _paired_false_acceptance(
                rows, "full_xcheck", "full", samples)}
        out["cross_check"] = _cross_check_counts(rows, rates)
    return out


def _evaluable(rows: list[dict], arm: str) -> list[dict]:
    return [r for r in rows if r["arm"] == arm and r.get("termination") not in INFRA_TERMINATIONS]


def _false_accept(row: dict) -> bool:
    return row.get("internal") == "accepted" and not row["upstream_pass"]


def _task_false_acceptance(rows: list[dict], arm: str) -> dict[str, float]:
    """Per-task false acceptances over that arm's evaluable cells (not over accepted cells)."""
    by_task: dict[str, list[int]] = {}
    for row in _evaluable(rows, arm):
        by_task.setdefault(row["task"], []).append(1 if _false_accept(row) else 0)
    return {task: sum(v) / len(v) for task, v in by_task.items()}


def _paired_false_acceptance(rows: list[dict], better: str, base: str, samples: int) -> dict:
    """V1 primary endpoint: mean over tasks of FA_t(better) - FA_t(base), task bootstrap.

    FA_t is cells internally accepted and failing upstream over evaluable cells, so
    every task with an evaluable cell in both arms has a value and the pairing holds.
    """
    fa = {arm: _task_false_acceptance(rows, arm) for arm in (better, base)}
    common = set(fa[better]) & set(fa[base])
    diff = {t: fa[better][t] - fa[base][t] for t in common}
    return {"tasks_compared": len(common),
            "mean_difference": sum(diff.values()) / len(diff),
            "ci95_task_bootstrap": cluster_bootstrap(diff, samples),
            "tasks_fewer": sum(v < 0 for v in diff.values()),
            "tasks_more": sum(v > 0 for v in diff.values()),
            "tasks_equal": sum(v == 0 for v in diff.values()),
            # Over every evaluable cell of each arm (the event count of the V1 rule).
            "tasks_with_false_acceptance": {arm: sum(v > 0 for v in fa[arm].values())
                                            for arm in (better, base)}}


def _cell_name(row: dict) -> str:
    return f"{row['task']}#{row['trial']}"


def _cross_check_counts(rows: list[dict], rates: dict[str, dict[str, float]]) -> dict:
    """Request cross-check outcomes of the full_xcheck cells, as their runs recorded them.

    blocked_tasks (V1 secondary 2): C-off passes every evaluable trial, C-xcheck none,
    and some C-xcheck cell of the task recorded replanned or disagreement_kept.
    """
    mine = sorted((r for r in rows if r["arm"] == "full_xcheck"), key=lambda r: (r["task"], r["trial"]))
    outcomes = {_cell_name(r): r.get("cross_check_outcomes") for r in mine}

    def having(name):
        return sorted(c for c, found in outcomes.items() if found and name in found)

    out = {"cells": len(mine),
           "policies": _count(r.get("cross_check_policy") for r in mine),
           "cells_without_record": sorted(c for c, found in outcomes.items() if found is None),
           "outcomes": _count(o for found in outcomes.values() for o in (found or [])),
           "cells_by_outcome": _count(o for found in outcomes.values() for o in sorted(set(found or []))),
           "cells_checked": sum(any(o != "skipped" for o in found or []) for found in outcomes.values()),
           "replanned_cells": having("replanned"),
           "disagreement_kept_cells": having("disagreement_kept"),
           "blocked_tasks": None, "replans_passing": None, "replans_failing_where_off_passed": None}
    if "full" not in rates:
        return out
    off, xcheck = rates["full"], rates["full_xcheck"]
    disputed = {r["task"]: [] for r in mine}
    for r in mine:
        if {"replanned", "disagreement_kept"} & set(r.get("cross_check_outcomes") or []):
            disputed[r["task"]].append(_cell_name(r))
    out["blocked_tasks"] = [{"task": t, "cells": disputed[t]} for t in sorted(set(off) & set(xcheck))
                            if off[t] == 1.0 and xcheck[t] == 0.0 and disputed.get(t)]
    replanned = [r for r in _evaluable(rows, "full_xcheck") if "replanned" in (r.get("cross_check_outcomes") or [])]
    out["replans_passing"] = sorted(_cell_name(r) for r in replanned if r["upstream_pass"])
    out["replans_failing_where_off_passed"] = sorted(
        _cell_name(r) for r in replanned if not r["upstream_pass"] and off.get(r["task"], 0.0) > 0)
    return out


def _count(values) -> dict:
    counts: dict = {}
    for value in values:
        counts[str(value)] = counts.get(str(value), 0) + 1
    return dict(sorted(counts.items()))


# ---------------------------------------------------------------- rendering
def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{100 * value:.1f}%"


def _ci(pair) -> str:
    return f"{100 * pair[0]:.1f} to {100 * pair[1]:.1f}"


def render_markdown(summary: dict, title: str = "VerilogEval comparison") -> str:
    """A self-contained Markdown report of a summarize() result."""
    lines = [f"# {title}", "",
             f"{summary['tasks']} tasks, {summary['cells']} graded cells. Intervals are 95% task-clustered "
             f"bootstrap ({summary['bootstrap']['samples']} resamples, seed {summary['bootstrap']['seed']}); "
             "trials of one task are not independent. Missing submissions count as failures; cells stopped "
             "by infrastructure (model quota, interruption) are not verdicts and are excluded from rates.", "",
             "## Functional correctness (official testbench, upstream-compatible verdict)", "",
             "| Arm | Pass | Rate | 95% CI | Always / never pass (tasks) | Missing | Excluded (infrastructure) |",
             "|---|---|---|---|---|---|---|"]
    degenerate = False
    for arm, a in summary["arms"].items():
        interval = _ci(a["ci95_task_bootstrap"])
        if a["ci95_task_bootstrap"][0] == a["ci95_task_bootstrap"][1]:
            # Every task has the same rate: resampling cannot vary. Show the per-cell Wilson bound instead.
            interval, degenerate = _ci(a["ci95_wilson_per_cell_reference"]) + " (Wilson*)", True
        lines.append(f"| {ARM_LABEL[arm]} | {a['passes']}/{a['cells']} | {_pct(a['pass_rate'])} | "
                     f"{interval} | {a['tasks_always_pass']} / {a['tasks_never_pass']} | {a['missing']} | "
                     f"{a['not_evaluable']} |")
    if degenerate:
        lines += ["", "*All tasks had the same rate, so the bootstrap cannot vary; the per-cell Wilson interval "
                  "is shown and is optimistic if trials of a task are correlated."]
    if summary["paired"]:
        lines += ["", "## Paired differences (same tasks; percentage points)", "",
                  "| Comparison | Mean difference | 95% CI | Tasks better / equal / worse |", "|---|---|---|---|"]
        for name, p in summary["paired"].items():
            first, second = name.split("-")
            lines.append(f"| {ARM_LABEL[first]} minus {ARM_LABEL[second]} | {100 * p['mean_difference']:+.1f} | "
                         f"{100 * p['ci95_task_bootstrap'][0]:+.1f} to {100 * p['ci95_task_bootstrap'][1]:+.1f} | "
                         f"{p['tasks_better']} / {p['tasks_equal']} / {p['tasks_worse']} |")
        lines += ["", "An interval that includes 0 does not show a difference."]
    lines += ["", "## False acceptance (internally accepted, externally failing)", "",
              "| Arm | Internally accepted | False acceptances | Rate | Cells |", "|---|---|---|---|---|"]
    for arm, a in summary["arms"].items():
        cells = ", ".join(a["false_acceptance_cells"]) or "none"
        lines.append(f"| {ARM_LABEL[arm]} | {a['internally_accepted']} | {a['false_acceptances']} | "
                     f"{_pct(a['false_acceptance_rate'])} | {cells} |")
    for name, p in (summary.get("paired_false_acceptance") or {}).items():
        first, second = name.split("-")
        events = ", ".join(f"{ARM_LABEL[a]} {n}" for a, n in p["tasks_with_false_acceptance"].items())
        lines += ["", f"Paired false acceptance, {ARM_LABEL[first]} minus {ARM_LABEL[second]}, per evaluable "
                  "cell (mean over tasks of each task's share of evaluable cells accepted and failing; "
                  "percentage points):", "",
                  "| Mean difference | 95% CI | Tasks fewer / equal / more | Tasks with a false acceptance |",
                  "|---|---|---|---|",
                  f"| {100 * p['mean_difference']:+.1f} | {100 * p['ci95_task_bootstrap'][0]:+.1f} to "
                  f"{100 * p['ci95_task_bootstrap'][1]:+.1f} | {p['tasks_fewer']} / {p['tasks_equal']} / "
                  f"{p['tasks_more']} | {events} |"]
    lines += ["", "Arm A submissions are never internally verified, so it has no accepted set.", "",
              "## Cost", "", "| Arm | Model calls | Calls per pass | Input tokens | Output tokens | Wall hours |",
              "|---|---|---|---|---|---|"]
    for arm, a in summary["arms"].items():
        per = "n/a" if a["calls_per_pass"] is None else f"{a['calls_per_pass']:.1f}"
        lines.append(f"| {ARM_LABEL[arm]} | {a['llm_calls']} | {per} | {a['input_tokens']:,} | "
                     f"{a['output_tokens']:,} | {a['seconds'] / 3600:.1f} |")
    if summary["categories"]:
        arms = list(summary["arms"])
        lines += ["", "## By category (mean per-task pass rate)", "",
                  "| Category | Tasks | " + " | ".join(ARM_LABEL[a] for a in arms) + " |",
                  "|---|---|" + "---|" * len(arms)]
        for category, per_arm in sorted(summary["categories"].items()):
            tasks = next(iter(per_arm.values()))["tasks"]
            lines.append(f"| {category} | {tasks} | "
                         + " | ".join(_pct(per_arm[a]["pass_rate"]) if a in per_arm else "n/a" for a in arms) + " |")
    lines += ["", "## Integrity", "", "| Arm | Strict passes | Grader disagreements | Terminations |", "|---|---|---|---|"]
    for arm, a in summary["arms"].items():
        terms = ", ".join(f"{k} {v}" for k, v in a["terminations"].items())
        lines.append(f"| {ARM_LABEL[arm]} | {a['strict_passes']} | {a['grader_disagreements']} | {terms} |")
    if summary.get("cross_check"):
        lines += _render_cross_check(summary["cross_check"])
    lines += ["", "Limits: public tasks do not exclude training contamination; one model and backend; "
              "functional correctness only, no area or timing claim; the single-call arm is one backend "
              "invocation, not a tools-enabled agent baseline.", ""]
    return "\n".join(lines)


def _named(cells) -> str:
    return ", ".join(cells) if cells else "none"


def _render_cross_check(x: dict) -> list[str]:
    lines = ["", f"## Request cross-check ({ARM_LABEL['full_xcheck']})", "",
             f"{x['cells']} cells; the check ran (an outcome other than skipped) in {x['cells_checked']}. "
             "Outcomes are counted per recorded check; a replanned cell has one check per spec revision.", "",
             "| Outcome | Checks | Cells |", "|---|---|---|"]
    lines += [f"| {name} | {count} | {x['cells_by_outcome'].get(name, 0)} |" for name, count in x["outcomes"].items()]
    if not x["outcomes"]:
        lines.append("| none recorded | 0 | 0 |")
    policies = ", ".join(f"{k} {v}" for k, v in x["policies"].items())
    lines += ["", f"- Recorded policies: {policies}",
              f"- Cells without a cross-check record: {_named(x['cells_without_record'])}",
              f"- Replanned: {_named(x['replanned_cells'])}",
              f"- Disagreement kept: {_named(x['disagreement_kept_cells'])}"]
    if x["blocked_tasks"] is not None:
        blocked = "; ".join(f"{b['task']} ({', '.join(b['cells'])})" for b in x["blocked_tasks"])
        lines += ["- Blocked tasks (C full harness passes every evaluable trial, C-xcheck none, after a "
                  f"disagreement): {blocked or 'none'}",
                  f"- Replanned cells that pass: {_named(x['replans_passing'])}",
                  "- Replanned cells that fail where C full harness passed at least once: "
                  f"{_named(x['replans_failing_where_off_passed'])}"]
    return lines


# ---------------------------------------------------------------------- CLI
def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m benchmark.report")
    sub = parser.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("grade")
    g.add_argument("--manifest", required=True, type=Path)
    g.add_argument("--dataset", required=True, type=Path)
    g.add_argument("--attempt", required=True, type=Path)
    g.add_argument("--iverilog")
    g.add_argument("--vvp")
    r = sub.add_parser("render")
    r.add_argument("--summary", required=True, type=Path)
    r.add_argument("--catalog", type=Path)
    r.add_argument("--title", default="VerilogEval comparison")
    r.add_argument("--out", required=True, type=Path)
    a = parser.parse_args(argv)
    if a.cmd == "grade":
        from . import artifacts
        from . import verilogeval as ve
        manifest = artifacts.load_manifest(a.manifest, public_root=a.dataset, private_root=a.dataset)
        iverilog, vvp = ve.tool_paths(a.iverilog, a.vvp)
        rows = grade_attempt(manifest, a.dataset, a.attempt, iverilog=iverilog, vvp=vvp)
        print(json.dumps({"graded": len(rows), "summary": str(a.attempt / "grades" / "summary.json")}))
        return 0
    rows = read_json(a.summary)
    for row in rows:
        row.setdefault("trial", 0)  # pilot summaries graded before trials were recorded
    catalog = read_json(a.catalog) if a.catalog else None
    summary = summarize(rows, catalog)
    with a.out.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(render_markdown(summary, a.title))
    a.out.with_suffix(".json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps({"report": str(a.out), "arms": {k: v["pass_rate"] for k, v in summary["arms"].items()}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
