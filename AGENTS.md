# AutoRTL session continuity

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
