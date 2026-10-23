# AutoRTL shared project memory

This repository is the shared workspace for every coordinator and its workers.
You can continue without access to the previous provider's conversation.

Canonical checkout: `C:/Users/prince.baah/Downloads/autortl-work`.
GitHub integration branch: `main`. Development branch: `codex/contract-context`.
Current verified checkpoint: **1,105 regression tests passed**.
FIFO05 recovered timing at22 LUTs/13 FFs, setup0.108 ns/hold0.076 ns; exact
saved winner passed independent verification and327-identity DONE checks.
Fresh fulltier0 campaign07 passed2/2: counter55→31 LUTs, mux baseline retained.
No held tier or controlled weak-model result is claimed. Earlier failed trials
remain archived. Main and development were integrated at141c548. Packet-tag FIFO admission now passed20/20 expected verdicts across six
configurations. Generated packet01 recovered timing at23 LUTs/31 FFs,+.078/.106ns; exact
savedwinner and331-identity DONE checks passed. Inspect current Git and SESSION_HANDOFF.
Measured runtime85e4fb8/6f3fa7c is unchanged by documentation/evidence commits.

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
