from autortl.tbqual import mutate
import pytest
from autortl import tbqual
from autortl.config import RunConfig
from autortl.triage import FailureKind


@pytest.mark.parametrize("outcome, expected", [
    ((False, "Testbench failures:\nFAIL mismatch", FailureKind.DESIGN), True),
    ((False, "testbench reported failure", FailureKind.DESIGN), True),
    ((False, "license unavailable", FailureKind.INFRA), False),
    ((False, "syntax error", FailureKind.DESIGN), False),
    ((False, "Simulation ended without clear pass/fail", FailureKind.UNKNOWN), False),
    ((False, "timed out after 300s", FailureKind.INFRA), False),
    ((False, "Fatal error in simulation", FailureKind.UNKNOWN), False),
    ((True, "", FailureKind.DESIGN), False),
])
def test_qualification_requires_control_and_explicit_mutant_failure(
        monkeypatch, tmp_path, outcome, expected):
    results = iter([(True, "", FailureKind.DESIGN), outcome])
    monkeypatch.setattr(tbqual, "xsim_run", lambda *a: next(results))
    ok, _ = tbqual.qualify("assign y = a + 1;", tmp_path / "tb.v", "m",
                           RunConfig(mode="build"), tmp_path)
    assert ok is expected
    assert next(results, None) is None


def test_failed_control_cannot_qualify(monkeypatch, tmp_path):
    calls = []
    def run(*args):
        calls.append(args)
        return False, "testbench reported failure", FailureKind.DESIGN
    monkeypatch.setattr(tbqual, "xsim_run", run)
    assert not tbqual.qualify("assign y = a + 1;", tmp_path / "tb.v", "m",
                              RunConfig(mode="build"), tmp_path)[0]
    assert len(calls) == 1


def test_no_mutation_does_not_qualify(tmp_path):
    assert not tbqual.qualify("assign y = a;", tmp_path / "tb.v", "m",
                              RunConfig(mode="build"), tmp_path)[0]


def test_mutation_changes_behavior():
    v = "module m; assign y = (a < b); endmodule"
    m = mutate(v)
    assert m is not None
    mutated, desc = m
    assert mutated != v and "<" in desc


def test_no_mutation_possible():
    assert mutate("module m; assign y = x; endmodule") is None
