# AutoRTL — guide for every coding agent

One guide for Codex, Claude, Gemini or any agent the owner starts in this
checkout. What to do next is in [docs/ROADMAP.md](docs/ROADMAP.md); where things
stand is in [docs/SESSION_HANDOFF.md](docs/SESSION_HANDOFF.md); why the system
is built this way is in [docs/DESIGN.md](docs/DESIGN.md). Files, Git and tool
results are the memory of this project; chat summaries are not.

## Hard rules

1. **Spec is law.** Generated code never changes a contract's interface or
   latency; a mismatch is a failure, not a negotiation.
2. **Model output lands only in `.v`, `.py` and spec JSON files.** Never
   interpolate model text into TCL, shell commands or paths.
3. **Vivado message severities are promoted only**, never demoted or hidden.
4. **Infrastructure failures** (locks, licences, quota, timeouts, tool crashes)
   never mutate a design, never enter history, never count as fix attempts or
   design verdicts.
5. **Every parser has a pytest with a fixture file. Every new failure mode gets
   a `data/taxonomy.yaml` entry before its fix.**
6. **Never weaken a test, contract, verifier or metric gate to pass.** Report
   the result you got. Never invent a result, a running job or a commit.
7. **A spent experiment is never rerun or edited.** Fix, commit, freeze a new
   manifest, use a new attempt directory, record the old one as aborted.
8. **No board access** (JTAG, programming, serial, hardware server) without the
   owner's explicit authorisation for that task.
9. **No credentials, tokens or home-directory paths in committed files.**

## Arriving

1. Read this file, `docs/SESSION_HANDOFF.md` and `docs/ROADMAP.md`.
2. Inspect before touching: `git status`, `git log --oneline -5`, running
   Vivado/model/benchmark processes, and ownership:

   ```bash
   python scripts/session.py status          # coordinator, tasks, last checkpoint
   python coordination/mail.py inbox --for <codex|claude>
   ```

3. Coordinators take turns. If another coordinator is **active**, stay
   read-only (you may still post or close mailbox messages). An expired lease
   does not prove its jobs stopped: check processes and unfinished files.
4. Preserve what you find. Do not reset, clean, stash, switch branches, pull,
   kill unfamiliar jobs or delete untracked artifacts to tidy up.

## Working

- Claim the lease, then exact file scopes (no wildcards; overlaps are refused):

  ```bash
  python scripts/session.py start --owner "<agent / purpose>"      # prints a private token
  python scripts/session.py claim-task --token <T> --id <id> --title "<what>" --owner "<who>" --files <paths...>
  python scripts/lease_keeper.py --token-file <private file>       # renews every 10 min
  python scripts/session.py checkpoint --token <T> --summary "..." --next "..." --test "..."
  ```

  The lease lasts about an hour and lapses if the machine sleeps; after a
  lapse, check `status` shows no other owner, `start` again and re-claim.
  Use `start --takeover-reason` only when the owner asks or you have verified
  the previous session and its tools have stopped.
- One coordinator integrates and owns the Vivado queue (one implementation job
  at a time). Its own subagents may work in parallel on non-overlapping
  scopes; code-writing subagents use a git worktree created at the working
  commit (`git worktree add .claude/worktrees/<name> -b <name> <commit>`) and
  the coordinator reviews and merges.
- **While a benchmark campaign runs, do not edit `autortl/`, `llm/`, `data/`,
  `.claude/skills/`, `run.py`, `benchmark/pilot.py` or
  `benchmark/verilogeval.py`**: every cell records the runtime it launched.
- Before substantial harness design changes read `docs/RESEARCH.md`; add
  complexity only for an observed need, with tests and a measurement.
- Tests before commit: focused tests, then the full suites (commands in
  ROADMAP section 3). Stage explicit paths, never `git add .`. Pushing, PRs
  and merges to `main` need the owner's approval. `main` stays frozen until
  the release gate.
- Completed curriculum tiers are not re-held during development; the final
  release identity is re-held once at the end.
- Evidence goes in `evidence/<date>/<name>/` with a README, raw data and
  `archive-manifest.json`; `python tools/evidence_audit.py --rev HEAD` must
  pass. See `docs/PUBLICATION.md`.

## Leaving

At a meaningful milestone, checkpoint (it keeps the lease). When actually
stopping or switching agents:

1. Stop assigning work; finish or cleanly stop tool jobs; record anything
   still running.
2. Inspect the full diff; test; describe failures as failures.
3. Replace the single `## Current` section of `docs/SESSION_HANDOFF.md`
   (branch, commit, what is running, exact next action, open decisions).
   Append history to `docs/PROGRESS.md`. Update task status in
   `docs/ROADMAP.md`.
4. Commit tested work; leave unfinished work clearly marked, not called done.
5. Post open requests for the next agent with `coordination/mail.py post`,
   then release:

   ```bash
   python scripts/session.py handoff --token <T> --summary "..." --next "..." --test "..."
   ```

## After context loss or compaction

Re-read the three files above, then verify against Git, `session.py status`,
running jobs and the cited result files before continuing or reporting
success. Mark anything unverified as unknown.

## Records

| Record | Purpose |
|---|---|
| `docs/ROADMAP.md` | Tasks, order, commands, acceptance criteria |
| `docs/SESSION_HANDOFF.md` | The one current checkpoint |
| `docs/PROGRESS.md` | Append-only engineering history |
| `docs/DECISIONS.md` | Why architectural and owner decisions were made |
| `docs/DESIGN.md` | Architecture (single source of truth) |
| `data/taxonomy.yaml` | Vivado message IDs and recorded failure modes |
| `coordination/` | Lease database export and the agent mailbox |
| `docs/archive/` | Superseded plans and history |

The runtime model backend is configured in `llm/routing.yaml` and by `--model`;
changing the coordinating agent does not change it. Nothing here schedules
work or switches providers automatically.
