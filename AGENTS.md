# AutoRTL session continuity

## Agent arrival and departure (user decision, October 28)

Codex, Claude Code and other user-authorized development agents **take turns**.
An active coordinator is not an invitation to start a second editing session.
Read `docs/AGENT_HANDOFF.md` for the arrival checks and departure procedure.

- Query live ownership with `python scripts/session.py status`; the checked-in
  handoff and an old JSON export can be stale. If another coordinator is active,
  stay read-only until it hands off. Do not use takeover just to avoid waiting.
- A released or expired lease is not proof that tool jobs have stopped. Inspect
  Git, unfinished changes, actual processes and saved run evidence before claim.
- Preserve dirty files and untracked artifacts. Do not reset, clean, stash,
  switch branches or resume experiments merely to make the checkout look tidy.
- Claim the coordinator lease and exact file scopes before editing. Renew at
  substantial checkpoints; a normal checkpoint keeps ownership active.
- On an actual departure, record pending work and live jobs, then run `handoff`.
  A returning agent starts from the latest repository state, not its old chat.
- Read your messages on arrival with `python coordination/mail.py inbox --for
  <codex|claude>`. Before leaving, post open requests and blockers for the next
  agent and close messages you resolved. See `coordination/README.md`.
- The one exception to staying read-only while another coordinator is active:
  you may run `coordination/mail.py post` and `close`, which only append to
  `coordination/messages.jsonl`. Do not stage or commit that file then; the
  active coordinator commits it with its next change.

At the start of every session, read `START_HERE.md`, `docs/AGENT_HANDOFF.md`, `docs/SESSION_HANDOFF.md`,
`docs/PROGRESS.md`, `CLAUDE.md`, and `docs/DESIGN.md`. Inspect the current
Git branch, status, and recent commits before editing. Reconcile these
records with actual files and tool results; documentation is not proof.

Current user choice: command-line Vivado. MCP integration is deferred.
The user authorizes different AI coordinators (Codex, Claude, Gemini or another
user-selected agent) to take turns, each with its own bounded subagents.
Claim the coordinator lease and explicit worker file scopes with
`scripts/session.py` before edits. One coordinator leads at a time; workers
must not edit overlapping scopes. Read the previous checkpoint and inspect Git
status before assuming unfinished changes are yours. The runtime LLM client is
currently configured for Codex; do not assume another provider's API is available
just because that provider is coordinating the development session.

The coordinator reviews worker changes and checks evidence before continuing.
When a tested milestone is ready, commit and push the development branch as
authorized by the user. The user also requested integrating the completed CLI
checkpoint into main on 2026-10-19; see docs/DECISIONS.md for its validation and
remaining experiment gaps. Push meaningful progress, not artificial activity.
Do not merge failed or incomplete work into main. Record the remote commit in
the handoff. Keep source and test evidence honest even when an agent changes.

Keep the existing contract and verification requirements in CLAUDE.md.
Never count infrastructure failures as design failures or successful tests.
Never weaken a test, specification, or metric gate to claim improvement.

Before ending a session, and after meaningful milestones:

- Update SESSION_HANDOFF with completed work, exact next action, blockers,
  branch, unfinished changes, and locations of evidence.
- Append PROGRESS with human decisions, AI-assisted changes, commands and
  outcomes, and limits of the evidence. Distinguish prior tests from new work.
- Preserve source-to-result traceability: commit/source hash, constraints,
  device, tool version, testbench, and baseline/winner reports.
- Do not record credentials or claim unmeasured CV improvements.

Chat memory is supplementary. These files and Git history are the durable
handoff. They do not schedule execution or guarantee experiment resumption;
the harness's interruption/resume behavior must itself be repaired and tested.

Canonical local checkout: `C:/Users/prince.baah/Downloads/autortl-work`.
`Downloads/autortl` is a separate preexisting copy; do not edit it by accident.

The root README is the public project overview: purpose, usage and concise
verified results. Keep coordinator messages, local paths, handoff instructions,
branch/session status and quotas in START_HERE or docs/AGENT_HANDOFF.md,
docs/SESSION_HANDOFF.md and docs/PROGRESS.md instead.

## Research-informed changes

The user requests ongoing study of comparable agentic systems and research.
Read docs/RESEARCH.md before substantial harness design changes. Consult primary
sources, map an idea to an observed AutoRTL need, and compare it against a
simpler existing approach. Add complexity only with a concrete justification,
tests and a measurable experiment; record keep/revise/remove decisions. Do not
add roles, memory stores or frameworks solely because another system uses them.

## Context compaction and recovery

Compaction summaries and chat memory are working aids. Files, Git and actual
tool evidence establish project state. Do not invent or assume a compaction
threshold, completed test, running process, source identity or published commit.

At each meaningful stage boundary, checkpoint: current branch/commit; claimed
files; live process/session IDs; last completed tests and their exact scope;
accepted/rejected measurements with artifact paths; remaining work and the next
command with its original budget. Keep current state in SESSION_HANDOFF and
append history to PROGRESS. Do not place coordinator notes in the public README.

After compaction, interruption or suspected context loss, re-read START_HERE,
the current SESSION_HANDOFF section and the latest relevant PROGRESS entries.
Inspect actual Git status/heads, coordinator ownership and running jobs. Check
the cited result JSON, raw verdicts and hashes before continuing or reporting
success. Resolve contradictions against files and tool results; mark unverified
claims unknown. Never rerun/resume a spent experiment across runtime changes.

Keep reads bounded: use rg and relevant sections/tails to recover history.
Retrieve full code or logs when necessary for the current edit or diagnosis;
do not repeatedly load the entire accumulated progress log into conversation.
These rules reduce context drift; they do not guarantee error-free reasoning.
