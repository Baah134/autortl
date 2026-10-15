# AutoRTL session continuity

At the start of every session, read `docs/SESSION_HANDOFF.md`,
`docs/PROGRESS.md`, `CLAUDE.md`, and `docs/DESIGN.md`. Inspect the current
Git branch, status, and recent commits before editing. Reconcile these
records with actual files and tool results; documentation is not proof.

Current user choice: command-line Vivado. MCP integration is deferred.

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
