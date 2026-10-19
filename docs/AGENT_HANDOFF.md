# Shared memory and coordinator handoff

Use files and Git as the durable memory. A chat summary can help, but does not
replace source code, test results or experiment artifacts.

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
