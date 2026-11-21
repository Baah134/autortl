# Decision record

## 2026-10-19 — Shared workspace and model-independent development

User requested moving the active project into Downloads and allowing different
AI coordinators to continue when another provider reaches its limit. Moved the
complete clone to Downloads/autortl-work and verified 317 file hashes. Preserved
the separate, preexisting Downloads/autortl folder. Original review/evidence
artifacts remain in Documents/Codex/2026-10-15/hey until their retained evidence
is copied into this repository.

Use one active coordinator with separate worker file claims. Keep canonical
instructions and status in the repository, transactional ownership locally,
and implementation history on GitHub. Each provider can use its own subagents.
Runtime provider changes remain explicit, tested integrations.

## 2026-10-19 — Publish substantive milestones

User authorized pushing good progress to GitHub. Push tested development
commits with accurate validation notes. Keep unfinished integration work visible
and preserve main until required gates pass. Activity follows engineering
milestones rather than artificial commit frequency.

## 2026-10-19 — Integrate the completed checkpoint into main

The user explicitly requested: "merge everything so we improve as we go".
Fast-forward integrate the six completed development commits through 387fe0e
into main, preserving their implementation, tests and full failure evidence.
This instruction authorizes integrating the current tested checkpoint before
the previously documented full-campaign/held-tier merge gate. It does not waive
RTL verification, change any hardware acceptance result or declare a tier held.
The existing evidence is 423 passing tests, nine live testbench cases, a passing
counter repair simulation and passing mux routed timing. The first autonomous
cohort remains 0/2. Next is authoritative contract context and a fresh cohort.
Future harness changes retain the default test/benchmark review requirements.

## 2026-10-28 — Message channel between alternating agents

The user asked for a communication channel so Codex and Claude Code can work
well in turns. The lease records ownership and the checkpoint holds one current
summary, which the next checkpoint overwrites. Neither carries a question or
review request until it is answered, and the waiting agent cannot write either
without the lease. Added `coordination/mail.py`, an append-only, Git-tracked
JSONL mailbox with post, inbox and close, and tests in `coordination/test_mail.py`.
It was kept out of `autortl/coordination.py` and `scripts/session.py` because
those files are in the frozen source sets that campaign13's recovery depends on.
No schema, lease rule or harness runtime changed. Revisit by folding it into
the coordination store once the frozen campaigns are resolved, if both agents
use it.

## 2026-11-20 — Pre-registered decision rule for the final comparison

Fixed before any final-02 cell was graded (123 of 360 cells sealed;
`benchmark.report grade` refuses to run until all are sealed, so no verdict
existed). Implemented as `benchmark/claim.py` and applied by
`python -m benchmark.finish`; the published claim is that module's output.

- **Primary endpoint:** upstream-compatible pass on the official testbench.
- **Primary comparison:** arm C (full harness) minus arm A (single call),
  mean of per-task differences with the 95% task-clustered bootstrap interval
  over the 40 registered tasks.
- **Verdict:** interval above 0 → `harness_better`; below 0 →
  `single_call_better`; inside ±10 percentage points → `no_material_difference`;
  otherwise `inconclusive` ("no difference shown; cannot rule out 10 pp").
- **Completeness:** if more than 10% of any arm's cells were stopped by
  infrastructure (model quota, interruption), the verdict is downgraded to
  `inconclusive` and the result is reported as descriptive only.
- **False acceptance:** every internally accepted design that fails the
  official testbench is named. Above 5% of an arm's accepted designs, the
  claim must say internal acceptance is not a reliable correctness signal on
  these tasks.
- **Always reported:** C minus B and B minus A as secondary, descriptive
  readings; model calls per pass, C over A; every non-`done` termination.
- **Not allowed:** removing tasks or cells, rerunning cells, changing a
  threshold after grading. A later change needs a new dated decision and the
  original verdict reported beside it.

ROADMAP B2 now reduces to recording this rule's output and, if it shows a
recurring planner failure, the follow-up (former task C4).

## 2026-11-21 — Fixes found on final-02 tasks stay out of its claim

Two harness failure causes seen in final-02's internal logs (before grading)
are fixed on branch `bench-fixes`: `multi_module_plan_without_trusted_tb`
(Prob131) and a recurrence of `fixed_latency_observation_ambiguous`
(Prob153_gshare). Both are general (a structural check and a prompt
clarification); neither weakens a check.

- They merge only after final-02 and flash-02 finish, so neither registered
  runtime changes.
- final-02 is reported as run. No cell is rerun with the fixes.
- Any later number on the same 40 tasks is tuned on them. It is reported as
  such, beside the registered result, never in place of it.

## 2026-11-21 — flash-01 had tools; flash-02 withdrawn before any cell

A live check of the Antigravity bridge found that `agy` runs Gemini as an agent
with web search, shell commands and file tools; `--sandbox` restricts only its
terminal, and permission deny rules did not stop `search_web`. On the
Prob131 planner prompt Flash-high made 46 web searches (one for
`"VerilogEval" "mt2015_q4"`) and 14 commands and took 6 minutes, more than
the harness's 180-second call limit. Flash-low used no tools there and took
18 seconds.

- **flash-01** (Flash-high, single call, 110/120) ran with these tools
  available, and the bridge recorded no tool events. The published references
  are on the web, so it is not a closed-book single call and is not compared
  with Codex arm A. It stays archived as run, described as "Gemini 3.8 Flash
  through the Antigravity agent, web search available". Call times are
  consistent with tool use in many cells (median 18 s against 7 s for a
  trivial prompt) but cannot show which cells used tools.
- **flash-02** (registered November 20, 0 cells run) is withdrawn: as
  registered, its planner calls would exceed the call limit, and its replies
  could use the web. Its auto-start watcher was stopped.
- The bridge now refuses any reply produced with a tool call
  (`agy_endpoint_uses_tools`). Any new Flash run needs a new registration that
  uses the guarded bridge and a model variant that fits the call limit.

## Continuing contracts

Use command-line Vivado. Specifications and independent verification control
acceptance. Infrastructure failures never justify changing RTL or claiming
design progress. Keep matching source, constraints and report evidence. Record
build correctness and optimization improvement as separate achievements.
