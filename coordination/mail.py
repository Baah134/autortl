"""Durable, Git-tracked messages between alternating development agents.

Agents take turns holding the coordinator lease (scripts/session.py). The lease
says who may edit; this mailbox carries what agents need to tell each other.
A waiting agent can leave a question for the active one without editing, and
requests, answers and blockers survive a handoff or a fresh clone.

The log is append-only JSONL; open/closed state is derived from it. It lives
outside the frozen harness source, so posting never changes experiment identity.
"""
from __future__ import annotations
import argparse
from contextlib import closing
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "coordination" / "messages.jsonl"
LEASE_DB = ROOT / ".autortl" / "coordination.sqlite3"
KINDS = ("note", "question", "request", "answer", "blocker")
NAME = re.compile(r"[a-z][a-z0-9-]{0,31}")
MAX_SUBJECT, MAX_BODY = 120, 4000
# Required fields per record type; reply_to may also be None.
FIELDS = {"post": {"id": int, "at": str, "from": str, "to": str, "kind": str,
                   "subject": str, "body": str, "reply_to": int},
          "close": {"ref": int, "at": str, "by": str, "resolution": str}}


class MailError(RuntimeError):
    pass


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _name(value, field):
    if not NAME.fullmatch(value or ""):
        raise MailError(f"{field} must be a short lowercase agent name such as codex, claude or user")
    return value


def _text(value, field, limit, single_line=False):
    value = (value or "").strip()
    if not value or len(value) > limit or (single_line and "\n" in value):
        raise MailError(f"{field} must be 1..{limit} characters" + (" on one line" if single_line else ""))
    return value


def _lease_token(lease_db):
    if not lease_db.exists():
        return None
    try:
        with closing(sqlite3.connect(lease_db.resolve().as_uri() + "?mode=ro", uri=True, timeout=5)) as db:
            row = db.execute("SELECT token FROM lease WHERE id=1").fetchone()
    except sqlite3.Error as exc:
        # Fail closed: without the token we cannot screen the message.
        raise MailError(f"Cannot read {lease_db.name} to screen for the lease token ({exc}); retry") from exc
    return row[0] if row else None


def _no_secret(lease_db, *texts):
    # Lease tokens are private; the mailbox is committed to Git.
    token = _lease_token(lease_db)
    if token and any(token in text for text in texts):
        raise MailError("Message contains the coordinator lease token; never share it")


class _Lock:
    """Exclusive lock file so a waiting agent and the active one cannot interleave writes."""

    def __init__(self, log, timeout):
        self.path = log.with_name(log.name + ".lock")
        self.timeout = timeout

    def __enter__(self):
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except (FileExistsError, PermissionError) as exc:
                # Windows reports a lock file pending deletion as PermissionError;
                # with no lock file present it is a real permission problem.
                if isinstance(exc, PermissionError) and not self.path.exists():
                    raise MailError(f"Cannot create {self.path.name}: {exc}") from exc
                if time.monotonic() >= deadline:
                    try:
                        holder = self.path.read_text(encoding="ascii").strip() or "unknown"
                    except OSError:
                        holder = "unknown"
                    raise MailError(f"Mailbox locked by {self.path.name} (pid {holder}); "
                                    "if that process is gone, delete the lock file")
                time.sleep(0.05)
                continue
            try:
                os.write(fd, str(os.getpid()).encode())
            finally:
                os.close(fd)
            return self

    def __exit__(self, *exc):
        for _ in range(20):
            try:
                self.path.unlink(missing_ok=True)
                return
            except PermissionError:
                time.sleep(0.05)
        print(f"Warning: could not remove {self.path}; delete it if no agent is posting", file=sys.stderr)


def _check(record, log, number):
    where = f"{log.name} line {number}"
    if not isinstance(record, dict) or record.get("type") not in FIELDS:
        raise MailError(f"{where} is not a post or close record")
    for field, kind in FIELDS[record["type"]].items():
        value = record.get(field)
        if field == "reply_to" and value is None:
            continue
        if not isinstance(value, kind) or isinstance(value, bool):
            raise MailError(f"{where} has missing or invalid '{field}'")


def read_log(log=LOG):
    if not log.exists():
        return []
    records = []
    # utf-8-sig tolerates a BOM left by a hand repair in Windows PowerShell.
    with log.open(encoding="utf-8-sig") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise MailError(f"{log.name} line {number} is not valid JSON; repair it before continuing") from exc
            _check(record, log, number)
            records.append(record)
    return records


