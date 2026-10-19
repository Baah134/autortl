"""Local, transactional handoffs for independent AI coordinators and workers.

SQLite owns the active lease and task claims. The JSON export is readable
shared memory, not the lock itself. Git history owns implementation history.
"""
from __future__ import annotations
from contextlib import contextmanager, closing
import json
from pathlib import Path, PurePosixPath
import sqlite3
import time
import uuid
from .state import atomic_write_text


class CoordinationError(RuntimeError):
    pass


class CoordinationStore:
    def __init__(self, root: Path, clock=time.time):
        self.root = Path(root).resolve()
        self.clock = clock
        directory = self.root / ".autortl"
        directory.mkdir(parents=True, exist_ok=True)
        self.database = directory / "coordination.sqlite3"
        self.export_path = self.root / "coordination" / "status.json"
        with closing(self._connect()) as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS lease (
                    id INTEGER PRIMARY KEY CHECK(id=1), owner TEXT NOT NULL,
                    token TEXT NOT NULL, expires REAL NOT NULL, summary TEXT NOT NULL DEFAULT '');
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY, title TEXT NOT NULL, state TEXT NOT NULL,
                    owner TEXT, files TEXT NOT NULL, evidence TEXT NOT NULL,
                    detail TEXT NOT NULL, updated REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, at REAL NOT NULL,
                    kind TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS checkpoint (
                    id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL);
            """)

    def _connect(self):
        db = sqlite3.connect(self.database, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    @contextmanager
    def _transaction(self):
        db = self._connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()
        self.export()

    def _event(self, db, kind, payload):
        db.execute("INSERT INTO events(at,kind,payload) VALUES(?,?,?)",
                   (self.clock(), kind, json.dumps(payload, sort_keys=True)))

    def _require_lease(self, db, token):
        lease = db.execute("SELECT * FROM lease WHERE id=1").fetchone()
        if not lease or lease["token"] != token or lease["expires"] <= self.clock():
            raise CoordinationError("No matching active coordinator lease; claim or renew a session first")
        return lease

    def claim(self, owner: str, ttl: int = 3600, takeover_reason: str | None = None) -> str:
        if not owner.strip() or len(owner) > 120 or not 60 <= ttl <= 28800:
            raise CoordinationError("Owner required; lease duration must be 60..28800 seconds")
        token = uuid.uuid4().hex
        with self._transaction() as db:
            previous = db.execute("SELECT * FROM lease WHERE id=1").fetchone()
            if previous and previous["expires"] > self.clock() and not takeover_reason:
                raise CoordinationError(f"Coordinator {previous['owner']} holds the lease until {previous['expires']}; do not edit concurrently")
            if takeover_reason is not None and not takeover_reason.strip():
                raise CoordinationError("Takeover needs a recorded reason")
            if previous:
                self._event(db, "COORDINATOR_REPLACED", {"previous": previous["owner"],
                            "expired": previous["expires"] <= self.clock(), "reason": takeover_reason})
                # Claims survive interruption but must be explicitly reassigned.
                db.execute("UPDATE tasks SET state='blocked',detail='Coordinator handoff: reclaim before editing',updated=? WHERE state='active'", (self.clock(),))
            db.execute("INSERT OR REPLACE INTO lease(id,owner,token,expires,summary) VALUES(1,?,?,?,?)",
                       (owner, token, self.clock() + ttl, ""))
            self._event(db, "SESSION_CLAIMED", {"owner": owner, "expires": self.clock() + ttl})
        return token

    def renew(self, token: str, ttl: int = 3600):
        if not 60 <= ttl <= 28800:
            raise CoordinationError("Invalid lease duration")
        with self._transaction() as db:
            self._require_lease(db, token)
            db.execute("UPDATE lease SET expires=? WHERE id=1", (self.clock() + ttl,))
            self._event(db, "LEASE_RENEWED", {"expires": self.clock() + ttl})

    @staticmethod
    def _scope(files):
        result = []
        for item in files:
            item = str(item).replace("\\", "/").rstrip("/")
            path = PurePosixPath(item)
            if not item or item == "." or path.is_absolute() or ".." in path.parts or ":" in item or any(c in item for c in "*?[]") or path.parts[0].casefold() in (".git", ".autortl"):
                raise CoordinationError("Task file scope must stay inside project source")
            result.append(path.as_posix())
        return sorted(set(result))

    @staticmethod
    def _overlap(left, right):
        return any(a.casefold() == b.casefold() or a.casefold().startswith(b.casefold() + "/")
                   or b.casefold().startswith(a.casefold() + "/") for a in left for b in right)

    def claim_task(self, token, task_id, title, owner, files):
        files = self._scope(files)
        if not task_id.strip() or not title.strip() or not owner.strip() or not files:
            raise CoordinationError("Task id, title, worker owner and file scope are required")
        with self._transaction() as db:
            self._require_lease(db, token)
            existing = db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
            if existing and existing["state"] == "done":
                raise CoordinationError("Completed tasks are immutable; create a new task for follow-up work")
            for task in db.execute("SELECT * FROM tasks WHERE state='active'"):
                if task["id"] == task_id and task["owner"] == owner:
                    continue
                if task["id"] == task_id or self._overlap(files, json.loads(task["files"])):
                    raise CoordinationError(f"Task/file scope already owned by {task['owner']} ({task['id']})")
            db.execute("INSERT OR REPLACE INTO tasks VALUES(?,?,?,?,?,?,?,?)",
                       (task_id, title, "active", owner, json.dumps(files), "[]", "", self.clock()))
            self._event(db, "TASK_CLAIMED", {"task": task_id, "owner": owner, "files": files})

    def update_task(self, token, task_id, owner, state, detail="", evidence=None):
        evidence = evidence or []
        if state not in ("active", "blocked", "done") or (state == "done" and not evidence) or (state == "blocked" and not detail.strip()):
            raise CoordinationError("Done needs evidence; blocked needs a reason; state must be active/blocked/done")
        with self._transaction() as db:
            self._require_lease(db, token)
            task = db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
            if not task or task["owner"] != owner or task["state"] == "done":
                raise CoordinationError("Only the assigned worker can update an unfinished task")
            if state == "active" and task["state"] != "active":
                raise CoordinationError("Reclaim blocked task and file scope before editing")
            db.execute("UPDATE tasks SET state=?,detail=?,evidence=?,updated=? WHERE id=?",
                       (state, detail, json.dumps(evidence), self.clock(), task_id))
            self._event(db, "TASK_UPDATED", {"task": task_id, "state": state, "detail": detail, "evidence": evidence})

    def checkpoint(self, token, summary, next_steps, tests, release=False):
        if not summary.strip() or not next_steps:
            raise CoordinationError("Checkpoint requires summary and concrete next steps")
        with self._transaction() as db:
            lease = self._require_lease(db, token)
            payload = {"at": self.clock(), "owner": lease["owner"], "summary": summary,
                       "next_steps": list(next_steps), "tests": list(tests)}
            db.execute("INSERT OR REPLACE INTO checkpoint VALUES(1,?)", (json.dumps(payload),))
            db.execute("UPDATE lease SET summary=? WHERE id=1", (summary,))
            if release:
                db.execute("UPDATE lease SET expires=0 WHERE id=1")
                db.execute("UPDATE tasks SET state='blocked',detail='Session ended: reclaim task before editing',updated=? WHERE state='active'", (self.clock(),))
            self._event(db, "HANDOFF" if release else "CHECKPOINT", payload)

    def status(self):
        with closing(self._connect()) as db:
            db.execute("BEGIN")
            lease = db.execute("SELECT owner,expires,summary FROM lease WHERE id=1").fetchone()
            tasks = []
            for row in db.execute("SELECT * FROM tasks ORDER BY id"):
                task = dict(row)
                for field in ("files", "evidence"): task[field] = json.loads(task[field])
                tasks.append(task)
            checkpoint = db.execute("SELECT payload FROM checkpoint WHERE id=1").fetchone()
            events = [{"id": row["id"], "at": row["at"], "kind": row["kind"],
                       "payload": json.loads(row["payload"])} for row in db.execute("SELECT * FROM events ORDER BY id")]
        coordinator = dict(lease) if lease else None
        if coordinator: coordinator["active"] = coordinator["expires"] > self.clock()
        return {"schema_version": 1, "project": str(self.root), "coordinator": coordinator,
                "checkpoint": json.loads(checkpoint[0]) if checkpoint else None,
                "tasks": tasks, "events": events}

    def export(self):
        # SQLite remains authoritative if a process dies during this derived export.
        atomic_write_text(self.export_path, json.dumps(self.status(), indent=2))
