"""tools/signoff.py holds tiers bottom-up, archives every campaign and resumes."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import signoff  # noqa: E402


def write_history(path, records):
    path.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")


def test_latest_full_record_ignores_subset_runs_and_other_tiers(tmp_path):
    history = tmp_path / "results.jsonl"
    write_history(history, [{"tier": 2, "full_tier": True, "held": False},
                            {"tier": 2, "full_tier": True, "held": True},
                            {"tier": 2, "full_tier": False, "held": False},
                            {"tier": 3, "full_tier": True, "held": False}])
    assert signoff.latest_full_record(2, history)["held"] is True
    assert signoff.latest_full_record(5, history) is None


def test_archive_copies_run_logs_and_writes_a_manifest(tmp_path):
    logs = tmp_path / "logs"
    (logs / "c1" / "entry" / "xsim.dir").mkdir(parents=True)
    (logs / "c1" / "entry" / "run_summary.json").write_text("{}", encoding="utf-8")
    (logs / "c1" / "entry" / "xsim.dir" / "big.bin").write_text("x", encoding="utf-8")
    (logs / "c1-prelaunch.json").write_text("{}", encoding="utf-8")
    (logs / "c1.console.txt").write_text("done", encoding="utf-8")
    (tmp_path / "curriculum").mkdir()
    (tmp_path / "curriculum" / "results.jsonl").write_text("", encoding="utf-8")
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "role_report.py").write_text("print('# Role report')", encoding="utf-8")
    dest = tmp_path / "evidence" / "c1"
    signoff.archive("c1", dest, root=tmp_path)
    manifest = json.loads((dest / "archive-manifest.json").read_text(encoding="utf-8"))["files"]
    assert "run/entry/run_summary.json" in manifest and "c1-prelaunch.json" in manifest
    assert "c1.console.txt" in manifest and "history-at-c1.jsonl" in manifest
    assert not any("xsim.dir" in name for name in manifest)
    assert (dest / "role-report.md").read_text(encoding="utf-8").startswith("# Role report")


def test_tiers_must_be_ascending():
    with pytest.raises(SystemExit):
        signoff.main(["--tiers", "1", "0", "--date", "d"])


def test_runs_campaigns_until_held_then_moves_up_and_resumes(tmp_path, monkeypatch):
    monkeypatch.setattr(signoff, "ROOT", tmp_path)
    (tmp_path / "logs").mkdir()
    history = tmp_path / "results.jsonl"
    monkeypatch.setattr(signoff, "HISTORY", history)
    write_history(history, [])
    verdicts = {0: [False, True, True, True], 1: [True, True, True]}
    runs = []

    def fake_run(cmd, cwd=None, stdout=None, stderr=None, **kwargs):
        tier = int(cmd[cmd.index("--tier") + 1])
        runs.append(cmd[cmd.index("--name") + 1])
        previous = [json.loads(l) for l in history.read_text(encoding="utf-8").splitlines() if l.strip()]
        mine = [r for r in previous if r["tier"] == tier]
        qualified = verdicts[tier][len(mine)]
        streak = 0
        for r in mine + [{"qualified": qualified}]:
            streak = streak + 1 if r["qualified"] else 0
        write_history(history, previous + [{"tier": tier, "full_tier": True, "qualified": qualified,
                                            "held": streak >= 3}])
        return subprocess.CompletedProcess(cmd, 0 if qualified else 1)

    monkeypatch.setattr(signoff.subprocess, "run", fake_run)
    monkeypatch.setattr(signoff, "archive", lambda name, dest, **k: dest.mkdir(parents=True) or 1)
    assert signoff.main(["--tiers", "0", "1", "--date", "d"]) == 0
    assert runs == ["signoff-t0-01", "signoff-t0-02", "signoff-t0-03", "signoff-t0-04",
                    "signoff-t1-01", "signoff-t1-02", "signoff-t1-03"]
    runs.clear()
    assert signoff.main(["--tiers", "0", "1", "--date", "d"]) == 0  # everything archived: nothing reruns
    assert runs == []


def test_stops_when_a_tier_cannot_hold(tmp_path, monkeypatch):
    monkeypatch.setattr(signoff, "ROOT", tmp_path)
    (tmp_path / "logs").mkdir()
    history = tmp_path / "results.jsonl"
    monkeypatch.setattr(signoff, "HISTORY", history)
    write_history(history, [])
    def fake_run(cmd, **kwargs):
        previous = history.read_text(encoding="utf-8")
        history.write_text(previous + json.dumps({"tier": 0, "full_tier": True, "qualified": False,
                                                  "held": False}) + "\n", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 1)
    monkeypatch.setattr(signoff.subprocess, "run", fake_run)
    monkeypatch.setattr(signoff, "archive", lambda name, dest, **k: dest.mkdir(parents=True) or 1)
    assert signoff.main(["--tiers", "0", "1", "--date", "d", "--max-campaigns", "2"]) == 1
