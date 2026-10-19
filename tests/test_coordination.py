from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import threading
import pytest
from autortl.coordination import CoordinationStore, CoordinationError


@pytest.fixture
def store(tmp_path):
    now = [1000.0]
    return CoordinationStore(tmp_path, clock=lambda: now[0]), now


def test_only_one_coordinator_and_explicit_handoff(store):
    memory, now = store
    first = memory.claim("Codex")
    with pytest.raises(CoordinationError): memory.claim("Claude")
    memory.checkpoint(first, "Tested milestone", ["Repair resume"], ["pytest: passed"], release=True)
    second = memory.claim("Claude")
    with pytest.raises(CoordinationError): memory.renew(first)
    assert second != first
    assert memory.status()["checkpoint"]["summary"] == "Tested milestone"


def test_expired_session_keeps_progress_and_requires_reclaim(store):
    memory, now = store
    token = memory.claim("Codex", ttl=60)
    memory.claim_task(token, "resume", "Recover runs", "codex-worker", ["autortl/fsm.py"])
    now[0] += 61
    replacement = memory.claim("Gemini")
    assert memory.status()["tasks"][0]["state"] == "blocked"
    memory.claim_task(replacement, "resume", "Recover runs", "gemini-worker", ["autortl/fsm.py"])
    assert memory.status()["tasks"][0]["owner"] == "gemini-worker"


def test_active_takeover_requires_recorded_reason(store):
    memory, _ = store
    memory.claim("Codex")
    with pytest.raises(CoordinationError): memory.claim("Claude", takeover_reason="")
    memory.claim("Claude", takeover_reason="User requested takeover after previous session stopped")
    event = [e for e in memory.status()["events"] if e["kind"] == "COORDINATOR_REPLACED"][0]
    assert event["payload"]["reason"]


def test_worker_scope_conflicts_and_completion_evidence(store):
    memory, _ = store
    token = memory.claim("Codex")
    memory.claim_task(token, "a", "First", "worker-a", ["autortl/fsm.py"])
    memory.claim_task(token, "b", "Second", "worker-b", ["autortl/tbgen.py"])
    with pytest.raises(CoordinationError):
        memory.claim_task(token, "c", "Third", "worker-c", ["autortl"])
    with pytest.raises(CoordinationError):
        memory.claim_task(token, "c", "Third", "worker-c", ["AUTORTL/FSM.py"])
    with pytest.raises(CoordinationError): memory.update_task(token, "a", "worker-b", "done", evidence=["test"])
    with pytest.raises(CoordinationError): memory.update_task(token, "a", "worker-a", "done")
    memory.update_task(token, "a", "worker-a", "done", evidence=["tests/test_resume.py: 8 passed"])
    with pytest.raises(CoordinationError): memory.claim_task(token, "a", "Changed", "worker-a", ["a.py"])


@pytest.mark.parametrize("scope", ["../escape", "C:/outside.py", "/outside.py", ".git/config", ".autortl/db", ".", "", "autortl/*.py"])
def test_invalid_worker_scopes_fail_closed(store, scope):
    memory, _ = store
    token = memory.claim("Codex")
    with pytest.raises(CoordinationError): memory.claim_task(token, "bad", "Bad", "worker", [scope])


def test_independent_connections_race_for_one_lease(tmp_path):
    CoordinationStore(tmp_path)
    barrier = threading.Barrier(2)
    def claim(owner):
        memory = CoordinationStore(tmp_path)
        barrier.wait()
        try:
            return memory.claim(owner)
        except CoordinationError:
            return None
    with ThreadPoolExecutor(max_workers=2) as workers:
        results = list(workers.map(claim, ["Claude", "Gemini"]))
    assert sum(result is not None for result in results) == 1


def test_transaction_rolls_back_and_export_survives_restart(store):
    memory, now = store
    token = memory.claim("Codex")
    memory.claim_task(token, "a", "First", "worker", ["a.py"])
    before = memory.status()
    with pytest.raises(RuntimeError):
        with memory._transaction() as db:
            db.execute("UPDATE tasks SET state='done'")
            raise RuntimeError("interrupted write")
    replacement = CoordinationStore(memory.root, clock=lambda: now[0])
    assert replacement.status() == before
    assert json.loads(memory.export_path.read_text())["tasks"][0]["state"] == "active"


def test_readable_export_contains_no_lease_token(store):
    memory, _ = store
    token = memory.claim("Codex")
    memory.checkpoint(token, "Source relocated", ["Run full suite"], ["9 live simulations as expected"])
    exported = memory.export_path.read_text()
    assert token not in exported
    assert "Source relocated" in exported
