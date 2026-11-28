"""Campaign ordering, restart safety and stop guards with a runner double."""
import json
from pathlib import Path

import pytest

from benchmark import campaign, pilot
from benchmark import verilogeval as ve

DATA = Path(__file__).parent / "fixtures" / "verilogeval" / "dataset"


@pytest.fixture
def manifest():
    return ve.build_manifest(DATA, ["Prob901_and2", "Prob900_inv"], dataset_commit="a" * 40,
                             source_commit="b" * 40, runtime_commit="c" * 40, runtime_sha256="d" * 64,
                             requested_model="unobserved-cli-default", budgets=pilot.PROVISIONAL_BUDGETS,
                             trials=2)


class Runner:
    def __init__(self, terminations=None):
        self.calls, self.terminations = [], terminations or {}

    def __call__(self, manifest, task, cell, out_dir, model):
        self.calls.append(cell)
        out_dir.mkdir(parents=True)
        assert task.id == cell[0]
        return {"kind": "candidate", "termination": self.terminations.get(cell, "done"),
                "receipt_id": "0" * 64}


def test_order_is_trial_major_manifest_tasks_fixed_arms(manifest):
    cells = campaign.ordered_cells(manifest)
    assert len(cells) == 12
    assert cells[:6] == [("Prob901_and2", "single_call", 0), ("Prob901_and2", "ablation", 0),
                         ("Prob901_and2", "full", 0), ("Prob900_inv", "single_call", 0),
                         ("Prob900_inv", "ablation", 0), ("Prob900_inv", "full", 0)]
    assert {c[2] for c in cells[:6]} == {0} and {c[2] for c in cells[6:]} == {1}


def test_only_registered_arms_are_scheduled():
    two = ve.build_manifest(DATA, ["Prob900_inv"], dataset_commit="a" * 40, source_commit="b" * 40,
                            runtime_commit="c" * 40, runtime_sha256="d" * 64, requested_model="m",
                            budgets={k: pilot.PROVISIONAL_BUDGETS[k] for k in ("single_call", "full")})
    assert [c[1] for c in campaign.ordered_cells(two)] == ["single_call", "full"]


def test_runs_all_then_restart_runs_nothing(manifest, tmp_path):
    runner = Runner()
    first = campaign.run_campaign(manifest, DATA, tmp_path, runner=runner)
    assert first == {"exit": 0, "ran": 12, "skipped": 0, "pending": 0, "reason": "all cells attempted"}
    assert runner.calls == campaign.ordered_cells(manifest)
    again = Runner()
    second = campaign.run_campaign(manifest, DATA, tmp_path, runner=again)
    assert second["ran"] == 0 and second["skipped"] == 12 and again.calls == []


def test_existing_directory_is_never_rerun_even_if_unsealed(manifest, tmp_path):
    spent = campaign.cell_dir(tmp_path, ("Prob901_and2", "ablation", 0))
    spent.mkdir(parents=True)  # e.g. a launch killed before sealing
    runner = Runner()
    result = campaign.run_campaign(manifest, DATA, tmp_path, runner=runner)
    assert ("Prob901_and2", "ablation", 0) not in runner.calls and result["skipped"] == 1 and result["ran"] == 11


def test_model_block_stops_before_spending_more_cells(manifest, tmp_path):
    blocked = ("Prob901_and2", "full", 0)
    runner = Runner({blocked: "model_blocked"})
    result = campaign.run_campaign(manifest, DATA, tmp_path, runner=runner)
    assert result["exit"] == campaign.EXIT_MODEL_BLOCKED and runner.calls[-1] == blocked
    assert result["ran"] == 3 and result["pending"] == 9
    assert not campaign.cell_dir(tmp_path, ("Prob900_inv", "single_call", 0)).exists()
    events = [json.loads(line) for line in (tmp_path / "campaign.log").read_text().splitlines()]
    assert events[-1]["event"] == "stop" and "model blocked" in events[-1]["reason"]
    assert [e["event"] for e in events[:2]] == ["start", "sealed"]


