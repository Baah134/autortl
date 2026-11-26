"""PPA measurement gates and report parsing on fixture Vivado reports; no Vivado, models or simulators."""
import hashlib
import json
from pathlib import Path

import pytest

from autortl.triage import FailureKind
from benchmark import artifacts, ppa

OOC = Path(__file__).parent / "fixtures" / "ooc"
TOP = "dot4_pipeline"  # the design named in the OOC fixture reports
PART = "xc7a35tcpg236-1"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


MANIFEST = {
    "schema": 1,
    "identity": {"dataset": {"commit": "1" * 40, "format": "synthetic"}, "source_commit": "2" * 40,
                 "runtime": {"commit": "3" * 40, "sha256": "4" * 64},
                 "requested_model": "synthetic-model", "observed_model": None},
    "tasks": [{"id": "t1", "public_files": [{"path": "p.txt", "sha256": "5" * 64}],
               "private_files": [{"path": "q.txt", "sha256": "6" * 64}]}],
    "cells": [{"task": "t1", "trial": 0, "arm": arm,
               "budget": {"model_calls": 1 if arm == "single_call" else 3, "tool_seconds": 5.0, "wall_seconds": 10},
               "verification_policy": "full"} for arm in ("single_call", "full")],
}


def make_run(tmp_path: Path, arm="full", missing=False) -> tuple[Path, dict]:
    """A sealed run directory and its upstream-passing verdict."""
    source = tmp_path / f"src-{arm}"
    source.mkdir(parents=True)
    raw = f"module {TOP}(input clk, input a, output reg y); always @(posedge clk) y <= a; endmodule\n".encode()
    (source / "top.v").write_bytes(raw)
    run = tmp_path / "runs" / f"t1-{arm}-0"
    run.mkdir(parents=True)
    cell = {"task": "t1", "trial": 0, "arm": arm}
    if missing:
        receipt = artifacts.record_missing(MANIFEST, cell, destination=run / "submission", termination="failed")
    else:
        receipt = artifacts.seal_candidate(MANIFEST, cell, source_root=source,
                                           files=[{"path": "top.v", "sha256": sha(raw), "role": "rtl"}],
                                           destination=run / "submission", top=TOP, internal_status="accepted",
                                           selection_reason="accepted_incumbent", termination="done")
    (run / "run.json").write_text(json.dumps({"receipt_id": receipt["id"], "termination": "done"}),
                                  encoding="utf-8")
    verdict = {"task": "t1", "status": "pass", "upstream_pass": True, "receipt_id": receipt["id"],
               "cell": cell, "internal_status": "accepted"}
    return run, verdict


def fake_synth(reports=OOC, ok=True, kind=FailureKind.DESIGN, edit=None, calls=None):
    """A run_synthesis double that drops fixture reports into the work directory."""
    def synth(files, top, cfg, work, timeout=900):
        if calls is not None:
            calls.append({"files": [Path(f).name for f in files], "top": top, "cfg": cfg, "timeout": timeout})
        work.mkdir(parents=True, exist_ok=True)
        if ok:
            for name in ppa.REPORTS:
                text = (reports / name).read_text(encoding="utf-8")
                (work / name).write_text(edit(name, text) if edit else text, encoding="utf-8")
        return ok, "" if ok else "ERROR: [Synth 8-439] module 'x' not found", kind
    return synth


# ------------------------------------------------------------------ parsing
def test_parse_reports_reads_routed_ooc_fixture():
    m = ppa.parse_reports(OOC, TOP, PART)
    assert (m["lut"], m["ff"], m["dsp"], m["bram"]) == (17, 18, 4, 0.0)
    assert (m["wns_ns"], m["whs_ns"], m["timing_met"], m["no_timing_paths"]) == (7.267, 0.346, True, False)
    assert m["tool_version"].startswith("Vivado v.2025.2")


@pytest.mark.parametrize("name,old,new,match", [
    ("utilization_routed.rpt", "Design State : Routed", "Design State : Synthesized", "not a routed"),
    ("timing_routed.rpt", "Design State : Routed", "Design State : Synthesized", "not a routed"),
    ("utilization_routed.rpt", f"Design       : {TOP}", "Design       : other_top", "not 'dot4_pipeline'"),
    ("utilization_routed.rpt", f"Device       : {PART}", "Device       : xc7a100tcsg324-1", "not 'xc7a35t"),
    ("utilization_routed.rpt", "| Slice LUTs ", "| Slice LUTx ", "no parsable LUT"),
    ("timing_routed.rpt", "WNS(ns)", "XNS(ns)", "no WNS/WHS"),
])
def test_parse_reports_refuses_untrustworthy_reports(tmp_path, name, old, new, match):
    for report in ppa.REPORTS:
        text = (OOC / report).read_text(encoding="utf-8")
        if report == name:
            assert old in text
            text = text.replace(old, new)
        (tmp_path / report).write_text(text, encoding="utf-8")
    with pytest.raises(ppa.PpaError, match=match):
        ppa.parse_reports(tmp_path, TOP, PART)


