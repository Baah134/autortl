# AutoRTL shared project memory

This repository is the shared workspace for every coordinator and its workers.
You can continue without access to the previous provider's conversation.

Canonical checkout: `C:/Users/prince.baah/Downloads/autortl-work`.
GitHub integration branch: `main`. Development branch: `codex/contract-context`.
Current development checkpoint: **1,074 passing regression tests**. Recovery
guards, bounded path/spec evidence, not-adopted Doctor feedback and proven no-op
deduplication are tested. FIFO02/03 exhausted their original budgets and remain
archived. FIFO04 exposed a false latency-annotation rejection despite routed
timing closure; its rejection remains preserved. Latency correction is tested
and ready for publication; fresh FIFO05 and fulltier0 are next (SESSION_HANDOFF).
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
