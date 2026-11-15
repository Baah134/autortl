"""Evidence archiving of a graded attempt: contents, sanitising, audit-safe names."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from benchmark import archive

ROOT = Path(__file__).resolve().parents[1]


def make_attempt(root: Path, graded=True) -> Path:
    attempt = root / "attempt"
    (attempt / "runs").mkdir(parents=True)
    (attempt / "manifest.json").write_text(json.dumps({"schema": 1, "tasks": [
        {"id": "t1", "public_files": [{"path": "t1_prompt.txt", "sha256": "a" * 64}]}]}))
    (attempt / "runtime-identity.txt").write_text("commit abc tree def\n")
    (attempt / "campaign.log").write_text('{"event": "start", "out": "C:\\\\Users\\\\someone\\\\x"}\r\n')
    rows = []
    for arm, internal in (("single_call", "unverified"), ("full", "accepted")):
        name = f"t1-{arm}-0"
        run = attempt / "runs" / name
        (run / "submission" / "rtl" / "modules" / "TopModule").mkdir(parents=True)
        (run / "submission" / "rtl" / "modules" / "TopModule" / "TopModule.v").write_text(
            "// built in C:/Users/someone/work\nmodule TopModule(input a, output y); assign y = a; endmodule\n")
        (run / "run.json").write_text(json.dumps({
            "cell": {"task": "t1", "arm": arm, "trial": 0}, "receipt_id": "0" * 64, "kind": "candidate",
            "termination": "done",
            "accounting": {"llm_calls": 1, "seconds": 2.0, "command": ["C:\\Users\\someone\\python.exe", "run.py"]}}))
        if arm == "full":
            (run / "run").mkdir()
            (run / "run" / "run_summary.json").write_text(json.dumps(
                {"status": "done", "top_module": "TopModule", "run_dir": "C:\\Users\\someone\\r", "best_metrics": {}}))
        if graded:
            (attempt / "grades" / name).mkdir(parents=True)
            (attempt / "grades" / name / "verdict.json").write_text(json.dumps(
                {"status": "pass", "compile": {"cmd": ["iverilog", "C:/Users/someone/t1_test.sv"]}}))
        rows.append({"task": "t1", "arm": arm, "trial": 0, "termination": "done", "internal": internal,
                     "status": "pass", "upstream_code": ".", "upstream_pass": True, "mismatches": 0, "samples": 5,
                     "run_status": "done", "llm_calls": 1, "input_tokens": 10, "output_tokens": 2, "seconds": 2.0,
                     "tool_seconds": 0.0})
    if graded:
        (attempt / "grades" / "summary.json").write_text(json.dumps(rows))
    return attempt


def test_archive_contents_are_complete_sanitised_and_hashed(tmp_path):
    out = tmp_path / "evidence" / "result"
    out.parent.mkdir()
    manifest = archive.archive_attempt(make_attempt(tmp_path), out, title="Synthetic", forbidden=("someone",))
    names = {p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()}
    assert {"benchmark_registration.json", "runtime-identity.txt", "campaign.log", "summary.json", "cells.json",
            "report.md", "report.json", "archive-manifest.json",
            "rtl/t1-full-0__modules__TopModule__TopModule.v",
            "rtl/t1-single_call-0__modules__TopModule__TopModule.v"} == names
    for path in out.rglob("*"):
        if path.is_file():
            data = path.read_bytes()
            assert b"someone" not in data and b"\r\n" not in data, path.name
    cells = json.loads((out / "cells.json").read_text())
    assert "command" not in cells["t1-full-0"]["run"]["accounting"]
    assert cells["t1-full-0"]["run_summary"] == {"status": "done", "top_module": "TopModule"}
    assert cells["t1-full-0"]["verdict"]["compile"]["cmd"][1] == "<home>/t1_test.sv"
    assert (out / "report.md").read_text().startswith("# Synthetic")
    recorded = json.loads((out / "archive-manifest.json").read_text())
    assert recorded == manifest and "archive-manifest.json" not in recorded
    for name, digest in recorded.items():
        assert hashlib.sha256((out / name).read_bytes()).hexdigest() == digest


def test_only_the_archive_manifest_has_a_manifest_name(tmp_path):
    """A second *manifest*.json would be audited as an archive manifest (tools/evidence_audit.py)."""
    out = tmp_path / "result"
    archive.archive_attempt(make_attempt(tmp_path), out)
    assert [p.name for p in out.rglob("*") if "manifest" in p.name] == ["archive-manifest.json"]
    spec = importlib.util.spec_from_file_location("evidence_audit", ROOT / "tools" / "evidence_audit.py")
    audit = importlib.util.module_from_spec(spec)
    sys.modules["evidence_audit"] = audit  # dataclasses resolve the module by name
    try:
        spec.loader.exec_module(audit)
    finally:
        sys.modules.pop("evidence_audit", None)
    assert not audit.is_manifest("evidence/2026-11-15/x/benchmark_registration.json")
    assert audit.is_manifest("evidence/2026-11-15/x/archive-manifest.json")


def test_ungraded_attempt_and_existing_folder_are_refused(tmp_path):
    with pytest.raises(archive.ArchiveError, match="grade it first"):
        archive.archive_attempt(make_attempt(tmp_path, graded=False), tmp_path / "out")
    assert not (tmp_path / "out").exists()
    graded = make_attempt(tmp_path / "second")
    (tmp_path / "taken").mkdir()
    with pytest.raises(FileExistsError):
        archive.archive_attempt(graded, tmp_path / "taken")


def test_forbidden_word_surviving_sanitising_fails(tmp_path):
    attempt = make_attempt(tmp_path)
    (attempt / "runtime-identity.txt").write_text("built by someone\n")  # not a path: the sanitiser keeps it
    with pytest.raises(archive.ArchiveError, match="forbidden word"):
        archive.archive_attempt(attempt, tmp_path / "out", forbidden=("someone",))


def test_seal_after_adding_readme_and_cli(tmp_path):
    out = tmp_path / "result"
    attempt = make_attempt(tmp_path)
    assert archive.main(["--attempt", str(attempt), "--out", str(out), "--forbid", "someone"]) == 0
    (out / "README.md").write_bytes(b"# Result\n")
    assert archive.main(["--out", str(out), "--seal"]) == 0
    recorded = json.loads((out / "archive-manifest.json").read_text())
    assert recorded["README.md"] == hashlib.sha256(b"# Result\n").hexdigest()
    with pytest.raises(SystemExit):
        archive.main(["--out", str(tmp_path / "x")])
