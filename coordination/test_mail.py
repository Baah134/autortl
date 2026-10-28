import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import pytest
from autortl.coordination import CoordinationStore
from coordination import mail
from coordination.mail import MailError

FIXTURES = Path(__file__).parent / "fixtures"
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def box(tmp_path):
    return {"log": tmp_path / "messages.jsonl", "lease_db": tmp_path / "missing.sqlite3"}


def _fixture(name, tmp_path):
    return Path(shutil.copy(FIXTURES / name, tmp_path / "messages.jsonl"))


def test_fixture_log_with_bom_parses_threads_and_closures(tmp_path):
    log = _fixture("valid_with_bom.jsonl", tmp_path)
    assert mail.inbox("codex", log=log)[0]["subject"] == "Board port"
    claude = mail.inbox("claude", log=log)
    assert [m["id"] for m in claude] == [2, 3] and claude[0]["reply_to"] == 1
    assert claude[0]["body"] == "Reviewed → one fix requested ✓"
    closed = mail.inbox("codex", include_closed=True, log=log)[0]
    assert closed["state"] == "closed" and closed["closed"]["by"] == "codex"
    nxt = mail.post("claude", "codex", "note", "Next", "Appends after BOM.", log=log,
                    lease_db=tmp_path / "missing.sqlite3")
    assert nxt["id"] == 4 and len(mail.read_log(log)) == 5


@pytest.mark.parametrize("name,match", [
    ("duplicate_id.jsonl", "Duplicate message id 1"),
    ("close_missing_at.jsonl", "line 2 has missing or invalid 'at'"),
    ("post_string_id.jsonl", "line 1 has missing or invalid 'id'"),
    ("corrupt_line.jsonl", "line 2 is not valid JSON"),
])
def test_bad_fixture_logs_fail_closed_for_reads_and_writes(tmp_path, name, match):
    log = _fixture(name, tmp_path)
    before = log.read_bytes()
    with pytest.raises(MailError, match=match):
        mail.inbox("claude", log=log)
    with pytest.raises(MailError, match=match):
        mail.post("claude", "codex", "note", "More", "Blocked.", log=log,
                  lease_db=tmp_path / "missing.sqlite3")
    assert log.read_bytes() == before


def test_messages_reach_only_their_recipient_or_any(box):
    mail.post("claude", "codex", "request", "Review mailbox", "Please review.", **box)
    mail.post("codex", "claude", "note", "Back soon", "Running campaign.", **box)
    mail.post("user", "any", "note", "Board", "Basys 3 on COM10.", **box)
    assert [m["id"] for m in mail.inbox("codex", log=box["log"])] == [1, 3]
    assert [m["id"] for m in mail.inbox("claude", log=box["log"])] == [2, 3]
    assert mail.inbox("gemini", log=box["log"])[0]["subject"] == "Board"


def test_close_resolves_once_and_only_by_a_party(box):
    first = mail.post("claude", "codex", "question", "Campaign13?", "Status?", **box)
    with pytest.raises(MailError, match="Only codex, claude or the user"):
        mail.close(first["id"], "gemini", "Not mine", **box)
    with pytest.raises(MailError, match="Resolution"):
        mail.close(first["id"], "codex", "  ", **box)
    mail.close(first["id"], "codex", "Recovered; see SESSION_HANDOFF", **box)
    with pytest.raises(MailError, match="already closed"):
        mail.close(first["id"], "codex", "Again", **box)
    assert mail.inbox("codex", log=box["log"]) == []
    anyone = mail.post("user", "any", "request", "Anyone", "Pick this up.", **box)
    mail.close(anyone["id"], "gemini", "Done", **box)


def test_replies_must_reference_an_existing_message(box):
    with pytest.raises(MailError, match="unknown message 7"):
        mail.post("codex", "claude", "answer", "Re", "Yes", reply_to=7, **box)
    question = mail.post("claude", "codex", "question", "Q", "Why?", **box)
    answer = mail.post("codex", "claude", "answer", "Re: Q", "Because.", reply_to=question["id"], **box)
    assert answer["reply_to"] == question["id"]