def test_parse_reports_needs_routed_reports_not_post_synthesis_ones(tmp_path):
    (tmp_path / "utilization.rpt").write_text((OOC / "utilization_routed.rpt").read_text(encoding="utf-8"))
    (tmp_path / "timing_routed.rpt").write_text((OOC / "timing_routed.rpt").read_text(encoding="utf-8"))
    with pytest.raises(ppa.PpaError, match="utilization_routed.rpt is missing"):
        ppa.parse_reports(tmp_path, TOP, PART)


def test_no_timing_paths_marker_counts_only_when_vivado_reported_no_slack(tmp_path):
    for report in ppa.REPORTS:
        text = (OOC / report).read_text(encoding="utf-8")
        if report == "timing_routed.rpt":
            text = text.replace("WNS(ns)", "XNS(ns)").replace("WHS(ns)", "XHS(ns)")
        (tmp_path / report).write_text(text, encoding="utf-8")
    (tmp_path / "no_timing_paths.txt").write_text("no_paths period_ns 10.000\n", encoding="utf-8")
    m = ppa.parse_reports(tmp_path, TOP, PART)
    assert (m["wns_ns"], m["whs_ns"], m["timing_met"], m["no_timing_paths"]) == (10.0, 0.0, True, True)


# ---------------------------------------------------------------- measuring
def test_measure_seals_a_passing_submission_with_the_fixed_flow(tmp_path):
    run, verdict = make_run(tmp_path)
    calls = []
    record = ppa.measure(run, verdict, tmp_path / "ppa" / "t1-full-0", vivado_bin="vivado.bat",
                         synthesize=fake_synth(calls=calls))
    assert record["status"] == "measured" and record["metrics"]["lut"] == 17
    assert record["cell"] == {"task": "t1", "arm": "full", "trial": 0} and record["top"] == TOP
    assert record["flow"] == dict(ppa.FLOW, template_sha256=ppa.template_sha256())
    cfg = calls[0]["cfg"]
    assert (cfg.implementation, cfg.target_part, cfg.target_period_ns) == ("out_of_context", PART, 10.0)
    assert calls[0]["files"] == ["top.v"] and calls[0]["top"] == TOP
    assert [r["path"] for r in record["reports"]] == ["work/utilization_routed.rpt", "work/timing_routed.rpt"]
    assert ppa.load_record(tmp_path / "ppa" / "t1-full-0") == record
    assert record["tool_version"].startswith("Vivado v.2025.2") and "tool_version" not in record["metrics"]


def test_template_hash_pins_the_harness_ooc_template():
    from autortl import vivado
    assert ppa.template_sha256() == sha(vivado.OOC_SYNTH_TCL.encode("utf-8"))
    assert ppa.template_sha256("chip_top") != ppa.template_sha256()


def test_measure_refuses_a_functionally_failing_design(tmp_path):
    run, verdict = make_run(tmp_path)
    for bad in ({"upstream_pass": False}, {"upstream_pass": None}, {"receipt_id": "0" * 64},
                {"cell": {"task": "t1", "trial": 1, "arm": "full"}}):
        with pytest.raises(ppa.PpaError):
            ppa.measure(run, dict(verdict, **bad), tmp_path / "out", vivado_bin="v", synthesize=fake_synth())
        assert not (tmp_path / "out").exists()  # refused before anything is written


def test_measure_refuses_unsealed_tampered_or_missing_submissions(tmp_path):
    run, verdict = make_run(tmp_path)
    (run / "submission" / "rtl" / "top.v").write_text("module evil; endmodule\n")
    with pytest.raises(ppa.PpaError, match="not a sealed artifact"):
        ppa.measure(run, verdict, tmp_path / "a", vivado_bin="v", synthesize=fake_synth())
    (run / "run.json").unlink()
    with pytest.raises(ppa.PpaError, match="not sealed"):
        ppa.measure(run, verdict, tmp_path / "b", vivado_bin="v", synthesize=fake_synth())
    run2, verdict2 = make_run(tmp_path / "m", arm="single_call", missing=True)
    with pytest.raises(ppa.PpaError, match="missing-output"):
        ppa.measure(run2, verdict2, tmp_path / "c", vivado_bin="v", synthesize=fake_synth())


def test_measure_never_overwrites_an_existing_record(tmp_path):
    run, verdict = make_run(tmp_path)
    out = tmp_path / "out"
    ppa.measure(run, verdict, out, vivado_bin="v", synthesize=fake_synth())
    with pytest.raises(FileExistsError):
        ppa.measure(run, verdict, out, vivado_bin="v", synthesize=fake_synth())


