# AutoRTL shared project memory

This repository is the shared workspace for every coordinator and its workers.
You can continue without access to the previous provider's conversation.

Canonical checkout: `C:/Users/prince.baah/Downloads/autortl-work`.
GitHub integration branch: `main`. The completed `codex/cli-bringup` checkpoint
has been merged. Start new development branches from the current remote main.

1. Read `AGENTS.md` and `docs/AGENT_HANDOFF.md` for the working contract.
2. Read `docs/SESSION_HANDOFF.md` for current state and exact next actions.
3. Inspect `git status --short`, recent commits, and `python scripts/session.py status`.
4. Claim the coordinator lease. Respect existing worker file ownership.
5. Read `docs/DECISIONS.md`, `docs/TASKS.md`, and `docs/DESIGN.md` before changes.
6. Implement, test, review, and retain evidence. Update shared memory and push
   tested progress. Before switching providers, run the handoff command.

The coordination database in `.autortl/` is local, transactional working state.
`coordination/status.json` is its readable export. Both are machine state, not
Git history. The checked-in handoff, task board, decisions, and test evidence
survive a fresh clone. On another computer, start a new coordinator lease and
reconstruct task ownership from the checked-in handoff.

Checkpointing does not stop the active coordinator or release its lease. Keep
working while usage is available; switch only when necessary. Read the handoff
and test results before starting unattended design campaigns.