def test_consecutive_interruptions_stop_but_isolated_ones_do_not(manifest, tmp_path):
    cells = campaign.ordered_cells(manifest)
    isolated = Runner({cells[0]: "interrupted", cells[2]: "interrupted", cells[4]: "interrupted"})
    assert campaign.run_campaign(manifest, DATA, tmp_path / "a", runner=isolated)["exit"] == 0
    streak = Runner({cells[1]: "interrupted", cells[2]: "interrupted", cells[3]: "interrupted"})
    result = campaign.run_campaign(manifest, DATA, tmp_path / "b", runner=streak)
    assert result["exit"] == campaign.EXIT_INTERRUPTED and result["ran"] == 4 and len(streak.calls) == 4


def test_max_cells_limits_a_session(manifest, tmp_path):
    runner = Runner()
    result = campaign.run_campaign(manifest, DATA, tmp_path, runner=runner, max_cells=5)
    assert result == {"exit": 0, "ran": 5, "skipped": 0, "pending": 7, "reason": "max_cells reached"}
    rest = campaign.run_campaign(manifest, DATA, tmp_path, runner=Runner())
    assert rest["skipped"] == 5 and rest["ran"] == 7 and rest["pending"] == 0


def test_run_cell_dispatches_by_arm(manifest, tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(pilot, "run_single_call", lambda m, t, o, trial, model: seen.append(("A", trial, model)) or {})
    monkeypatch.setattr(pilot, "run_full", lambda m, t, o, trial, model, arm: seen.append((arm, trial, model)) or {})
    task = ve.load_task(DATA, "Prob900_inv")
    for arm in ("single_call", "ablation", "full"):
        campaign.run_cell(manifest, task, ("Prob900_inv", arm, 1), tmp_path / arm, "pinned")
    assert seen == [("A", 1, "pinned"), ("ablation", 1, "pinned"), ("full", 1, "pinned")]


# ------------------------------------------------------------ model availability
class Probe:
    def __init__(self, answers):
        self.answers, self.calls = list(answers), 0

    def __call__(self):
        self.calls += 1
        return self.answers.pop(0) if self.answers else (True, "")


def test_blocked_probe_stops_before_spending_any_cell(manifest, tmp_path):
    runner, probe = Runner(), Probe([(False, "CODEX_QUOTA: limit")])
    result = campaign.run_campaign(manifest, DATA, tmp_path, runner=runner, probe=probe)
    assert result["exit"] == campaign.EXIT_MODEL_BLOCKED and result["ran"] == 0 and result["pending"] == 12
    assert runner.calls == [] and not any((tmp_path / "runs").iterdir())
    assert "CODEX_QUOTA" in result["reason"] and "before Prob901_and2 single_call" in result["reason"]


def test_wait_mode_probes_until_available_then_runs_everything(manifest, tmp_path):
    runner, sleeps = Runner(), []
    probe = Probe([(False, "quota"), (False, "quota"), (True, "")])
    result = campaign.run_campaign(manifest, DATA, tmp_path, runner=runner, probe=probe,
                                   wait_seconds=1200, sleep=sleeps.append)
    assert result["exit"] == 0 and result["ran"] == 12 and sleeps == [1200, 1200] and probe.calls == 3
    events = [json.loads(line)["event"] for line in (tmp_path / "campaign.log").read_text().splitlines()]
    assert events[:3] == ["waiting_for_model", "waiting_for_model", "model_available"]


def test_block_mid_campaign_waits_and_resumes_spending_only_that_cell(manifest, tmp_path):
    cells = campaign.ordered_cells(manifest)
    runner, sleeps = Runner({cells[2]: "model_blocked"}), []
    probe = Probe([(True, ""), (False, "quota"), (True, "")])  # start ok; blocked after cell 2; then back
    result = campaign.run_campaign(manifest, DATA, tmp_path, runner=runner, probe=probe,
                                   wait_seconds=600, sleep=sleeps.append)
    assert result["exit"] == 0 and result["ran"] == 12 and runner.calls == cells and sleeps == [600]


def test_wait_gives_up_after_max_wait(manifest, tmp_path):
    sleeps = []
    result = campaign.run_campaign(manifest, DATA, tmp_path, runner=Runner(), probe=Probe([(False, "q")] * 50),
                                   wait_seconds=1800, max_wait_seconds=3600, sleep=sleeps.append)
    assert result["exit"] == campaign.EXIT_MODEL_BLOCKED and sleeps == [1800, 1800] and result["ran"] == 0


def test_model_available_maps_block_and_success():
    from llm import client

    def blocked(*args, **kwargs):
        raise client.ModelCallError("generator", "CODEX_QUOTA", message="usage limit")

    assert campaign.model_available(ask=lambda *a, **k: "OK") == (True, "")
    ok, reason = campaign.model_available(ask=blocked)
    assert not ok and reason.startswith("CODEX_QUOTA")


def test_interrupted_cell_also_triggers_a_probe_and_wait(manifest, tmp_path):
    """A harness cell stopped by quota is sealed interrupted; do not start the next cell blind."""
    cells = campaign.ordered_cells(manifest)
    runner, sleeps = Runner({cells[1]: "interrupted"}), []
    probe = Probe([(True, ""), (False, "quota"), (True, "")])
    result = campaign.run_campaign(manifest, DATA, tmp_path, runner=runner, probe=probe,
                                   wait_seconds=900, sleep=sleeps.append)
    assert result["exit"] == 0 and result["ran"] == 12 and sleeps == [900] and probe.calls == 3
    stop_now = campaign.run_campaign(manifest, DATA, tmp_path / "b", runner=Runner({cells[1]: "interrupted"}),
                                     probe=Probe([(True, ""), (False, "quota")]))
    assert stop_now["exit"] == campaign.EXIT_MODEL_BLOCKED and stop_now["ran"] == 2


# ------------------------------------------------------------ spent, unsealed cells
def test_spent_unsealed_cell_is_sealed_interrupted_not_rerun(manifest, tmp_path):
    from benchmark import artifacts
    cell = ("Prob901_and2", "ablation", 0)
    spent = campaign.cell_dir(tmp_path, cell)
    (spent / "run").mkdir(parents=True)  # the process died mid-build
    runner = Runner()
    result = campaign.run_campaign(manifest, DATA, tmp_path, runner=runner)
    assert cell not in runner.calls and result["skipped"] == 1 and result["ran"] == 11
    record = json.loads((spent / "run.json").read_text())
    assert (record["kind"], record["termination"]) == ("missing", "interrupted")
    assert record["accounting"]["spent_unsealed"] is True and (spent / "run").is_dir()
    receipt = artifacts.load_artifact(spent / "submission", expected_id=record["receipt_id"])
    assert receipt["termination"] == "interrupted" and receipt["cell"]["arm"] == "ablation"
    events = [json.loads(line) for line in (tmp_path / "campaign.log").read_text().splitlines()]
    spent_events = [e for e in events if e["event"] == "sealed_spent"]
    assert len(spent_events) == 1 and spent_events[0]["arm"] == "ablation"
    assert spent_events[0]["termination"] == "interrupted"


def test_sealed_cell_is_left_untouched_and_published_receipt_is_reused(manifest, tmp_path):
    from benchmark import artifacts
    sealed = ("Prob901_and2", "single_call", 0)
    done_dir = campaign.cell_dir(tmp_path, sealed)
    done_dir.mkdir(parents=True)
    (done_dir / "run.json").write_text('{"kept": true}')
    assert campaign.seal_spent(manifest, sealed, done_dir) is None
    assert json.loads((done_dir / "run.json").read_text()) == {"kept": True}
    half = ("Prob900_inv", "full", 0)  # the receipt was published, run.json was not written
    half_dir = campaign.cell_dir(tmp_path, half)
    half_dir.mkdir(parents=True)
    receipt = artifacts.record_missing(manifest, {"task": half[0], "trial": 0, "arm": "full"},
                                       destination=half_dir / "submission", termination="budget")
    record = campaign.seal_spent(manifest, half, half_dir)
    assert record["receipt_id"] == receipt["id"] and record["termination"] == "budget"
