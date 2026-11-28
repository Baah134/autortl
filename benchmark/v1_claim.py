"""The V1 decision rule (request cross-check on fresh tasks) as code: a PROPOSAL.

    python -m benchmark.v1_claim --report REPORT.json [--out CLAIM.json]

Status: PROPOSAL, NOT FROZEN. This module implements section "Decision rule
(proposal)" of docs/V1_REGISTRATION_DRAFT.md exactly as drafted (November 27,
2026), with its numbers as the constants below. It decides nothing until the
owner freezes the registration: a dated docs/DECISIONS.md entry, then RULE set
to that entry and FROZEN set to True in a commit before the first V1 cell runs.
Until then every result carries the flag `rule_not_frozen`, and no verdict can
make a default change eligible. After freezing, a threshold change needs a new
dated decision with the old verdict reported beside the new one.

The rule reads only a `benchmark.report.summarize` result of a run with arms
C-off (`full`) and C-xcheck (`full_xcheck`). Endpoints (draft "Endpoints"):

- primary: false-acceptance difference, mean over tasks of FA_t(C-xcheck) -
  FA_t(C-off), FA_t being cells internally accepted and failing the official
  testbench over evaluable cells (`paired_false_acceptance["full_xcheck-full"]`);
- pass-rate difference, C-xcheck - C-off (`paired["full_xcheck-full"]`);
- both with the 95% task-clustered bootstrap, 10,000 resamples, seed 20261115;
- blocked tasks: C-off passes every evaluable trial, C-xcheck none, with a
  `replanned` or `disagreement_kept` outcome in a C-xcheck cell
  (`cross_check["blocked_tasks"]`).

Rules, applied in order: (1) more than 10% of either arm's cells stopped by
infrastructure -> inconclusive (descriptive only; the verdict rules 2-7 would
have given is recorded as `downgraded_from:<verdict>`); (2) pass-rate interval
entirely below 0 -> blocks_correct_designs; (3) false-acceptance interval
entirely above 0 -> increases_false_acceptance; (4) C-off has false acceptances
on fewer than 3 tasks -> insufficient_events; (5) false-acceptance interval
entirely below 0, pass-rate lower bound >= -10 pp, mean pass-rate difference
>= 0 and no blocked task -> reduces_false_acceptance; (6) false-acceptance
interval inside +-3 pp and pass-rate interval inside +-10 pp ->
no_material_difference; (7) otherwise inconclusive. Only
reduces_false_acceptance under a frozen rule makes a change of the
`RunConfig.spec_cross_check` default eligible, and even then only by an
owner-approved dated decision: the verdict alone changes no code.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import claim

RULE = "docs/V1_REGISTRATION_DRAFT.md decision rule (proposal, not frozen)"
FROZEN = False
ARM_OFF, ARM_XCHECK = "full", "full_xcheck"
PRIMARY = f"{ARM_XCHECK}-{ARM_OFF}"
MAX_NOT_EVALUABLE = 0.10        # rule 1: share of an arm's cells stopped by infrastructure
PASS_RATE_FLOOR = -0.10         # rule 5: pass-rate interval lower bound
FALSE_ACCEPTANCE_MARGIN = 0.03  # rule 6: false-acceptance interval inside +-3 pp
PASS_RATE_MARGIN = 0.10         # rule 6: pass-rate interval inside +-10 pp
MIN_EVENT_TASKS = 3             # rule 4: C-off tasks with a false acceptance
BOOTSTRAP_SAMPLES = 10_000
BOOTSTRAP_SEED = 20261115
ADOPT = "reduces_false_acceptance"
VERDICTS = ("blocks_correct_designs", "increases_false_acceptance", "insufficient_events", ADOPT,
            "no_material_difference", "inconclusive")


class ClaimError(claim.ClaimError):
    """The summary lacks what the V1 rule needs."""


def applies(summary: dict) -> bool:
    """True when the summary holds both V1 arms and their paired comparison."""
    arms = summary.get("arms", {})
    return ARM_OFF in arms and ARM_XCHECK in arms and PRIMARY in summary.get("paired", {})


def rule(pass_ci, pass_mean: float, fa_ci, events: int, blocked: list) -> str:
    """Rules 2 to 7 of the draft, in order (rule 1, completeness, is applied by decide)."""
    pass_low, pass_high = pass_ci
    fa_low, fa_high = fa_ci
    if pass_high < 0:
        return "blocks_correct_designs"
    if fa_low > 0:
        return "increases_false_acceptance"
    if events < MIN_EVENT_TASKS:
        return "insufficient_events"
    if fa_high < 0 and pass_low >= PASS_RATE_FLOOR and pass_mean >= 0 and not blocked:
        return ADOPT
    if (-FALSE_ACCEPTANCE_MARGIN <= fa_low and fa_high <= FALSE_ACCEPTANCE_MARGIN
            and -PASS_RATE_MARGIN <= pass_low and pass_high <= PASS_RATE_MARGIN):
        return "no_material_difference"
    return "inconclusive"


def _inputs(summary: dict) -> tuple[dict, dict, dict, dict]:
    if not applies(summary):
        raise ClaimError(f"the summary needs arms {ARM_OFF} and {ARM_XCHECK} and the paired comparison {PRIMARY}")
    bootstrap = summary.get("bootstrap", {})
    if bootstrap.get("samples") != BOOTSTRAP_SAMPLES or bootstrap.get("seed") != BOOTSTRAP_SEED:
        raise ClaimError(f"the rule needs the task bootstrap with {BOOTSTRAP_SAMPLES} resamples and seed "
                         f"{BOOTSTRAP_SEED}; the summary has {bootstrap.get('samples')} and {bootstrap.get('seed')}")
    fa = summary.get("paired_false_acceptance", {}).get(PRIMARY)
    if not fa or ARM_OFF not in fa.get("tasks_with_false_acceptance", {}):
        raise ClaimError(f"paired false-acceptance difference {PRIMARY} is missing from the summary")
    cross = summary.get("cross_check")
    if not cross or not isinstance(cross.get("blocked_tasks"), list):
        raise ClaimError("cross-check outcomes with blocked tasks are missing from the summary")
    return summary["arms"], summary["paired"][PRIMARY], fa, cross


def _pp(value: float) -> str:
    return f"{100 * value:+.1f}"


def _interval(pair) -> str:
    return f"{_pp(pair[0])} to {_pp(pair[1])} pp"


def decide(summary: dict) -> dict:
    """Apply the proposed V1 rule to a summarize() result."""
    arms, paired, fa, cross = _inputs(summary)
    pass_ci, fa_ci = tuple(paired["ci95_task_bootstrap"]), tuple(fa["ci95_task_bootstrap"])
    events = fa["tasks_with_false_acceptance"][ARM_OFF]
    blocked = cross["blocked_tasks"]
    flags, disclosures = [], []
    if not FROZEN:
        flags.append("rule_not_frozen")
        disclosures.append("The V1 decision rule is a proposal that has not been frozen; this verdict is "
                           "descriptive until the owner freezes the registration.")

    incomplete = False
    for arm in (ARM_OFF, ARM_XCHECK):  # rule 1: either V1 arm
        a = arms[arm]
        registered = a["cells"] + a["not_evaluable"]
        share = a["not_evaluable"] / registered if registered else 0.0
        if share > MAX_NOT_EVALUABLE:
            incomplete = True
            flags.append(f"incomplete:{arm}")
            disclosures.append(f"{a['not_evaluable']} of {registered} cells of {arm} were stopped by "
                               f"infrastructure ({100 * share:.0f}%, above {100 * MAX_NOT_EVALUABLE:.0f}%); "
                               "the result is descriptive only.")
        elif a["not_evaluable"]:
            disclosures.append(f"{a['not_evaluable']} cell(s) of {arm} were stopped by infrastructure and are "
                               "excluded from rates.")
    verdict = rule(pass_ci, paired["mean_difference"], fa_ci, events, blocked)
    if incomplete:
        if verdict != "inconclusive":
            flags.append(f"downgraded_from:{verdict}")
        verdict = "inconclusive"

    tasks = summary.get("tasks")
    for name, entry in (("pass-rate", paired), ("false-acceptance", fa)):
        if tasks is not None and entry["tasks_compared"] < tasks:
            disclosures.append(f"The {name} comparison covers {entry['tasks_compared']} of {tasks} tasks (the rest "
                               "have no evaluable cell in one arm).")
    if blocked:
        disclosures.append("Blocked tasks (C-off passes every evaluable trial, C-xcheck none, after a "
                           "disagreement): " + "; ".join(f"{b['task']} ({', '.join(b['cells'])})" for b in blocked)
                           + ".")
    wrong = {p: n for p, n in cross.get("policies", {}).items() if p not in ("request_traces", "None")}
    if wrong:
        disclosures.append(f"{ARM_XCHECK} cells recorded another cross-check policy: "
                           + ", ".join(f"{p} {n}" for p, n in wrong.items()) + ".")
    if cross.get("cells_without_record"):
        disclosures.append(f"{len(cross['cells_without_record'])} {ARM_XCHECK} cell(s) have no cross-check record: "
                           + ", ".join(cross["cells_without_record"]) + ".")
    for arm in (ARM_OFF, ARM_XCHECK):
        a = arms[arm]
        if a.get("false_acceptances"):
            disclosures.append(f"{arm}: {a['false_acceptances']} of {a['internally_accepted']} internally "
                               f"accepted designs fail the official testbench "
                               f"({', '.join(a['false_acceptance_cells'])}).")

    off, x = arms[ARM_OFF], arms[ARM_XCHECK]
    fa_text = f"{_pp(fa['mean_difference'])} pp (95% CI {_interval(fa_ci)}, {fa['tasks_compared']} tasks)"
    pass_text = (f"{_pp(paired['mean_difference'])} pp (95% CI {_interval(pass_ci)}; C-xcheck "
                 f"{100 * x['pass_rate']:.1f}% vs C-off {100 * off['pass_rate']:.1f}%)")
    both = f"false-acceptance difference {fa_text}, pass-rate difference {pass_text}"
    sentence = {
        "blocks_correct_designs": f"The request cross-check blocks correct designs: {both}. The default stays off.",
        "increases_false_acceptance": f"The request cross-check increases false acceptance: {both}. "
                                      "The default stays off.",
        "insufficient_events": f"C-off falsely accepted designs on {events} task(s), fewer than the "
                               f"{MIN_EVENT_TASKS} needed to measure a reduction; descriptive only: {both}. "
                               "The default stays off.",
        ADOPT: f"The request cross-check reduces false acceptance without blocking correct designs: {both}.",
        "no_material_difference": f"No material difference between the full harness with and without the "
                                  f"request cross-check (within {100 * FALSE_ACCEPTANCE_MARGIN:.0f} pp false "
                                  f"acceptance and {100 * PASS_RATE_MARGIN:.0f} pp pass rate): {both}. "
                                  "The default stays off.",
        "inconclusive": f"The request cross-check is not shown to change false acceptance: {both}. "
                        "The default stays off.",
    }[verdict]
    outcomes = {"replanned": len(cross.get("replanned_cells", [])),
                "disagreement_kept": len(cross.get("disagreement_kept_cells", [])),
                "cells_checked": cross.get("cells_checked"), "cells": cross.get("cells"),
                "outcomes": cross.get("outcomes", {})}
    return {"rule": RULE, "frozen": FROZEN, "primary": PRIMARY, "verdict": verdict, "sentence": sentence,
            "default_change_eligible": FROZEN and verdict == ADOPT,
            "false_acceptance": {"mean_difference": fa["mean_difference"], "ci95": list(fa_ci),
                                 "tasks_compared": fa["tasks_compared"],
                                 "per_accepted_rate": {arm: arms[arm]["false_acceptance_rate"]
                                                       for arm in (ARM_OFF, ARM_XCHECK)}},
            "pass_rate": {"mean_difference": paired["mean_difference"], "ci95": list(pass_ci),
                          "tasks_compared": paired["tasks_compared"]},
            "events": {"off_tasks_with_false_acceptance": events, "minimum": MIN_EVENT_TASKS},
            "blocked_tasks": blocked, "cross_check": outcomes, "secondary": {}, "flags": flags,
            "disclosures": disclosures,
            "thresholds": {"max_not_evaluable": MAX_NOT_EVALUABLE, "pass_rate_floor": PASS_RATE_FLOOR,
                           "false_acceptance_margin": FALSE_ACCEPTANCE_MARGIN,
                           "pass_rate_margin": PASS_RATE_MARGIN, "min_event_tasks": MIN_EVENT_TASKS,
                           "bootstrap_samples": BOOTSTRAP_SAMPLES, "bootstrap_seed": BOOTSTRAP_SEED}}


def readme_row(decision: dict, summary: dict, links: str) -> str:
    """The README results-table row for a V1 run."""
    status = "registered" if decision.get("frozen") else "proposed, not frozen"
    tail = " ".join(decision["disclosures"])
    text = (f"**Request cross-check (V1, rule {status}).** {summary['tasks']} public VerilogEval tasks, "
            f"C-off and C-xcheck. Verdict `{decision['verdict']}`. {decision['sentence']}"
            + (f" {tail}" if tail else ""))
    return f"| {text} | {links} |"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m benchmark.v1_claim")
    parser.add_argument("--report", required=True, type=Path, help="report.json written by benchmark.report render")
    parser.add_argument("--out", type=Path)
    a = parser.parse_args(argv)
    try:
        decision = decide(json.loads(a.report.read_text(encoding="utf-8")))
    except ClaimError as exc:
        print(f"v1_claim refused: {exc}", file=sys.stderr)
        return 2
    text = json.dumps(decision, indent=1)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8", newline="\n")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
