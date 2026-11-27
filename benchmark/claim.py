"""The pre-registered decision rule for the final comparison, as code.

    python -m benchmark.claim --report REPORT.json [--out CLAIM.json]

Registered November 20, 2026 (docs/DECISIONS.md), after final-02 had started
but before any cell was graded: `benchmark.report grade` refuses to run until
every cell is sealed, so no verdict existed when these thresholds were fixed.
The rule reads only a `benchmark.report.summarize` result and returns the
claim, the sentence to publish and the disclosures that must accompany it.
Nothing here is tuned after grading; changing a threshold needs a new dated
decision and the old verdict reported beside the new one.

Primary endpoint: upstream-compatible pass, arm C (full harness) minus arm A
(single call), mean of per-task differences with the 95% task-clustered
bootstrap interval.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PRIMARY = "full-single_call"
SECONDARY = ("full-ablation", "ablation-single_call")
EQUIVALENCE_MARGIN = 0.10      # |difference| bound for "no material difference"
MAX_NOT_EVALUABLE = 0.10       # share of an arm's cells stopped by infrastructure
FALSE_ACCEPTANCE_LIMIT = 0.05  # internal acceptance is called unreliable above this rate

VERDICTS = ("harness_better", "single_call_better", "no_material_difference", "inconclusive")


class ClaimError(ValueError):
    """The summary lacks what the registered rule needs."""


def _pp(value: float) -> str:
    return f"{100 * value:+.1f}"


def _interval(pair) -> str:
    return f"{_pp(pair[0])} to {_pp(pair[1])} pp"


def classify(ci: tuple[float, float], margin: float = EQUIVALENCE_MARGIN) -> str:
    """Interval rule: excludes 0 on one side, sits inside the margin, or neither."""
    low, high = ci
    if low > 0:
        return "harness_better"
    if high < 0:
        return "single_call_better"
    if -margin <= low and high <= margin:
        return "no_material_difference"
    return "inconclusive"


def decide(summary: dict) -> dict:
    """Apply the registered rule to a summarize() result."""
    arms, paired = summary.get("arms", {}), summary.get("paired", {})
    for arm in ("single_call", "full"):
        if arm not in arms:
            raise ClaimError(f"arm {arm} is missing from the summary")
    if PRIMARY not in paired:
        raise ClaimError(f"paired comparison {PRIMARY} is missing from the summary")
    primary = paired[PRIMARY]
    ci = tuple(primary["ci95_task_bootstrap"])
    verdict = classify(ci)
    disclosures, flags = [], []

    for arm, a in arms.items():
        registered = a["cells"] + a["not_evaluable"]
        share = a["not_evaluable"] / registered if registered else 0.0
        if share > MAX_NOT_EVALUABLE:
            flags.append(f"incomplete:{arm}")
            disclosures.append(f"{a['not_evaluable']} of {registered} cells of {arm} were stopped by "
                               f"infrastructure ({100 * share:.0f}%, above the registered "
                               f"{100 * MAX_NOT_EVALUABLE:.0f}%); the result is descriptive only.")
        elif a["not_evaluable"]:
            disclosures.append(f"{a['not_evaluable']} cell(s) of {arm} were stopped by infrastructure and "
                               "are excluded from rates.")
    if primary["tasks_compared"] < summary.get("tasks", primary["tasks_compared"]):
        disclosures.append(f"The primary comparison covers {primary['tasks_compared']} of "
                           f"{summary['tasks']} tasks (the rest have no evaluable cell in one arm).")
    if any(f.startswith("incomplete:") for f in flags) and verdict != "inconclusive":
        flags.append(f"downgraded_from:{verdict}")
        verdict = "inconclusive"

    for arm in ("ablation", "full"):
        a = arms.get(arm)
        if not a or not a["internally_accepted"]:
            continue
        if a["false_acceptances"]:
            disclosures.append(f"{arm}: {a['false_acceptances']} of {a['internally_accepted']} internally "
                               f"accepted designs fail the official testbench "
                               f"({', '.join(a['false_acceptance_cells'])}).")
        if (a["false_acceptance_rate"] or 0) > FALSE_ACCEPTANCE_LIMIT:
            flags.append(f"unreliable_acceptance:{arm}")
            disclosures.append(f"{arm}: false acceptance above {100 * FALSE_ACCEPTANCE_LIMIT:.0f}%, so internal "
                               "acceptance is not a reliable correctness signal on these tasks.")

    a, c = arms["single_call"], arms["full"]
    cost = (c["calls_per_pass"] / a["calls_per_pass"]
            if c.get("calls_per_pass") and a.get("calls_per_pass") else None)
    rates = f"C {100 * c['pass_rate']:.1f}% vs A {100 * a['pass_rate']:.1f}%"
    difference = f"{_pp(primary['mean_difference'])} pp (95% CI {_interval(ci)}, {primary['tasks_compared']} tasks)"
    cost_text = f"; the harness used {cost:.1f}x the model calls per pass" if cost else ""
    sentence = {
        "harness_better": f"The full harness passes more tasks than a single model call: {rates}, "
                          f"difference {difference}{cost_text}.",
        "single_call_better": f"A single model call passes more tasks than the full harness: {rates}, "
                              f"difference {difference}{cost_text}.",
        "no_material_difference": f"On these tasks the full harness and a single model call perform the same "
                                  f"within {100 * EQUIVALENCE_MARGIN:.0f} pp: {rates}, difference "
                                  f"{difference}{cost_text}.",
        "inconclusive": f"No difference is shown between the full harness and a single model call: {rates}, "
                        f"difference {difference}; the interval is too wide to rule out a "
                        f"{100 * EQUIVALENCE_MARGIN:.0f} pp effect{cost_text}.",
    }[verdict]
    secondary = {name: {"mean_difference": paired[name]["mean_difference"],
                        "ci95_task_bootstrap": paired[name]["ci95_task_bootstrap"],
                        "reading": classify(tuple(paired[name]["ci95_task_bootstrap"]))}
                 for name in SECONDARY if name in paired}
    return {"rule": "docs/DECISIONS.md 2026-11-20", "primary": PRIMARY, "verdict": verdict,
            "sentence": sentence, "mean_difference": primary["mean_difference"], "ci95": list(ci),
            "calls_per_pass_ratio": cost, "secondary": secondary, "flags": flags,
            "disclosures": disclosures,
            "thresholds": {"equivalence_margin": EQUIVALENCE_MARGIN, "max_not_evaluable": MAX_NOT_EVALUABLE,
                           "false_acceptance_limit": FALSE_ACCEPTANCE_LIMIT}}


ARM_LABELS = {"single_call": "A (single call)", "ablation": "B (harness without generated-testbench "
              "mutation qualification)", "full": "C (full harness)"}


def has_registered_comparison(summary: dict) -> bool:
    """True when the summary holds both arms of the pre-registered primary endpoint."""
    arms = summary.get("arms", {})
    return "single_call" in arms and "full" in arms and PRIMARY in summary.get("paired", {})


def describe(summary: dict) -> dict:
    """Descriptive result for a run without the registered comparison (e.g. one arm only).

    No verdict is drawn: the pre-registered rule needs arms A and C. Pass rates,
    infrastructure stops and false acceptances are still stated per arm.
    """
    arms = summary.get("arms", {})
    if not arms:
        raise ClaimError("the summary has no arms")
    parts, disclosures = [], []
    for arm, a in arms.items():
        low, high = a["ci95_task_bootstrap"]
        parts.append(f"arm {ARM_LABELS.get(arm, arm)} passes {a['passes']} of {a['cells']} graded cells "
                     f"({100 * a['pass_rate']:.1f}%, 95% task-clustered CI {100 * low:.1f}% to "
                     f"{100 * high:.1f}%)")
        if a["not_evaluable"]:
            disclosures.append(f"{a['not_evaluable']} cell(s) of {arm} were stopped by infrastructure and are "
                               "excluded from rates.")
        if a.get("false_acceptances"):
            disclosures.append(f"{arm}: {a['false_acceptances']} of {a['internally_accepted']} internally "
                               f"accepted designs fail the official testbench "
                               f"({', '.join(a['false_acceptance_cells'])}).")
    sentence = ("No pre-registered comparison applies (it needs arms A and C); descriptive only: "
                + "; ".join(parts) + ".")
    return {"rule": None, "primary": None, "verdict": "descriptive_only", "sentence": sentence,
            "secondary": {}, "flags": ["no_registered_comparison"], "disclosures": disclosures}


def readme_row(claim: dict, summary: dict, links: str) -> str:
    """The README results-table row for the comparison (task P3)."""
    tail = " ".join(claim["disclosures"])
    if claim["verdict"] == "descriptive_only":
        text = (f"**Registered descriptive run.** {summary['tasks']} public VerilogEval tasks, "
                f"{len(summary['arms'])} arm(s), tasks fixed before any cell. {claim['sentence']}"
                + (f" {tail}" if tail else ""))
        return f"| {text} | {links} |"
    text = (f"**Registered comparison with a single model call.** {summary['tasks']} public VerilogEval "
            f"tasks, three arms, three trials, tasks and decision rule fixed before grading. "
            f"{claim['sentence']}" + (f" {tail}" if tail else ""))
    return f"| {text} | {links} |"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m benchmark.claim")
    parser.add_argument("--report", required=True, type=Path, help="report.json written by benchmark.report render")
    parser.add_argument("--out", type=Path)
    a = parser.parse_args(argv)
    claim = decide(json.loads(a.report.read_text(encoding="utf-8")))
    text = json.dumps(claim, indent=1)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8", newline="\n")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
