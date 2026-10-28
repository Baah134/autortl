# Local coordination state

Run `python scripts/session.py status` to inspect the active coordinator,
worker claims and latest handoff. Its JSON export appears here as `status.json`.
SQLite transactions in `.autortl/coordination.sqlite3` are the local authority.
Both runtime files are ignored by Git. Read START_HERE.md and the checked-in
handoff/task board on a fresh clone, then claim a new local session.

## Messages between agents

The lease says who may edit. `mail.py` carries what agents need to tell each
other: questions, requests, answers and blockers that must survive a handoff.
`messages.jsonl` is committed with the work, so it also survives a fresh clone.
Posting needs no lease, so a waiting agent can ask the active one a question
without editing anything else. Names are lowercase: `codex`, `claude`, `user`,
or `any` as a recipient.

```powershell
python coordination/mail.py inbox --for claude
python coordination/mail.py post --from claude --to codex --kind request `
  --subject "Review Basys 3 bring-up" --body "Evidence in evidence/2026-10-28/..."
python coordination/mail.py post --from codex --to claude --kind answer `
  --reply-to 1 --subject "Re: Review" --body "Reviewed; one fix requested"
python coordination/mail.py close --id 1 --by codex --resolution "Reviewed in a1b2c3d"
```

Kinds: `note`, `question`, `request`, `answer`, `blocker`. Close a message only
when it is resolved, with a resolution that names the evidence or commit.
Messages are pointers and requests, not proof: verify claims against files,
Git and tool results. Never post lease tokens or credentials. A message that
contains the live lease token is rejected, and if the lease database cannot be
read, posting stops rather than skipping that check.

The log is append-only. A corrupt line, an incomplete record or a duplicate
message id stops every command until it is repaired; a duplicate id usually
means two branches each appended the next id, so renumber one post and its
replies. A UTF-8 BOM is tolerated, and output never fails on a legacy console
code page. Tests use the fixture logs in `fixtures/`:
`python -m pytest coordination -q`.

Posting is the only write allowed while another coordinator holds the lease
(see AGENTS.md). Leave the log uncommitted in that case.

This tool and its log live outside the frozen harness source sets, so posting
or changing them does not alter experiment identities.
