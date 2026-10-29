"""role_report reads real run records (fixtures copied from tier1-campaign-01)."""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import role_report  # noqa: E402

CAMPAIGN = HERE / "fixtures" / "role_report" / "campaign"


def test_campaign_folder_finds_every_run():
    assert [r.name for r in role_report.runs([CAMPAIGN])] == ["debouncer_build", "pwm"]


def test_pwm_roles_verdicts_and_the_baseline_repair():
    report = role_report.summarize(CAMPAIGN / "pwm")
    assert report["status"] == "done" and report["model_calls"] == 16
    assert report["roles"]["generator.generate"] == {"completed": 5, "unfinished": 0, "retries": 0}
    assert report["repairs"] == {"generator repairs": 1}
    assert report["verdicts"] == {"REJECT": 5}
    assert (report["baseline_lut"], report["best_lut"], report["best_iteration"]) == (7, 7, 0)
    assert [i["lut"] for i in report["iterations"]] == [7, 10, 10, 8, 10, 9]


def test_spec_lint_failure_is_reported_with_its_error():
    report = role_report.summarize(CAMPAIGN / "debouncer_build")
    assert report["status"] == "spec_lint_failed"
    assert report["errors"] == ["top module must differ from child module names"]
    assert report["repairs"] == {"planner spec attempts": 1}
    assert report["iterations"] == []


def test_unfinished_and_retried_attempts_are_counted():
    events = [{"stage": "iteration_1:model:evaluator.evaluate:0", "attempt": 1, "outcome": "RUNNING"},
              {"stage": "iteration_1:model:evaluator.evaluate:0", "attempt": 2, "outcome": "RUNNING"},
              {"stage": "iteration_1:model:evaluator.evaluate:0", "attempt": 2, "outcome": "COMPLETE"},
              {"stage": "iteration_1:tool:xsim_run:0", "attempt": 1, "outcome": "RUNNING"}]
    assert role_report.role_calls(events) == {"evaluator.evaluate": {"completed": 1, "unfinished": 1, "retries": 1}}


def test_markdown_and_json_outputs(capsys):
    assert role_report.main([str(CAMPAIGN)]) == 0
    text = capsys.readouterr().out
    assert "| pwm | done | 16 | 7 | 7 | REJECT 5 | generator repairs 1 |" in text
    assert role_report.main([str(CAMPAIGN), "--json"]) == 0
    assert [r["run"] for r in json.loads(capsys.readouterr().out)] == ["debouncer_build", "pwm"]


def test_empty_path_fails(tmp_path, capsys):
    assert role_report.main([str(tmp_path)]) == 1
