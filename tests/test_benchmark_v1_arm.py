"""Opt-in arm full_xcheck (V1 request cross-check) with process doubles; no model, Vivado or Icarus.

Every existing arm must behave exactly as at v1.0.0: default manifests, commands,
run records, campaign order, graded rows and rendered reports are unchanged.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from benchmark import artifacts, campaign, pilot, report
from benchmark import verilogeval as ve
from tests.test_benchmark_report import grid, row

DATA = Path(__file__).parent / "fixtures" / "verilogeval" / "dataset"
REPO = Path(__file__).resolve().parents[1]
CATALOG = REPO / "benchmark" / "catalogs" / "verilogeval-c498220.json"
V1_BUDGETS = {"full": pilot.PROVISIONAL_BUDGETS["full"], **pilot.OPT_IN_BUDGETS}
CELL_KEYS = {"task", "trial", "arm", "budget", "verification_policy"}
CHECKS = {"policy": "request_traces",
          "checks": [{"revision": 0, "module": "TopModule", "spec_sha256": "a" * 64, "outcome": "replanned",
                      "spec_repair": 1, "traces": 2, "compared": 8, "mismatches": [{"cycle": 1}]},
                     {"revision": 1, "module": "TopModule", "spec_sha256": "b" * 64, "outcome": "agree",
                      "traces": 2, "compared": 8, "mismatches": []}]}


@pytest.fixture(autouse=True)
def fake_tools(monkeypatch):
    monkeypatch.setattr(pilot, "vivado_tools", lambda: {n: f"C:/Vivado/bin/{n}.bat" for n in ("vivado", "xvlog")})


def build(tasks=("Prob900_inv",), budgets=None, trials=1):
    return ve.build_manifest(DATA, list(tasks), dataset_commit="a" * 40, source_commit="b" * 40,
                             runtime_commit="c" * 40, runtime_sha256="d" * 64, requested_model="m",
                             budgets=V1_BUDGETS if budgets is None else budgets, trials=trials)


@pytest.fixture
def task():
    return ve.load_task(DATA, "Prob900_inv")


class Build:
    """run.py double: a DONE winner and a run summary, optionally with spec_cross_check."""

    def __init__(self, cross_check=None, status="done"):
        self.cmd, self.cross_check, self.status = None, cross_check, status

    def __call__(self, cmd, cwd, capture_output, text, errors, timeout):
        self.cmd = cmd
        run_dir = Path(cmd[cmd.index("--output-dir") + 1])
        run_dir.mkdir(parents=True)
        summary = {"status": self.status, "top_module": "TopModule"}
        if self.cross_check is not None:
            summary["spec_cross_check"] = self.cross_check
        (run_dir / "run_summary.json").write_text(json.dumps(summary))
        (run_dir / "budget.json").write_text(json.dumps({"llm_calls": 9, "vivado_seconds": 30.0, "tokens": {}}))
        (run_dir / "TopModule_best.v").write_text("module TopModule(input a, output y); assign y=~a; endmodule\n")
        return subprocess.CompletedProcess(cmd, 0, "", "")


# ------------------------------------------------------------- registration
def test_default_arm_sets_never_include_full_xcheck():
    assert "full_xcheck" not in pilot.PROVISIONAL_BUDGETS
    assert pilot.OPT_IN_BUDGETS["full_xcheck"] == pilot.PROVISIONAL_BUDGETS["full"]  # same caps (draft "Arms")
    manifest = build(budgets=pilot.PROVISIONAL_BUDGETS)
    assert [c["arm"] for c in manifest["cells"]] == ["ablation", "full", "single_call"]
    assert all(set(c) == CELL_KEYS for c in manifest["cells"])  # v1.0.0 cells, no new key


def test_full_xcheck_cells_declare_request_traces_and_full_verification():
    cells = {c["arm"]: c for c in build()["cells"]}
    assert cells["full_xcheck"]["spec_cross_check"] == "request_traces"
    assert cells["full_xcheck"]["verification_policy"] == "full"
    assert set(cells["full"]) == CELL_KEYS


@pytest.mark.parametrize("arm, declared, accepted", [
    ("full_xcheck", None, False), ("full_xcheck", "off", False), ("full_xcheck", "request_traces", True),
    ("full", "request_traces", False), ("full", "off", True), ("ablation", "request_traces", False),
    ("single_call", "off", True), ("full_xcheck", "sometimes", False)])
def test_manifest_refuses_an_arm_and_cross_check_mismatch(arm, declared, accepted):
    manifest = build(budgets={**pilot.PROVISIONAL_BUDGETS, **pilot.OPT_IN_BUDGETS})
    cell = next(c for c in manifest["cells"] if c["arm"] == arm)
    cell.pop("spec_cross_check", None)
    if declared is not None:
        cell["spec_cross_check"] = declared
    if accepted:
        artifacts._manifest(manifest)
    else:
        with pytest.raises(artifacts.ArtifactError, match="spec cross-check"):
            artifacts._manifest(manifest)


def test_cli_manifest_adds_full_xcheck_only_when_named(tmp_path, monkeypatch):
    monkeypatch.setattr(pilot, "_git_head", lambda: "f" * 40)
    base = ["manifest", "--dataset", str(DATA), "--commit", "a" * 40, "--tasks", "Prob900_inv",
            "--runtime-sha256", "0" * 64]
    assert pilot.main(base + ["--out", str(tmp_path / "default.json")]) == 0
    default = artifacts.load_manifest(tmp_path / "default.json", public_root=DATA, private_root=DATA)
    assert sorted(c["arm"] for c in default["cells"]) == ["ablation", "full", "single_call"]
    assert pilot.main(base + ["--arms", "full", "full_xcheck", "--out", str(tmp_path / "v1.json")]) == 0
    v1 = artifacts.load_manifest(tmp_path / "v1.json", public_root=DATA, private_root=DATA)
    assert [(c["arm"], c.get("spec_cross_check")) for c in v1["cells"]] == [
        ("full", None), ("full_xcheck", "request_traces")]


# ------------------------------------------------------------------ command
def test_command_with_cross_check_off_is_unchanged(tmp_path):
    budget = pilot.PROVISIONAL_BUDGETS["full"]
    plain = pilot.full_command(tmp_path / "p.txt", tmp_path / "r", budget, python="py")
    assert pilot.full_command(tmp_path / "p.txt", tmp_path / "r", budget, python="py", spec_cross_check="off") == plain
    assert "--spec-cross-check" not in plain
    checked = pilot.full_command(tmp_path / "p.txt", tmp_path / "r", budget, python="py",
                                 spec_cross_check="request_traces")
    flag = checked.index("--spec-cross-check")
    assert checked[flag + 1] == "request_traces" and checked.count("--spec-cross-check") == 1
    assert checked[:flag] + checked[flag + 2:] == plain  # nothing else differs


def test_full_xcheck_runs_the_flag_and_records_the_outcomes(task, tmp_path):
    manifest, xcheck, full = build(), Build(CHECKS), Build(CHECKS)
    record = pilot.run_full(manifest, task, tmp_path / "x", runner=xcheck, python="py", arm="full_xcheck")
    pilot.run_full(manifest, task, tmp_path / "c", runner=full, python="py")
    assert xcheck.cmd[xcheck.cmd.index("--spec-cross-check") + 1] == "request_traces"
    assert "--spec-cross-check" not in full.cmd and "--verification-policy" not in xcheck.cmd
    assert record["accounting"]["spec_cross_check"] == CHECKS and record["kind"] == "candidate"
    written = json.loads((tmp_path / "c" / "run.json").read_text())
    assert "spec_cross_check" not in written["accounting"]  # arm C's run record is unchanged
    receipt = artifacts.load_artifact(tmp_path / "x" / "submission", expected_id=record["receipt_id"])
    assert receipt["cell"]["arm"] == "full_xcheck" and receipt["cell"]["spec_cross_check"] == "request_traces"


def test_full_xcheck_without_a_run_summary_records_none(task, tmp_path):
    def died(cmd, **kwargs):
        Path(cmd[cmd.index("--output-dir") + 1]).mkdir(parents=True)
        return subprocess.CompletedProcess(cmd, 1, "", "")
    record = pilot.run_full(build(), task, tmp_path / "x", runner=died, python="py", arm="full_xcheck")
    assert record["accounting"]["spec_cross_check"] is None and record["termination"] == "interrupted"


@pytest.mark.parametrize("arm, declared, message", [
    ("full_xcheck", "off", "full_xcheck cell must declare spec_cross_check request_traces"),
    ("full_xcheck", None, "full_xcheck cell must declare spec_cross_check request_traces"),
    ("full", "request_traces", "full cell must declare spec_cross_check off")])
def test_run_full_refuses_a_cell_whose_arm_and_cross_check_disagree(task, tmp_path, arm, declared, message):
    manifest = build()
    cell = next(c for c in manifest["cells"] if c["arm"] == arm)
    cell.pop("spec_cross_check", None)
    if declared is not None:
        cell["spec_cross_check"] = declared
    with pytest.raises(ve.AdapterError, match=message):
        pilot.run_full(manifest, task, tmp_path / "x", runner=Build(), arm=arm)
    assert not (tmp_path / "x").exists()


def test_run_full_still_refuses_single_call(task, tmp_path):
    with pytest.raises(ve.AdapterError, match="full or ablation"):
        pilot.run_full(build(), task, tmp_path / "x", runner=Build(), arm="single_call")


def test_full_xcheck_command_passes_real_run_py_validation(task, tmp_path):
    """The flag reaches run.py's parser and RunConfig; a zero model budget stops before any model call."""
    request = tmp_path / task.prompt.name
    request.write_bytes(task.prompt.read_bytes())
    budget = dict(pilot.OPT_IN_BUDGETS["full_xcheck"], model_calls=0)
    cmd = pilot.full_command(request, tmp_path / "run", budget, python=sys.executable,
                             spec_cross_check="request_traces")
    done = subprocess.run(cmd, cwd=str(pilot.REPO), capture_output=True, text=True, timeout=120)
    assert "error:" not in done.stderr and "must be one of" not in done.stderr, done.stderr
    summary = json.loads((tmp_path / "run" / "run_summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "budget_exhausted"


# ----------------------------------------------------------------- campaign
def test_campaign_puts_full_xcheck_right_after_full():
    manifest = build(tasks=("Prob901_and2", "Prob900_inv"), budgets={**pilot.PROVISIONAL_BUDGETS,
                                                                    **pilot.OPT_IN_BUDGETS}, trials=2)
    cells = campaign.ordered_cells(manifest)
    assert cells[:4] == [("Prob901_and2", "single_call", 0), ("Prob901_and2", "ablation", 0),
                         ("Prob901_and2", "full", 0), ("Prob901_and2", "full_xcheck", 0)]
    assert len(cells) == 16 and {c[2] for c in cells[:8]} == {0}


def test_campaign_order_without_full_xcheck_is_unchanged():
    manifest = build(tasks=("Prob901_and2", "Prob900_inv"), budgets=pilot.PROVISIONAL_BUDGETS)
    assert [c[1] for c in campaign.ordered_cells(manifest)] == ["single_call", "ablation", "full"] * 2


def test_campaign_dispatches_full_xcheck_to_the_harness_runner(tmp_path, monkeypatch, task):
    seen = []
    monkeypatch.setattr(pilot, "run_full", lambda m, t, o, trial, model, arm: seen.append((arm, trial, model)) or {})
    campaign.run_cell(build(), task, ("Prob900_inv", "full_xcheck", 0), tmp_path / "x", "pinned")
    assert seen == [("full_xcheck", 0, "pinned")]


# ------------------------------------------------------------------ grading
def test_graded_rows_carry_outcomes_only_for_full_xcheck(tmp_path, monkeypatch, task):
    manifest = build()
    pilot.run_full(manifest, task, tmp_path / "runs" / "Prob900_inv-full-0", runner=Build(CHECKS))
    pilot.run_full(manifest, task, tmp_path / "runs" / "Prob900_inv-full_xcheck-0", runner=Build(CHECKS),
                   arm="full_xcheck")
    monkeypatch.setattr(ve, "grade", lambda files, task, workdir, **kw: (
        Path(workdir).mkdir(parents=True) or {"task": task.id, "status": "fail", "upstream_code": "R",
                                                "upstream_pass": False, "mismatches": 2, "samples": 20}))
    rows = {r["arm"]: r for r in report.grade_attempt(manifest, DATA, tmp_path)}
    assert set(rows["full"]) == set(report.ROW_KEYS)
    assert set(rows["full_xcheck"]) == set(report.ROW_KEYS) | set(report.XCHECK_ROW_KEYS)
    assert rows["full_xcheck"]["cross_check_policy"] == "request_traces"
    assert rows["full_xcheck"]["cross_check_outcomes"] == ["replanned", "agree"]


@pytest.mark.parametrize("recorded, fields", [
    (None, (None, None)), ({"policy": "off", "checks": []}, ("off", [])),
    (CHECKS, ("request_traces", ["replanned", "agree"])), ({"policy": "request_traces"}, ("request_traces", None))])
def test_cross_check_fields_copy_what_the_run_recorded(recorded, fields):
    got = report.cross_check_fields(recorded)
    assert (got["cross_check_policy"], got["cross_check_outcomes"]) == fields


# ------------------------------------------------------------------- report
def xrow(task, trial, passed, outcomes, internal="accepted", **extra):
    fields = {"cross_check_policy": "request_traces", "cross_check_outcomes": outcomes, **extra}
    return row(task, "full_xcheck", trial, passed, internal=internal, calls=8, **fields)


def test_summary_without_full_xcheck_has_exactly_the_old_keys():
    s = report.summarize(grid({"single_call": {"t1": [True]}, "full": {"t1": [True]}}), samples=50)
    assert set(s) == {"tasks", "cells", "arms", "paired", "categories", "bootstrap"}
    assert list(s["paired"]) == ["full-single_call"]
    assert "Request cross-check" not in report.render_markdown(s) and "C-xcheck" not in report.render_markdown(s)


def test_paired_comparisons_add_full_xcheck_minus_full_last():
    passes = {arm: {"t1": [True], "t2": [False]} for arm in ("single_call", "ablation", "full")}
    rows = grid(passes) + [xrow("t1", 0, True, ["agree"]), xrow("t2", 0, True, ["replanned", "agree"])]
    s = report.summarize(rows, samples=200)
    assert list(s["paired"]) == ["full-single_call", "full-ablation", "ablation-single_call", "full_xcheck-full"]
    assert s["paired"]["full_xcheck-full"]["mean_difference"] == 0.5
    md = report.render_markdown(s)
    assert "| C-xcheck full harness + request cross-check minus C full harness | +50.0 |" in md


def test_paired_false_acceptance_is_per_evaluable_cell_and_counts_event_tasks():
    rows = [row("t1", "full", n, False) for n in range(2)] + [row("t1", "full", 2, True)]
    rows += [row("t2", "full", n, False, internal="rejected") for n in range(3)]
    rows += [row("t3", "full", 0, False), row("t3", "full", 1, True, termination="interrupted")]
    rows += [xrow("t1", 0, True, ["agree"]), xrow("t1", 1, False, ["disagreement_kept"]),
             xrow("t1", 2, True, ["replanned", "agree"])]
    rows += [xrow("t2", n, False, ["agree"], internal="rejected") for n in range(3)]
    rows += [xrow("t3", 0, True, ["skipped"]), xrow("t3", 1, True, ["agree"])]
    s = report.summarize(rows, samples=500)
    fa = s["paired_false_acceptance"]["full_xcheck-full"]
    # FA_t off: t1 2/3, t2 0, t3 1/1 (the interrupted cell is excluded); xcheck: t1 1/3, t2 0, t3 0.
    assert fa["mean_difference"] == pytest.approx(((1 / 3 - 2 / 3) + 0 + (0 - 1)) / 3)
    assert fa["tasks_compared"] == 3 and (fa["tasks_fewer"], fa["tasks_equal"], fa["tasks_more"]) == (2, 1, 0)
    assert fa["tasks_with_false_acceptance"] == {"full_xcheck": 1, "full": 2}
    assert fa["ci95_task_bootstrap"][1] <= 0
    md = report.render_markdown(s)
    assert "Paired false acceptance, C-xcheck full harness + request cross-check minus C full harness" in md


def test_cross_check_counts_outcomes_cells_and_blocked_tasks():
    rows = [row(t, "full", n, True) for t in ("t1", "t2", "t3") for n in range(2)]
    rows += [xrow("t1", 0, False, ["replanned", "disagreement_kept"]), xrow("t1", 1, False, ["agree"])]
    rows += [xrow("t2", 0, False, ["agree"]), xrow("t2", 1, False, ["skipped"])]  # no disagreement: not blocked
    rows += [xrow("t3", 0, True, ["replanned", "agree"]),
             xrow("t3", 1, False, None, cross_check_policy=None, termination="failed")]
    x = report.summarize(rows, samples=200)["cross_check"]
    assert x["cells"] == 6 and x["cells_checked"] == 4
    assert x["outcomes"] == {"agree": 3, "disagreement_kept": 1, "replanned": 2, "skipped": 1}
    assert x["cells_by_outcome"] == {"agree": 3, "disagreement_kept": 1, "replanned": 2, "skipped": 1}
    assert x["policies"] == {"None": 1, "request_traces": 5} and x["cells_without_record"] == ["t3#1"]
    assert x["replanned_cells"] == ["t1#0", "t3#0"] and x["disagreement_kept_cells"] == ["t1#0"]
    assert x["blocked_tasks"] == [{"task": "t1", "cells": ["t1#0"]}]
    assert x["replans_passing"] == ["t3#0"] and x["replans_failing_where_off_passed"] == ["t1#0"]
    md = report.render_markdown(report.summarize(rows, samples=200))
    assert "## Request cross-check (C-xcheck full harness + request cross-check)" in md
    assert "| replanned | 2 | 2 |" in md and "t1 (t1#0)" in md


def test_full_xcheck_alone_has_counts_but_no_pairing():
    s = report.summarize([xrow("t1", 0, True, ["agree"])], samples=50)
    assert "paired_false_acceptance" not in s and s["paired"] == {}
    assert s["cross_check"]["blocked_tasks"] is None
    assert "Blocked tasks" not in report.render_markdown(s)


@pytest.mark.parametrize("folder", ["evidence/2026-11-21/final-02-results", "evidence/2026-11-26/flash-03-results"])
def test_archived_reports_render_byte_identically(folder):
    """v1.0.0 behaviour: the committed final-02 and flash-03 reports re-render exactly from their rows."""
    root = REPO / folder
    rows = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    original = (root / "report.md").read_bytes().decode("utf-8")
    title = original.split("\n", 1)[0][2:]
    summary = report.summarize(rows, json.loads(CATALOG.read_text(encoding="utf-8")))
    assert report.render_markdown(summary, title) == original
    assert json.loads(json.dumps(summary)) == json.loads((root / "report.json").read_text(encoding="utf-8"))
