# Shared memory and coordinator handoff

Use files and Git as the durable memory. A chat summary can help, but does not
replace source code, test results or experiment artifacts.

## Arrival checklist for alternating agents

User decision, October 28: development coordinators take turns. Keep the existing
single-coordinator protocol; independent concurrent worker sessions were considered
but not implemented. The current coordinator may still use its own scoped subagents.

1. Read START_HERE, AGENTS, this guide, the current SESSION_HANDOFF section and
   relevant recent PROGRESS entries. Inspect branch, commit, index and untracked
   files. Existing unfinished work belongs to the project; do not discard it.
2. Query the database through the CLI, not only its previously saved JSON export.
   A compact PowerShell view avoids loading the entire event history:

   ```powershell
   $ownership = python scripts/session.py status | ConvertFrom-Json
   if ($LASTEXITCODE -ne 0) { throw "Coordination status failed; do not edit" }
   $ownership.coordinator | Format-List
   $ownership.tasks | Where-Object { $_.state -ne 'done' } | Select-Object id,state,owner,files
   $ownership.checkpoint | Format-List
   ```

3. If another coordinator is active, remain read-only. Do not use
   `--takeover-reason` merely because another model is available. If its session
   ended abruptly, verify cessation or obtain an explicit user takeover request,
   following the existing takeover rule below. A session token is private: never
   put it in Git, progress files or exported logs.
4. Even with a released/expired lease, inspect owned model/vendor jobs and
   experiment events. A stale RUNNING record is not a live process or a successful
   exit. Do not terminate unfamiliar processes. If a job is still active, preserve
   its source and wait for its result before changing measured inputs.
5. Start a lease without a takeover flag when eligible; a claim conflict means
   another coordinator won the race, so stop editing. Reclaim only the required
   unfinished task scopes. Never infer that blocked tasks are completed or that
   their files are disposable.
6. Reconcile old checkpoint instructions against actual results. Preserve each
   attempt and its original budgets; do not relaunch a spent experiment into its
   old output directory or resume it across changed runtime identities. An
   interrupted experiment needs an evidence/recovery decision before continuation.
7. Read open messages addressed to you or `any`:
   `python coordination/mail.py inbox --for codex` (or `claude`). Answer with
   `--reply-to`, and close each one only when resolved, naming the evidence.

## Messages between agents

The lease and checkpoint record who owns the work and its latest state; each
checkpoint replaces the previous one. Questions, review requests and blockers
addressed to the other agent go in `coordination/messages.jsonl` through
`coordination/mail.py`, which keeps them open until a party closes them.
Posting needs no lease: it is the one write a waiting agent may make, and that
agent leaves the log uncommitted. The active coordinator commits the log with its
work so it survives a fresh clone. A message is a
pointer, not proof: check files, Git and tool results before acting on it.
Details and examples are in `coordination/README.md`.

Do not automatically pull, switch branches, stash, reset or clean on arrival.
Review existing work and remote changes first. Stage explicit reviewed paths;
avoid `git add .` when unrelated unfinished evidence is present. Only the active
coordinator integrates and pushes tested changes or owns the Vivado job queue.

## Departure record

At a real switch/end, update the current SESSION_HANDOFF with branch/commit,
pending tracked/untracked paths, completed checks and their evidence, failures,
live job identities and output paths, and the next executable action. Distinguish
confirmed running jobs from stale session IDs. Keep historical results in PROGRESS
and put local coordination notes here, never in the public README.

Save work before releasing ownership. Run the existing `handoff` command below;
the next agent gets its own token and explicitly reclaims unfinished scopes.
Do not hand off merely to save an intermediate checkpoint. Abrupt usage limits
may prevent release: the next agent still checks actual jobs and lease state.
These files do not schedule execution or automatically switch model providers.

## One coordinator, several workers

The active coordinator owns the integration plan and the Vivado job queue.
It can assign its own subagents separate files. Workers report changes, tests,
failures and remaining work. They cannot silently change another worker's scope.
Only one implementation job uses Vivado at a time on this machine.

`scripts/session.py` uses SQLite transactions for coordinator leases and task
claims, so two processes cannot both claim the same active ownership. A readable
snapshot is exported to `coordination/status.json`. The lease is a cooperation
protocol, not an operating-system security boundary: every agent must follow it.

Start a session in PowerShell from the canonical checkout:

