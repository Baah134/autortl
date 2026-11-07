# AutoRTL shared project memory

This repository is the shared workspace for every coordinator and its workers.
You can continue without access to the previous provider's conversation.

Canonical checkout: `C:/Users/prince.baah/Downloads/autortl-work`.
GitHub integration branch: `main`. Development branch: `codex/contract-context`.
Current checkpoint: **November6, release plan and final sign-off supervision**.
Read docs/SESSION_HANDOFF.md and query live ownership before editing. Base
e61665c5; last checked remote main ca61dbc. The prior October29 patches are
already integrated; do not replay stale staged changes.

Twelve harness-built designs have recorded Basys3 verification. Current full
records hold tiers0–5; tier3 includes a recurring UART/FIFO failure. Tier6's
first attempt passed2/3 and failed AES oracle generation. An existing signoff4
process is running tier6-02; preserve all334 frozen inputs and original budgets.
A held tier is an80% curriculum criterion, not a claim every entry passed.

The finite release plan is docs/ACTION_PLAN.md: close the current sign-off,
resolve demonstrated reliability gaps, freeze a release candidate, measure
a public-task comparison and publish a reproducible CV/engineering package.
Finished tiers are not repeatedly re-held during development; the final pass
is the release gate. Full public-benchmark superiority is not yet established.

**Agents take turns.** Before editing, check live coordinator ownership and
actual jobs using the arrival checklist in `docs/AGENT_HANDOFF.md`. An active
coordinator keeps ownership; a returning agent must not overwrite newer work.

1. Read `AGENTS.md` and `docs/AGENT_HANDOFF.md` for the working contract.
2. Read `docs/SESSION_HANDOFF.md` for current state and exact next actions.
3. Inspect `git status --short`, recent commits, and `python scripts/session.py status`.
   Read messages for you: `python coordination/mail.py inbox --for <codex|claude>`.
4. Claim the coordinator lease. Respect existing worker file ownership.
5. Read `docs/DECISIONS.md`, `docs/TASKS.md`, `docs/DESIGN.md` and
   `docs/RESEARCH.md` before substantial harness changes.
6. Implement, test, review, and retain evidence. Follow `docs/PUBLICATION.md`
   before declaring archives published. Update shared memory and push
   tested progress. Before switching providers, run the handoff command.

The coordination database in `.autortl/` is local, transactional working state.
`coordination/status.json` is its readable export. Both are machine state, not
Git history. The checked-in handoff, task board, decisions, and test evidence
survive a fresh clone. On another computer, start a new coordinator lease and
reconstruct task ownership from the checked-in handoff.

Checkpointing does not stop the active coordinator or release its lease. Keep
working while usage is available; switch only when necessary. Read the handoff
and test results before starting unattended design campaigns.