@pytest.mark.parametrize("kind", [FailureKind.INFRA, FailureKind.UNKNOWN])
def test_infrastructure_failure_writes_no_record(tmp_path, kind):
    run, verdict = make_run(tmp_path)
    with pytest.raises(ppa.PpaInfraError):
        ppa.measure(run, verdict, tmp_path / "out", vivado_bin="v", synthesize=fake_synth(ok=False, kind=kind))
    assert not (tmp_path / "out" / ppa.RECORD).exists()


def test_design_synthesis_failure_is_a_sealed_outcome_without_metrics(tmp_path):
    run, verdict = make_run(tmp_path)
    record = ppa.measure(run, verdict, tmp_path / "out", vivado_bin="v", synthesize=fake_synth(ok=False))
    assert record["status"] == "synth_failed" and record["metrics"] is None
    assert record["failure_kind"] == "design" and "Synth 8-439" in record["failure"]


def test_measure_surfaces_report_errors_instead_of_recording_zero(tmp_path):
    run, verdict = make_run(tmp_path)
    edit = lambda name, text: text.replace("Design State : Routed", "Design State : Placed")  # noqa: E731
    with pytest.raises(ppa.PpaError, match="not a routed"):
        ppa.measure(run, verdict, tmp_path / "out", vivado_bin="v", synthesize=fake_synth(edit=edit))
    assert not (tmp_path / "out" / ppa.RECORD).exists()


def test_flow_identity_refuses_a_chip_top_or_malformed_flow():
    with pytest.raises(ppa.PpaError, match="out of context"):
        ppa.flow_identity(dict(ppa.FLOW, implementation="chip_top"))
    with pytest.raises(ppa.PpaError, match="exactly"):
        ppa.flow_identity({"implementation": "out_of_context", "part": PART})
    with pytest.raises(ppa.PpaError, match="period"):
        ppa.flow_identity(dict(ppa.FLOW, period_ns=0))
    assert ppa.flow_identity(dict(ppa.FLOW, period_ns=5))["period_ns"] == 5.0


def test_load_record_detects_edits_to_the_record_or_its_reports(tmp_path):
    run, verdict = make_run(tmp_path)
    out = tmp_path / "out"
    ppa.measure(run, verdict, out, vivado_bin="v", synthesize=fake_synth())
    report = out / "work" / "utilization_routed.rpt"
    original = report.read_bytes()
    report.write_bytes(original.replace(b"|   17 |", b"|   12 |"))
    with pytest.raises(ppa.PpaError, match="changed after sealing"):
        ppa.load_record(out)
    report.write_bytes(original)
    record = json.loads((out / ppa.RECORD).read_bytes())
    record["metrics"]["lut"] = 3
    (out / ppa.RECORD).write_text(json.dumps(record))
    with pytest.raises(ppa.PpaError, match="identity mismatch"):
        ppa.load_record(out)


# ------------------------------------------------------------- attempt-wide
def make_attempt(tmp_path):
    attempt = tmp_path / "attempt"
    rows = []
    for arm, passed in (("single_call", True), ("full", False)):
        run, verdict = make_run(attempt, arm=arm)
        verdict["upstream_pass"] = passed
        grade = attempt / "grades" / f"t1-{arm}-0"
        grade.mkdir(parents=True)
        (grade / "verdict.json").write_text(json.dumps(verdict), encoding="utf-8")
        rows.append({"task": "t1", "arm": arm, "trial": 0, "upstream_pass": passed})
    (attempt / "grades" / "summary.json").write_text(json.dumps(rows), encoding="utf-8")
    return attempt


def test_measure_attempt_measures_passing_cells_only_and_resumes(tmp_path):
    attempt = make_attempt(tmp_path)
    calls = []
    first = ppa.measure_attempt(attempt, vivado_bin="v", synthesize=fake_synth(calls=calls), log=lambda *_: None)
    assert [r["cell"]["arm"] for r in first["measured"]] == ["single_call"] and first["skipped_failing"] == 1
    again = ppa.measure_attempt(attempt, vivado_bin="v", synthesize=fake_synth(calls=calls), log=lambda *_: None)
    assert len(calls) == 1 and again["measured"] == first["measured"]  # sealed cells are never re-synthesised
    assert ppa.collect(attempt) == first["measured"]


def test_measure_attempt_keeps_infra_leftovers_aside_and_retries(tmp_path):
    attempt = make_attempt(tmp_path)
    out = ppa.measure_attempt(attempt, vivado_bin="v", synthesize=fake_synth(ok=False, kind=FailureKind.INFRA),
                              log=lambda *_: None)
    assert out["infra"] == ["t1-single_call-0"] and out["measured"] == []
    retry = ppa.measure_attempt(attempt, vivado_bin="v", synthesize=fake_synth(), log=lambda *_: None)
    assert len(retry["measured"]) == 1
    assert (attempt / "ppa" / "t1-single_call-0.infra-1").is_dir()  # kept, not deleted or reused
    assert [r["cell"]["arm"] for r in ppa.collect(attempt)] == ["single_call"]