```powershell
$session = python scripts/session.py start --owner "Claude coordinator" | ConvertFrom-Json
$sessionToken = $session.token
python scripts/session.py claim-task --token $sessionToken --id resume --title "Complete interruption recovery" --owner "Claude/resume-worker" --files autortl/fsm.py tests/test_fsm_resume.py
```

Claim exact files or directory scopes; wildcard scopes are rejected. Overlapping
active scopes are rejected, including directory/file and case differences.
Renew the lease during work, normally at each substantial checkpoint:

Saving a checkpoint keeps the coordinator active. The user wants continuous
work while usage is available, then another available provider can continue.
Release ownership only when actually ending or switching sessions. If usage
ends abruptly, preserve files and let the next coordinator reconcile Git,
running processes and lease status before taking over. Returning coordinators
read the latest repository state rather than assuming their old plan is current.

```powershell
python scripts/session.py renew --token $sessionToken
python scripts/session.py checkpoint --token $sessionToken --summary "Resume tests now pass" --next "Run counter integration campaign" --test "pytest tests/test_fsm_resume.py: 12 passed"
```

Mark a task done only with concrete evidence:

```powershell
python scripts/session.py update-task --token $sessionToken --id resume --owner "Claude/resume-worker" --state done --detail "Reviewed and integrated" --evidence "test log and commit reference"
```

## Before switching providers or ending a session

1. Stop assigning new work and collect every worker's saved changes and status.
2. Finish or stop tool jobs cleanly. Record any process still running.
3. Inspect the full diff. Test changes and document failures as failures.
4. Update SESSION_HANDOFF, TASKS and PROGRESS. Record exact commands, source
   branch/commit, pending files, blockers, and the next executable action.
   Post open requests or blockers for the next agent with `coordination/mail.py`.
5. Commit and push tested milestones to the development branch. Preserve
   unfinished work clearly; do not call it complete merely to make a commit.
6. Release the lease with a handoff:

```powershell
python scripts/session.py handoff --token $sessionToken --summary "What was completed and what remains" --next "Exact next command or repair" --test "Commands and actual outcomes"
```

Handoff leaves unfinished claims blocked so the next coordinator must reclaim
them. A released or expired lease can be claimed normally. If a previous agent
stopped unexpectedly while its lease remains active, the next coordinator may
use `start --takeover-reason "..."` only after verifying the previous session
and tools have stopped or the user explicitly requested takeover. The reason is
recorded; this is not permission to displace a concurrently working coordinator.

## What each file means

| Record | Purpose |
|---|---|
| SESSION_HANDOFF.md | Current state, outstanding changes, exact next actions |
| TASKS.md | Durable task board, acceptance criteria and dependencies |
| DECISIONS.md | Why architectural/user decisions were made |
| PROGRESS.md | Append-only engineering and CV evidence log |
| coordination/status.json | Live local coordinator, worker claims and checkpoint |
| Run config/state/events/reports | Machine evidence for individual experiments |
| Git commits and remote branch | Reviewed implementation history and shared backup |

Runtime run checkpoints and development handoffs are different records. A
development agent can resume engineering from this memory even while an
interrupted hardware experiment still needs a harness repair.

## Provider independence

Codex, Claude, Gemini and other user-authorized coordinators follow the same
contract. A coordinator may use its own workers to play planner, implementation,
verification and review roles. The harness currently invokes Codex CLI for its
runtime model calls. Changing the runtime backend requires its own tested
integration and available credentials; changing the coordinator does not by
itself change runtime routing.

Git cannot schedule agent switches or overcome provider usage limits. The user
starts the next available provider in this folder and directs it to START_HERE.
No background scheduler or automatic cross-provider failover is configured.

## Recovery after context compaction

The same resume procedure applies after automatic compaction within one chat.
A compacted summary is not a passing-test receipt or publication record.
Recover current state from START_HERE, the active section of SESSION_HANDOFF,
relevant recent PROGRESS entries, Git, coordination and actual job/result files.
Verify the measured source and scope before reusing a result. Read historical
entries selectively with rg rather than loading the complete log every time.

Minimum checkpoint: source commit/branch, worker scopes, live jobs, completed
test/result paths, unresolved failures, next exact command and immutable budget.
Model context compaction is supplied by the host; no custom app/API threshold
has been configured by this repository's session-coordination files.
