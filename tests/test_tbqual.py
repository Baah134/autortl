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
    def simulate(*args):
        result = next(results)
        (args[-1] / "sim_log.txt").write_text("TEST PASSED\n" if result[0] else "FAIL index=1 expected=2 got=3\nTEST FAILED: 1 errors\n")
        return result
    monkeypatch.setattr(tbqual, "xsim_run", simulate)
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


@pytest.mark.parametrize("increment, mutated", [("1'b1", "1'b0"), ("8'd1", "8'd2"), ("4'h1", "4'h2"), ("1", "+ 2")])
def test_sized_increment_mutation_changes_value(increment, mutated):
    source, _ = mutate(f"module m; assign y = x + {increment}; endmodule")
    assert mutated in source
    assert "+ 2'b1" not in source


def test_comments_do_not_qualify_as_a_mutation():
    assert mutate("module m; // a < b + 1\nassign y=x; endmodule") is None


@pytest.mark.parametrize("raw,expected",[
    ("FAIL index=3 expected=7 got=9\nTEST FAILED: 1 errors\n",True),
    (None,False), ("TEST FAILED: watchdog\n",False),
    ("FAIL index=3 expected=7 got=9\nTEST FAILED: watchdog\n",False),
    ("FAIL timeout\nTEST FAILED: 1 errors\n",False),
    ("FAIL mismatch\nTEST FAILED: 1 errors\nTEST PASSED\n",False),
    ("TEST FAILED: 1 errors\n",False),("FAIL mismatch\n",False)])
def test_raw_assertion_proof_rejects_generic_or_ambiguous_failure(tmp_path,raw,expected):
    if raw is not None: (tmp_path/"sim_log.txt").write_text(raw)
    assert tbqual.assertion_failure_proof(tmp_path)[0] is expected


def test_qualification_wrapper_failure_without_raw_assertions_is_not_proof(tmp_path,monkeypatch):
    results=iter([(True,"",FailureKind.DESIGN),(False,"testbench reported failure",FailureKind.DESIGN)])
    monkeypatch.setattr(tbqual,"xsim_run",lambda *args:next(results))
    assert not tbqual.qualify("assign y=a+1;",tmp_path/"tb.v","m",RunConfig(mode="build"),tmp_path)[0]
