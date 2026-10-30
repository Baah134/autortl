"""run_view renders run records as one self-contained, escaped HTML page."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import run_view  # noqa: E402

CAMPAIGN = HERE / "fixtures" / "role_report" / "campaign"
PAYLOAD = "<script>alert(1)</script> </textarea>"
EXTERNAL = re.compile(r"""(?:src|href|action|poster|data)\s*=\s*["']?\s*(?:https?:)?//|@import|url\(""", re.I)


def _write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _jsonl(path: Path, rows):
    _write(path, "".join(json.dumps(row) + "\n" for row in rows))


def _stage(stage, attempt, outcome, ts=None):
    event = {"stage": stage, "attempt": attempt, "outcome": outcome,
             "event_id": f"stage:{stage}:{attempt}:{'start' if outcome == 'RUNNING' else 'end'}"}
    if ts is not None:
        event["ts"] = ts
    return event


def _journal(run: Path, stage: str, result):
    folder = run / "journal" / hashlib.sha256(stage.encode()).hexdigest()
    _write(folder / "started.json", json.dumps({"stage": stage, "attempt": 1}))
    _write(folder / "completed.json", json.dumps({"stage": stage, "result": result, "artifacts": {}}))


def synthetic_run(root: Path) -> Path:
    """A small optimize run whose model-written files carry an HTML payload."""
    run = root / "evil"
    metrics = {"sim_passed": True, "sim_error": "", "wns_ns": 0.5, "whs_ns": 0.1, "timing_met": True,
               "lut_used": 10, "ff_used": 4, "reg2reg_wns_ns": 2.5}
    _write(run / "run_summary.json", json.dumps({"status": "done", "best_iteration": 1, "top_module": "evil",
                                                  "improvement_kind": "objective", "baseline_metrics": metrics,
                                                  "best_metrics": {**metrics, "lut_used": 7}}))
    _write(run / "config.json", json.dumps({"mode": "optimize", "top_module": "evil", "model": "test-model",
                                             "objective": "minimize_luts", "target_part": "xc7a35tcpg236-1",
                                             "target_freq_mhz": 100.0}))
    _write(run / "budget.json", json.dumps({"llm_calls": 4, "vivado_seconds": 90.0, "elapsed": 125.0,
                                             "tokens": {"input_tokens": 5000, "cached_input_tokens": 1000,
                                                        "output_tokens": 321}}))
    _jsonl(run / "designs.jsonl", [
        {"iteration": 0, "is_best": False, "recommendation": "BASELINE", **metrics},
        {"iteration": 1, "is_best": True, "recommendation": "ACCEPT", **metrics, "lut_used": 7,
         "artifact_dir": "C:\\logs\\evil\\iter_001\\cand_standard"}])
    _jsonl(run / "events.jsonl", [
        _stage("baseline:tool:xsim_run:0", 1, "RUNNING", "2026-10-29T10:00:00+00:00"),
        _stage("baseline:tool:xsim_run:0", 1, "COMPLETE", "2026-10-29T10:00:42+00:00"),
        _stage("iteration_1:model:planner.plan:0", 1, "RUNNING", 100.0),
        _stage("iteration_1:model:planner.plan:0", 1, "COMPLETE", 112.5),
        _stage("iteration_1:model:generator.generate:0", 1, "RUNNING"),
        _stage("iteration_1:model:generator.generate:0", 1, "COMPLETE"),
        _stage("iteration_1:model:generator.fix:0", 1, "RUNNING"),
        _stage("iteration_1:model:generator.fix:0", 1, "COMPLETE"),
        _stage("iteration_1:decision:need_plan:0", 1, "RUNNING"),
        _stage("iteration_1:decision:need_plan:0", 1, "COMPLETE"),
        _stage("iteration_1:model:evaluator.evaluate:0", 1, "RUNNING"),
        {"stage": "model_worker", "scope": "iteration_1", "outcome": "INFRA_FAIL", "failure_kind": "infra",
         "role": "evaluator", "error_code": "CODEX_QUOTA", "error": "limit hit, see https://example.invalid/usage "
         + PAYLOAD, "event_id": "infra:1"}])
    _journal(run, "iteration_1:model:generator.generate:0", "module evil; // " + PAYLOAD + "\nendmodule\n")
    _journal(run, "iteration_1:model:generator.fix:0", "module evil; // fixed\nendmodule\n")
    _journal(run, "iteration_1:decision:need_plan:0", True)
    baseline = "module evil(input a, output y);\n  assign y = a;\nendmodule\n"
    _write(run / "iter_000" / "evil.v", baseline)
    _write(run / "iter_001" / "cand_standard" / "evil.v",
           "module evil(input a, output y);\n  // " + PAYLOAD + "\n  assign y = ~~a;\nendmodule\n")
    _write(run / "iter_001" / "evaluation.md",
           "# EVALUATION\n## Recommendation\nACCEPT\n## Reason\nFewer LUTs " + PAYLOAD + "\n")
    _write(run / "plan.md", "# PLAN\n## Instruction for generator\n" + PAYLOAD + "\n")
    _write(run / "contract.md", "# Fixed optimization contract\n" + "\n".join(f"line {i}" for i in range(1000)))
    _write(run / "progress.md", "\n<!-- event:x -->\n## [2026-10-29 10:05:00] iter 001 | ACCEPT\n- Invert twice "
           + PAYLOAD + "\n")
    return run


