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

- They merge only after final-02 finishes (flash-02 was later withdrawn), so no registered
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

## 2026-11-21 — Request cross-check: built behind a switch, off by default

Taxonomy `planner_spec_error_shared_by_oracle_and_rtl` caused most of the
final-02 gap between the harness and a single model call. v1.1 adds
`spec_cross_check` (DESIGN.md "Request cross-check"): an independent role call
writes cycle traces from the original request and the port list only, the
harness runs them through the planner spec's qualified golden model, and a
disagreement replans once from the shared `max_fix_attempts` counter.

- **Default `off`.** ROADMAP V1 already fixed the rule: off until measured, and
  the default changes only if false acceptances fall without blocking correct
  designs. The check is untested live; every final-02 task counts as tuned, so
  its effect can only be measured on fresh tasks, and the trace writer can
  misread the request too. `request_traces` is one flag away for that
  measurement, and both settings are recorded as benchmark arms.
- **Traces, not "examples".** The spec's examples hold constant inputs from
  reset, which cannot express the observed failures (a reset that should not
  clear an edge register; an input sampled one cycle early). Short traces with
  per-row inputs, written in physical cycles independent of the planner's
  latency, can. Comparing them in the generated testbench's own observation
  phase makes a latency misreading visible.
- **Second derivation reaches only the oracle.** It runs after oracle
  qualification and before RTL generation, so a disagreement costs no
  generator calls, and nothing derived from the trace writer enters the spec
  except through the planner.
- **Never fails a design itself.** A disagreement makes the planner re-read the
  quoted request once; the planner may keep its spec. A second disagreement is
  recorded (`disagreement_kept`) and the build continues. Turning an unverified
  second reading into a gate would trade false acceptances for false
  rejections of correct designs; whether to gate is a later, measured decision.
- **Interface is shared.** The writer sees the planner's port list (names are
  needed to write traces). The behavioral reading stays independent; an
  interface misreading is outside this check.
- **Benchmark wiring is separate.** `benchmark/pilot.py` (edited by another
  session) does not set the field, so registered arms keep v1.0.0 behaviour
  until a new registration names it.

## 2026-11-25 — flash-03: closed-book Flash-low single call, registered before any cell

A second model on arm A, done properly this time: Gemini 3.8 Flash-low through
the guarded bridge (tool-using replies refused and counted as failures), the
same 40 tasks and 120 single-call cells as `flash-01`, runtime `1c341f798`.
Registration: `evidence/2026-11-25/flash-03-registration-02`, which
supersedes `-01` (re-frozen the same evening, before any cell ran, on runtime
`202a6daa6`). A trivial Flash-low call took 105 to 138 s even on an idle host:
the Antigravity CLI updated that day lingers about 100 s after its result and
the bridge waited for it (`agy_exits_late_after_result`); the fixed bridge
returns at the result in 6 s. Only the runtime commit changed. The comparison
with `final-02` arm A is descriptive (different model, different week), never
a harness claim. The run starts once a trivial probe answers within 30 s, so
timeouts measure the model, not the CLI. Harness arms with Flash need their
own registration later, when Vivado time is free.

## DRAFT, awaiting the owner's approval — Decision rule for the optimisation benchmark (B3)

Not in force. Proposed November 21, 2026 with `docs/B3_REGISTRATION_DRAFT.md`.
No B3 trial exists. The owner freezes the registration (tasks, model, budgets,
flow) and this rule together, before any trial; the date of freezing replaces
"DRAFT" in this heading. Implemented as `benchmark/ppa_report.decide`, whose
constants are these thresholds.

- **Question:** on designs that both arms get functionally right, does the
  harness with optimisation (arm C-opt) give smaller routed designs than a
  single model call (arm A)?
- **Functional gate first:** a cell enters PPA only if its sealed submission
  passes the official testbench (upstream-compatible verdict). Failing designs
  have no area. A task is compared only when each arm has at least one passing
  trial.
- **Primary endpoint:** routed LUTs from `benchmark/ppa.py` (out of context,
  xc7a35tcpg236-1, 10 ns, the harness's OOC template, one Vivado version for
  every cell; the report refuses mixed flows).
- **Primary comparison:** geometric-mean LUT ratio C-opt / A over tasks
  measured in both arms. Per task and arm, the geometric mean of (LUT + 1) over
  passing trials; 95% task-clustered bootstrap interval (10,000 resamples,
  seed 20261115).
- **Verdict:** interval below 1 → `harness_smaller`; above 1 →
  `single_call_smaller`; inside [1/1.10, 1.10] → `no_material_difference`;
  otherwise `inconclusive`. Fewer than 10 tasks measured in both arms →
  `insufficient_pairs` (descriptive only).
- **Completeness:** more than 10% of an arm's cells stopped by infrastructure
  downgrades the verdict to `inconclusive`. Infrastructure failures of PPA
  synthesis write no record and are retried; the report refuses until every
  passing cell has a sealed record.
- **Timing (secondary):** share of passing trials that meet setup and hold at
  10 ns, paired difference C-opt minus A with the same bootstrap, read with
  the final comparison's ±10 pp rule. A passing design that fails synthesis
  counts as not closed and is named.
- **Always reported:** FF ratio and WNS difference (descriptive), per-task
  ratios, functional pass counts per arm, tasks without a functional pair,
  model calls and tool time per arm.
- **Not allowed:** removing tasks or cells after the first trial, rerunning a
  cell, changing the flow, part, period or a threshold after grading. The
  candidate tasks were chosen from final-02 results, so the claim names that
  selection and is not a fresh functional comparison.

## Continuing contracts

Use command-line Vivado. Specifications and independent verification control
acceptance. Infrastructure failures never justify changing RTL or claiming
design progress. Keep matching source, constraints and report evidence. Record
build correctness and optimization improvement as separate achievements.