@pytest.mark.parametrize("sender,recipient,kind,subject,body", [
    ("Claude", "codex", "note", "s", "b"),
    ("claude", "co dex", "note", "s", "b"),
    ("claude", "codex", "gossip", "s", "b"),
    ("claude", "codex", "note", "two\nlines", "b"),
    ("claude", "codex", "note", "s", " "),
    ("claude", "codex", "note", "x" * 121, "b"),
    ("claude", "codex", "note", "s", "x" * 4001),
])
def test_invalid_posts_fail_without_writing(box, sender, recipient, kind, subject, body):
    with pytest.raises(MailError):
        mail.post(sender, recipient, kind, subject, body, **box)
    assert not box["log"].exists()


def test_real_coordinator_lease_token_is_never_written(box, tmp_path):
    token = CoordinationStore(tmp_path).claim("Codex coordinator")
    box["lease_db"] = tmp_path / ".autortl" / "coordination.sqlite3"
    with pytest.raises(MailError, match="lease token"):
        mail.post("claude", "codex", "note", "Token", f"use {token}", **box)
    note = mail.post("claude", "codex", "note", "Safe", "No secrets here.", **box)
    with pytest.raises(MailError, match="lease token"):
        mail.close(note["id"], "codex", token, **box)
    assert token not in box["log"].read_text(encoding="utf-8")


def test_unreadable_lease_database_fails_closed(box, tmp_path):
    box["lease_db"] = tmp_path / "broken.sqlite3"
    box["lease_db"].write_bytes(b"not a sqlite database at all" * 10)
    with pytest.raises(MailError, match="Cannot read broken.sqlite3"):
        mail.post("claude", "codex", "note", "Blocked", "Cannot screen.", **box)
    assert not box["log"].exists()


def test_held_lock_times_out_with_holder_and_is_released_after_writes(box):
    lock = box["log"].with_name(box["log"].name + ".lock")
    lock.write_text("123")
    with pytest.raises(MailError, match=r"pid 123"):
        mail.post("claude", "codex", "note", "Blocked", "Wait.", timeout=0.1, **box)
    lock.unlink()
    mail.post("claude", "codex", "note", "Free", "Go.", **box)
    assert not lock.exists()


def test_real_permission_error_is_reported_not_treated_as_lock(box, monkeypatch):
    def denied(*args, **kwargs):
        raise PermissionError("access denied")
    monkeypatch.setattr(mail.os, "open", denied)
    with pytest.raises(MailError, match="Cannot create messages.jsonl.lock: access denied"):
        mail.post("claude", "codex", "note", "Denied", "No ACL.", timeout=5, **box)


def test_inbox_survives_legacy_code_page_pipe(tmp_path):
    log = _fixture("valid_with_bom.jsonl", tmp_path)
    env = {k: v for k, v in os.environ.items() if k != "PYTHONIOENCODING"}
    env["PYTHONIOENCODING"] = "cp1252"
    script = ("import sys; from pathlib import Path; from coordination import mail; "
              "sys.exit(mail.main(['inbox', '--for', 'claude'], log=Path(sys.argv[1]), "
              "lease_db=Path(sys.argv[2])))")
    result = subprocess.run([sys.executable, "-c", script, str(log), str(tmp_path / "none.sqlite3")],
                            cwd=ROOT, env=env, capture_output=True)
    assert result.returncode == 0, result.stderr.decode("cp1252", "replace")
    out = result.stdout.decode("cp1252")
    assert "#2 [answer] codex -> claude" in out and "\\u2192" in out


def test_cli_round_trip(box, capsys):
    assert mail.main(["post", "--from", "claude", "--to", "codex", "--kind", "request",
                      "--subject", "Review", "--body", "Line one\nLine two"], **box) == 0
    assert json.loads(capsys.readouterr().out) == {"posted": 1}
    assert mail.main(["inbox", "--for", "codex"], **box) == 0
    out = capsys.readouterr().out
    assert "#1 [request] claude -> codex" in out and "    Line two" in out
    assert mail.main(["close", "--id", "1", "--by", "codex", "--resolution", "Reviewed"], **box) == 0
    capsys.readouterr()
    assert mail.main(["inbox", "--for", "codex"], **box) == 0
    assert "No open messages for codex" in capsys.readouterr().out
    assert mail.main(["close", "--id", "9", "--by", "codex", "--resolution", "x"], **box) == 2
    assert "No message 9" in capsys.readouterr().err
