# AutoRTL shared project memory

This repository is the shared workspace for every coordinator and its workers.
You can continue without access to the previous provider's conversation.

Canonical checkout: `C:/Users/prince.baah/Downloads/autortl-work`.
GitHub integration branch: `main`. Development branch: `codex/contract-context`.
Current development checkpoint: **1,074 passing regression tests**.
FIFO05 completed accepted timing recovery:22 LUTs/13 FFs, setup0.108 ns,
hold0.076 ns. Exact saved winner passed the independent matrix; actual DONE
reuse and restored tamper checks retained327 identities and the original budget.
Fresh complete tier0 campaign07 is running; see SESSION_HANDOFF.
Earlier FIFO02/03 budget failures and FIFO04 false rejection remain archived.
Main remains **7bef3bf** pending those gates. Prior source49599b5 passed939tests;
fixtureffc15fc passed836tests/FIFO14of14admission; FIFO01 failed timing.
Prior runtime8098466 passed fulltier0; archives retain their measured source.
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
