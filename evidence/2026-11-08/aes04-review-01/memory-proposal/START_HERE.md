# AutoRTL: start here

Canonical checkout: `C:/Users/prince.baah/Downloads/autortl-work`.
`Downloads/autortl` is a separate copy. User choice: command-line Vivado.

**The sole current checkpoint is [docs/SESSION_HANDOFF.md](docs/SESSION_HANDOFF.md).**
Read its dated state and exact next action; do not infer live work from older
chat summaries, mailbox requests or progress entries. This entry guide was
prepared November 8, 2026; its linked checkpoint must be reconciled at each
meaningful milestone rather than prepending another "current" section here.

## Arrive or recover context

1. Read `AGENTS.md`, `docs/AGENT_HANDOFF.md`, `docs/SESSION_HANDOFF.md`,
   `CLAUDE.md`, `docs/DESIGN.md` and relevant recent `docs/PROGRESS.md` entries.
   Consult `docs/ACTION_PLAN.md` for the finite release plan and `docs/RESEARCH.md`
   before substantial harness design changes.
2. Inspect Git branch/HEAD, dirty and untracked files, actual jobs and saved
   results. Query live ownership with `python scripts/session.py status`;
   display only coordinator, active tasks and latest checkpoint. Read
   `python coordination/mail.py inbox --for codex` (or `claude`), but reconcile
   old requests against the current checkpoint and later user decisions.
3. Coordinators take turns. If another coordinator is active, stay read-only;
   its own bounded workers may use nonoverlapping claimed scopes. Follow
   `docs/AGENT_HANDOFF.md` before claiming or recovering ownership. An expired
   lease does not prove tool jobs stopped. Never displace an active coordinator
   merely because another model is available. Never publish a session token.
4. Preserve unfinished files and immutable attempts. Do not automatically pull,
   reset, clean, stash, switch branches, terminate unfamiliar jobs or replay old
   patches. Do not edit frozen experiment inputs or duplicate an existing job.

## Continue and leave an honest checkpoint

One coordinator owns integration and the vendor queue. Verify source identity,
raw results and original budgets before acting; an outer launcher exit is not
a design verdict. Never weaken a contract, verifier, sandbox or metric gate.
Do not resume a spent attempt across runtime changes.

Push meaningful tested milestones to development. **Main stays frozen until
the final release validation/re-hold gate passes.** Completed lower tiers are
not repeatedly re-held during development; see `docs/ACTION_PLAN.md`.
The connected FPGA is not authorization for board access: this stage includes
no JTAG, serial, programming, flash, reset or hardware-server operation.

Replace the checkpoint's current state after meaningful progress, recording
commit, scopes, actual jobs, tests, evidence, failures and exact next action.
Append history to `docs/PROGRESS.md`; keep immutable evidence under `evidence/`
and preserve source/result hashes per `docs/PUBLICATION.md`. Keep the public
README focused on the project and verified results. Checkpointing retains
ownership; use `handoff` only when actually ending or switching coordinators.
These files support recovery; they do not schedule execution or provider swaps.
