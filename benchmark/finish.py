"""Finish a registered campaign in one command: grade, report, claim, archive, audit.

    python -m benchmark.finish --manifest M.json --dataset D --attempt DIR --out evidence/<date>/<name>
                               --catalog C.json --title "..." [--forbid WORD] [--iverilog P --vvp P]

Steps, each refusing rather than guessing:
1. every registered cell is sealed (`benchmark.report.grade_attempt` checks);
2. grade once (an existing `grades/summary.json` is reused, never regraded);
3. archive to `--out` (`benchmark.archive`; refuses an existing folder);
4. apply the pre-registered rule (`benchmark.claim`) and write `claim.json`; a run
   without arms A and C (one arm, like flash-03) gets `claim.describe`: rates and
   disclosures, verdict `descriptive_only`, never a comparison claim;
5. write `README.md` from the report, the claim and the cell records;
6. seal `archive-manifest.json` and run `tools/evidence_audit.py --worktree`.

It prints the README results-table row for task P3. The coordinator then reads
every false acceptance and every non-`done` termination (ROADMAP B1 step 4),
may add findings to the README and re-seal with `python -m benchmark.archive
--out <folder> --seal`; the numbers and the claim are not edited by hand.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from . import archive, claim, report

ROOT = Path(__file__).resolve().parents[1]


class FinishError(RuntimeError):
    """A step refused; nothing after it ran."""


def _cell_lines(cells: dict, predicate) -> list[str]:
    out = []
    for name, entry in sorted(cells.items()):
        run = entry["run"]
        if predicate(run, entry):
            verdict = entry.get("verdict", {})
            out.append(f"- `{name}`: termination `{run.get('termination')}`, grade `{verdict.get('status', 'n/a')}`")
    return out


def _arms_sentence(arms: list[str]) -> str:
    labels = ["Arm " + claim.ARM_LABELS.get(arm, f"`{arm}`") for arm in arms] or ["No arm"]
    if len(labels) == 1:
        return labels[0]
    return "Arms " + ", ".join(label[4:] for label in labels[:-1]) + " and " + labels[-1][4:]


def _trials_text(stats: dict) -> str:
    """Registered trials per task: the graded and infrastructure-stopped cells of one arm over tasks."""
    counts = {a["cells"] + a["not_evaluable"] for a in stats.get("arms", {}).values()}
    tasks = stats.get("tasks") or 0
    if len(counts) == 1 and tasks and next(iter(counts)) % tasks == 0:
        trials = next(iter(counts)) // tasks
        return f"{trials} trial{'s' if trials != 1 else ''}"
    return "trials as registered"


def render_readme(*, title: str, registration: dict, stats: dict, decision: dict, cells: dict,
                  report_md: str) -> str:
    identity = registration.get("identity", {})
    runtime = identity.get("runtime", {})
    dataset = identity.get("dataset", {})
    not_done = _cell_lines(cells, lambda run, e: run.get("termination") != "done")
    arms = list(stats.get("arms", {}))
    lines = [f"# {title}", "",
             "Archived by `python -m benchmark.finish`. Numbers, claim and tables below are generated from "
             "the sealed cells; nothing was rerun or removed.", ""]
    if decision["verdict"] == "descriptive_only":
        lines += ["## Result (descriptive; no pre-registered comparison applies)", "",
                  decision["sentence"], ""]
    else:
        lines += ["## Claim (pre-registered rule, docs/DECISIONS.md 2026-11-20)", "",
                  f"**Verdict: `{decision['verdict']}`.** {decision['sentence']}", ""]
    if decision["disclosures"]:
        lines += ["Disclosures required by the rule:", ""] + [f"- {d}" for d in decision["disclosures"]] + [""]
    if decision["secondary"]:
        lines += ["Secondary comparisons (descriptive):", ""]
        for name, s in decision["secondary"].items():
            low, high = s["ci95_task_bootstrap"]
            lines.append(f"- {name.replace('-', ' minus ')}: {100 * s['mean_difference']:+.1f} pp "
                         f"(95% CI {100 * low:+.1f} to {100 * high:+.1f}), reading `{s['reading']}`")
        lines.append("")
    lines += ["## Identity", "",
              f"- Dataset: VerilogEval spec-to-RTL, commit `{dataset.get('commit')}`",
              f"- Runtime: commit `{runtime.get('commit')}`, sha256 `{runtime.get('sha256')}`",
              f"- Requested model: `{identity.get('requested_model')}`; observed: `{identity.get('observed_model')}`",
              f"- Tasks {stats['tasks']}, graded cells {stats['cells']}; registration copied as "
              "`benchmark_registration.json`", "",
              "## Protocol", "",
              f"{_arms_sentence(arms)}, {_trials_text(stats)} per task, run trial-major by "
              "`benchmark.campaign`; a cell is attempted "
              "once and never rerun. Grading with the official testbench (Icarus Verilog 12, upstream-compatible "
              "verdict) started only after every cell was sealed. Intervals are task-clustered bootstrap.", "",
              "## Non-`done` terminations", ""]
    lines += not_done or ["None."]
    lines += ["", "## Report", ""]
    body = report_md.split("\n", 2)[2] if report_md.startswith("# ") else report_md
    lines += [body.replace("\n## ", "\n### ").strip(), "",
              "## Files", "",
              "`report.md`/`report.json` (statistics), `claim.json` (rule output), `summary.json` (graded rows), "
              "`cells.json` (run record, verdict and run summary per cell), `rtl/` (every sealed design), "
              "`campaign.log`, `runtime-identity.txt`, `benchmark_registration.json`, `archive-manifest.json` "
              "(SHA-256 of every file).", ""]
    return "\n".join(lines)


def finish(manifest_path: Path, dataset: Path, attempt: Path, out: Path, *, catalog: dict | None,
           title: str, forbidden: tuple[str, ...] = (), audit: bool = True, links: str = "",
           grade=None, run_audit=None) -> dict:
    attempt, out = Path(attempt), Path(out)
    if out.exists():
        raise FinishError(f"{out} already exists; finish never overwrites evidence")
    summary_path = attempt / "grades" / "summary.json"
    if not summary_path.is_file():
        if grade is None:
            raise FinishError("attempt is not graded and no grader was given")
        grade(manifest_path, dataset, attempt)
    archive.archive_attempt(attempt, out, catalog=catalog, title=title, forbidden=forbidden)
    stats = json.loads((out / "report.json").read_text(encoding="utf-8"))
    # A run without arms A and C (flash-03: one arm) gets a descriptive result, never a verdict.
    decision = claim.decide(stats) if claim.has_registered_comparison(stats) else claim.describe(stats)
    readme = render_readme(title=title, stats=stats, decision=decision,
                           registration=json.loads((out / "benchmark_registration.json").read_text(encoding="utf-8")),
                           cells=json.loads((out / "cells.json").read_text(encoding="utf-8")),
                           report_md=(out / "report.md").read_text(encoding="utf-8"))
    for name, text in (("claim.json", json.dumps(decision, indent=1) + "\n"), ("README.md", readme)):
        text = archive.sanitize(text)
        for word in forbidden:
            if word and word.lower() in text.lower():
                raise FinishError(f"{name} contains a forbidden word")
        (out / name).write_text(text, encoding="utf-8", newline="\n")
    archive.seal(out)
    if audit:
        (run_audit or _audit)()
    return {"out": str(out), "verdict": decision["verdict"], "readme_row": claim.readme_row(decision, stats, links)}


def _audit() -> None:
    done = subprocess.run([sys.executable, str(ROOT / "tools" / "evidence_audit.py"), "--worktree"], cwd=ROOT)
    if done.returncode:
        raise FinishError("evidence audit failed; see its output, fix, then re-seal")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m benchmark.finish")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--attempt", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--title", default="VerilogEval comparison")
    parser.add_argument("--forbid", action="append", default=[])
    parser.add_argument("--links", default="", help="evidence links for the README table row")
    parser.add_argument("--iverilog")
    parser.add_argument("--vvp")
    parser.add_argument("--no-audit", action="store_true")
    a = parser.parse_args(argv)

    def grade(manifest_path, dataset, attempt):
        from . import artifacts
        from . import verilogeval as ve
        manifest = artifacts.load_manifest(manifest_path, public_root=dataset, private_root=dataset)
        iverilog, vvp = ve.tool_paths(a.iverilog, a.vvp)
        report.grade_attempt(manifest, dataset, attempt, iverilog=iverilog, vvp=vvp)

    catalog = json.loads(a.catalog.read_text(encoding="utf-8")) if a.catalog else None
    try:
        result = finish(a.manifest, a.dataset, a.attempt, a.out, catalog=catalog, title=a.title,
                        forbidden=tuple(a.forbid), audit=not a.no_audit, links=a.links, grade=grade)
    except (FinishError, report.ReportError, archive.ArchiveError, claim.ClaimError) as exc:
        print(f"finish refused: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
