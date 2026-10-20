import hashlib
import json
from pathlib import Path
from unittest.mock import Mock
import pytest
from scripts import check_generated_build as cli
from autortl.config import RunConfig
from autortl.triage import FailureKind


@pytest.fixture
def build(tmp_path):
    run = tmp_path / "build"; run.mkdir()
    spec = Path(__file__).resolve().parents[1] / "curriculum/tier1/counter8_build/design_spec.json"
    RunConfig(mode="build", top_module="counter8", spec_path=spec).save(run / "config.json")
    (run / "run_summary.json").write_text(json.dumps({"status":"done", "top_module":"counter8"}))
    (run / "counter8_best.v").write_text("winner")
    child = run / "modules/counter8_core"; child.mkdir(parents=True)
    (child / "counter8_core.v").write_text("exact child")
    (child / "mutant.v").write_text("must not include")
    tb = tmp_path / "independent.v"; tb.write_text("independent TB")
    return run, tb, tmp_path / "check"


def test_only_winner_and_declared_child_copied(build):
    run, tb, out = build
    _, top, sources, copied_tb = cli.prepare(run, tb, out)
    assert top == "counter8"
    assert [p.read_text() for p in sources] == ["winner", "exact child"]
    assert copied_tb.read_bytes() == tb.read_bytes()
    for row in json.loads((out / "inputs.json").read_text())["inputs"]:
        assert hashlib.sha256((out / row["copy"]).read_bytes()).hexdigest() == row["sha256"]
    with pytest.raises(FileExistsError): cli.prepare(run, tb, out)


@pytest.mark.parametrize("status", ["baseline_blocked", "building", "failed"])
def test_incomplete_build_is_not_checked(build, status):
    run, tb, out = build
    (run / "run_summary.json").write_text(json.dumps({"status":status, "top_module":"counter8"}))
    with pytest.raises(ValueError, match="not completed"): cli.prepare(run, tb, out)
    assert not out.exists()


@pytest.mark.parametrize("raw,passed,kind,expected", [
    ("TEST PASSED\n", True, FailureKind.DESIGN, 0),
    ("TEST PASSED\nFAIL wrong\n", True, FailureKind.DESIGN, 1),
    ("TEST FAILED: watchdog", False, FailureKind.DESIGN, 1),
    ("", True, FailureKind.DESIGN, 1),
    ("TEST PASSED\n", False, FailureKind.INFRA, 1),
])
def test_actual_raw_verdict_required(build, monkeypatch, raw, passed, kind, expected):
    run, tb, out = build
    def sim(sources, testbench, top, cfg, work, timeout):
        assert len(sources)==2 and top=="counter8_tb" and timeout==60
        (work / "sim_log.txt").write_text(raw)
        return passed, "controlled unit result", kind
    monkeypatch.setattr(cli,"xsim_run",Mock(side_effect=sim))
    assert cli.main(["--run",str(run),"--tb",str(tb),"--output",str(out)])==expected
    assert (out / "archive-manifest.json").is_file()
