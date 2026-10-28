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

## Continuing contracts

Use command-line Vivado. Specifications and independent verification control
acceptance. Infrastructure failures never justify changing RTL or claiming
design progress. Keep matching source, constraints and report evidence. Record
build correctness and optimization improvement as separate achievements.