def messages(log=LOG):
    """All posts by id, each with its derived state and closing record."""
    result = {}
    for record in read_log(log):
        if record["type"] == "post":
            if record["id"] in result:
                # Two branches can append the same next id; never let one hide the other.
                raise MailError(f"Duplicate message id {record['id']} in {log.name}; renumber one post")
            result[record["id"]] = dict(record, state="open", closed=None)
        else:
            message = result.get(record["ref"])
            if message is None or message["state"] == "closed":
                raise MailError(f"Close record for message {record['ref']} has no open post")
            message["state"] = "closed"
            message["closed"] = {k: record[k] for k in ("at", "by", "resolution")}
    return result


def _append(log, record):
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def post(sender, recipient, kind, subject, body, reply_to=None,
         log=LOG, lease_db=LEASE_DB, timeout=10.0):
    sender = _name(sender, "Sender")
    recipient = recipient if recipient == "any" else _name(recipient, "Recipient")
    if kind not in KINDS:
        raise MailError(f"Kind must be one of {', '.join(KINDS)}")
    subject = _text(subject, "Subject", MAX_SUBJECT, single_line=True)
    body = _text(body, "Body", MAX_BODY)
    _no_secret(lease_db, subject, body)
    with _Lock(log, timeout):
        existing = messages(log)
        if reply_to is not None and reply_to not in existing:
            raise MailError(f"Cannot reply to unknown message {reply_to}")
        record = {"type": "post", "id": max(existing, default=0) + 1, "at": _now(),
                  "from": sender, "to": recipient, "kind": kind,
                  "subject": subject, "body": body, "reply_to": reply_to}
        _append(log, record)
    return record


def close(message_id, by, resolution, log=LOG, lease_db=LEASE_DB, timeout=10.0):
    by = _name(by, "Closer")
    resolution = _text(resolution, "Resolution", MAX_BODY)
    _no_secret(lease_db, resolution)
    with _Lock(log, timeout):
        message = messages(log).get(message_id)
        if message is None:
            raise MailError(f"No message {message_id}")
        if message["state"] == "closed":
            raise MailError(f"Message {message_id} is already closed")
        if message["to"] != "any" and by not in (message["to"], message["from"], "user"):
            raise MailError(f"Only {message['to']}, {message['from']} or the user can close message {message_id}")
        record = {"type": "close", "ref": message_id, "at": _now(), "by": by, "resolution": resolution}
        _append(log, record)
    return record


def inbox(agent, include_closed=False, log=LOG):
    agent = _name(agent, "Agent")
    return [m for _, m in sorted(messages(log).items())
            if m["to"] in (agent, "any") and (include_closed or m["state"] == "open")]


def _render(message):
    reply = f"  (reply to #{message['reply_to']})" if message.get("reply_to") else ""
    lines = [f"#{message['id']} [{message['kind']}] {message['from']} -> {message['to']}  "
             f"{message['at']}  {message['state']}{reply}",
             f"  {message['subject']}"]
    lines += [f"    {line}" for line in message["body"].splitlines()]
    if message["closed"]:
        closed = message["closed"]
        lines.append(f"  closed by {closed['by']} {closed['at']}: {closed['resolution']}")
    return "\n".join(lines)


def main(argv=None, log=LOG, lease_db=LEASE_DB):
    # A console or pipe may use a legacy code page; never crash on a model's arrow or check mark.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="backslashreplace")
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    send = sub.add_parser("post")
    send.add_argument("--from", dest="sender", required=True)
    send.add_argument("--to", required=True, help="agent name, user, or any")
    send.add_argument("--kind", choices=KINDS, required=True)
    send.add_argument("--subject", required=True)
    send.add_argument("--body", required=True)
    send.add_argument("--reply-to", type=int)
    box = sub.add_parser("inbox")
    box.add_argument("--for", dest="agent", required=True)
    box.add_argument("--all", action="store_true", help="include closed messages")
    box.add_argument("--json", action="store_true")
    done = sub.add_parser("close")
    done.add_argument("--id", type=int, required=True)
    done.add_argument("--by", required=True)
    done.add_argument("--resolution", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "post":
            record = post(args.sender, args.to, args.kind, args.subject, args.body,
                          args.reply_to, log=log, lease_db=lease_db)
            print(json.dumps({"posted": record["id"]}))
        elif args.command == "close":
            close(args.id, args.by, args.resolution, log=log, lease_db=lease_db)
            print(json.dumps({"closed": args.id}))
        else:
            found = inbox(args.agent, args.all, log=log)
            if args.json:
                print(json.dumps(found, indent=2))
            elif found:
                print("\n\n".join(_render(m) for m in found))
            else:
                print(f"No {'' if args.all else 'open '}messages for {args.agent}")
        return 0
    except MailError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