def test_fixture_campaign_page_has_summary_and_runs():
    page = run_view.build(CAMPAIGN)
    assert "Campaign summary" in page
    assert page.count('<section class="run"') == 2
    assert 'href="#run-1"' in page and 'id="run-2"' in page
    assert "debouncer_build" in page and "spec_lint_failed" in page
    assert "top module must differ from child module names" in page
    assert "planner spec attempts" in page and "generator repairs" in page
    assert "generator.fix" in page and "evaluator.evaluate" in page
    assert "REJECT 5" in page                        # pwm verdicts in the summary table
    assert "no timestamps" in page                   # fixture events carry no times
    assert not EXTERNAL.search(page)


def test_synthetic_run_shows_roles_metrics_rtl_and_timeline(tmp_path):
    run = synthetic_run(tmp_path)
    page = run_view.build(run)
    assert "Campaign summary" not in page            # a single run has no summary table
    for text in ("test-model", "5,000 in / 321 out (1,000 cached)", "minimize_luts", "Promoted best: iteration 1.",
                 "planner.plan", "generator.generate", "evaluator.evaluate", "CODEX_QUOTA",
                 "Evaluator report", "evaluation.md", "reg2reg WNS ns", "2.5", "Latest planner plan"):
        assert text in page, text
    assert '7 <span class="delta good">-3</span>' in page          # LUT against the baseline
    assert "42.0 s" in page and "12.5 s" in page                     # durations from ISO and epoch times
    assert "unfinished" in page                                      # evaluator start without an end
    assert "2 lines added, 1 removed." in page                       # winner diff against the baseline
    assert '<span class="d-add">+  assign y = ~~a;</span>' in page
    assert "Showing the first 400 of 1,001 lines." in page           # contract capped
    assert "line 398" in page and "line 400" not in page


def test_untrusted_text_is_escaped_everywhere(tmp_path):
    page = run_view.build(synthetic_run(tmp_path))
    assert "<script>alert(1)</script>" not in page
    assert "</textarea>" not in page
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page
    assert "&lt;/textarea&gt;" in page
    assert page.count("<script") == 1                # only the page's own collapse script
    assert not EXTERNAL.search(page)                 # the escaped URL in an error is text, not a resource
    assert "Content-Security-Policy" in page and "default-src &#x27;none&#x27;" in page


def test_folder_names_and_summary_fields_are_escaped(tmp_path):
    # Windows forbids < > " in names, so the folder carries & and ' while the record carries tags.
    run = tmp_path / "camp" / "a&b'c"
    _write(run / "run_summary.json", json.dumps({"status": "done"}))
    other = tmp_path / "camp" / "plain"
    _write(other / "run_summary.json", json.dumps({"status": "<b>odd</b>", "failure_kind": "<i>k</i>"}))
    page = run_view.build(tmp_path / "camp")
    assert "a&amp;b&#x27;c" in page and "a&b'c" not in page
    assert "<b>odd" not in page and "<i>k" not in page
    assert "&lt;b&gt;odd&lt;/b&gt;" in page and "&lt;i&gt;k&lt;/i&gt;" in page


def test_cli_writes_the_default_and_the_named_file(tmp_path):
    run = synthetic_run(tmp_path)
    out = subprocess.run([sys.executable, str(HERE.parent / "run_view.py"), str(run)],
                         capture_output=True, text=True)
    assert out.returncode == 0
    default = run / "run-view.html"
    assert Path(out.stdout.strip()) == default and default.is_file()
    named = tmp_path / "out" / "view.html"
    assert run_view.main([str(CAMPAIGN), "--out", str(named)]) == 0
    assert named.read_text(encoding="utf-8").startswith("<!doctype html>")


def test_empty_folder_fails(tmp_path, capsys):
    assert run_view.main([str(tmp_path)]) == 1
    assert "no runs found" in capsys.readouterr().err
