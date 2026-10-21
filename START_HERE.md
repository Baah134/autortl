# AutoRTL shared project memory

This repository is the shared workspace for every coordinator and its workers.
You can continue without access to the previous provider's conversation.

Canonical checkout: `C:/Users/prince.baah/Downloads/autortl-work`.
GitHub integration branch: `main`. Development branch: `codex/contract-context`.
Current development checkpoint: **939 passing regression tests**, FIFO recovery
policy/context/repair and completed child-source integrity guards. Fresh FIFO02
and full tier0 validation are next; main remains at **7bef3bf** pending those
gates. Prior fixture source **ffc15fc** passed 836 tests and FIFO admission14/14;
its FIFO01 failed timing and is preserved. Prior runtime8098466 passed fulltier0.
Inspect actual heads, status and SESSION_HANDOFF before editing or switching.

1. Read `AGENTS.md` and `docs/AGENT_HANDOFF.md` for the working contract.
2. Read `docs/SESSION_HANDOFF.md` for current state and exact next actions.
3. Inspect `git status --short`, recent commits, and `python scripts/session.py status`.
4. Claim the coordinator lease. Respect existing worker file ownership.
5. Read `docs/DECISIONS.md`, `docs/TASKS.md`, `docs/DESIGN.md` and
   `docs/RESEARCH.md` before substantial harness changes.
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
