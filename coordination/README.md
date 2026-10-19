# Local coordination state

Run `python scripts/session.py status` to inspect the active coordinator,
worker claims and latest handoff. Its JSON export appears here as `status.json`.
SQLite transactions in `.autortl/coordination.sqlite3` are the local authority.
Both runtime files are ignored by Git. Read START_HERE.md and the checked-in
handoff/task board on a fresh clone, then claim a new local session.
