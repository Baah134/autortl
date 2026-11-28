"""Lease keeper loop with injected renew and sleep; one real refusal through session.py."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("lease_keeper", ROOT / "scripts" / "lease_keeper.py")
keeper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(keeper)


def test_renews_until_stop_file_and_rereads_token(tmp_path):
    token, stop = tmp_path / "token.txt", tmp_path / "stop"
    token.write_text("first\n")
    seen, sleeps = [], []

    def renew(value):
        seen.append(value)
        return True, "ok"

    def sleep(seconds):
        sleeps.append(seconds)
        if len(sleeps) == 1:
            token.write_text("second")  # the coordinator reclaimed and rewrote the file
        if len(sleeps) == 2:
            stop.write_text("")

    assert keeper.keep(token, stop, 600, renew_once=renew, sleep=sleep) == keeper.EXIT_STOPPED
    assert seen == ["first", "second"] and sleeps == [600, 600]


def test_refused_renewal_exits_without_retrying_or_leaking_token(tmp_path, capsys):
    token = tmp_path / "token.txt"
    token.write_text("secret-token-value")
    calls = []

    def renew(value):
        calls.append(value)
        return False, "No matching active coordinator lease; claim or renew a session first"

    assert keeper.keep(token, None, 600, renew_once=renew, sleep=lambda s: None) == keeper.EXIT_REFUSED
    err = capsys.readouterr().err
    assert len(calls) == 1 and "lease renewal refused" in err and "secret-token-value" not in err


def test_existing_stop_file_means_no_renewal(tmp_path):
    token, stop = tmp_path / "token.txt", tmp_path / "stop"
    token.write_text("t")
    stop.write_text("")
    assert keeper.keep(token, stop, renew_once=lambda v: (_ for _ in ()).throw(AssertionError)) == 0


def test_real_session_cli_refuses_an_unknown_token(tmp_path):
    ok, message = keeper.renew("not-a-real-token")
    assert not ok and "lease" in message.lower()


def test_cli_rejects_tight_interval(tmp_path):
    token = tmp_path / "token.txt"
    token.write_text("t")
    try:
        keeper.main(["--token-file", str(token), "--interval", "5"])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("interval below 30 s must be rejected")



def test_session_cli_default_lease_is_four_hours(monkeypatch):
    """A one-hour lease lapsed during long runs and sleep; start and renew default to 4 h."""
    spec2 = importlib.util.spec_from_file_location("session_cli", ROOT / "scripts" / "session.py")
    session = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(session)
    seen = []

    class Store:
        def __init__(self, root):
            pass

        def claim(self, owner, ttl, reason):
            seen.append(("claim", ttl))
            return "t"

        def renew(self, token, ttl):
            seen.append(("renew", ttl))

    monkeypatch.setattr(session, "CoordinationStore", Store)
    assert session.main(["start", "--owner", "me"]) == 0
    assert session.main(["renew", "--token", "t"]) == 0
    assert session.main(["renew", "--token", "t", "--ttl", "600"]) == 0
    assert seen == [("claim", 14400), ("renew", 14400), ("renew", 600)]
    assert session.DEFAULT_TTL == 14400
