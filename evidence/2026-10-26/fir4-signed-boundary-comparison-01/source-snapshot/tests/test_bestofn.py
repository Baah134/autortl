import pytest

from autortl.bestofn import Candidate, mutation_prompts, dedupe, select


def test_portfolio_matches_objective():
    names = [n for n, _ in mutation_prompts("maximize_freq", 4)]
    assert "pipeline" in names and "wildcard" in names


def test_dedupe_kills_exact_duplicates():
    a = Candidate("module m; assign y = x; endmodule", "standard")
    b = Candidate(a.verilog, "narrow")
    candidates = [a, b]
    survivors = dedupe(candidates)
    assert survivors == [a]
    assert survivors[0] is a
    assert candidates == [a, b]
    assert a.alive and a.fail_reason == ""
    assert not b.alive
    assert b.fail_reason == "duplicate of 'standard' candidate"


@pytest.mark.parametrize("first,second", [
    ("module m; assign y = x; endmodule",
     "module m;  assign y=x;  endmodule // cosmetic variant"),
    ('module m(output [15:0] y); assign y = "//A"; endmodule',
     'module m(output [15:0] y); assign y = "//B"; endmodule'),
    ('module m(output [31:0] y); assign y = " A"; endmodule',
     'module m(output [31:0] y); assign y = "  A"; endmodule'),
    ('module m(output [15:0] y); assign y = "/*A*/"; endmodule',
     'module m(output [15:0] y); assign y = "/*B*/"; endmodule'),
    ('`define VALUE 1\nmodule m(output y); assign y = `VALUE; endmodule',
     '`define VALUE 1\r\nmodule m(output y); assign y = `VALUE; endmodule'),
    ('module m(input \\a+b , input b, output y); assign y = \\a+b ; endmodule',
     'module m(input \\a , input b, output y); assign y = \\a +b; endmodule'),
    ('module m; // cafÃ©\nendmodule', 'module m; // cafe\nendmodule'),
], ids=["cosmetic", "line-comment-in-string", "literal-whitespace",
        "block-comment-in-string", "macro-newline", "escaped-identifier", "utf8"])
def test_dedupe_retains_distinct_sources(first, second):
    a = Candidate(first, "standard")
    b = Candidate(second, "narrow")
    assert dedupe([a, b]) == [a, b]
    assert a.alive and b.alive
    assert a.fail_reason == b.fail_reason == ""


def test_dedupe_preserves_order_and_first_duplicate_identity():
    a = Candidate("module a; endmodule", "standard")
    b = Candidate("module b; endmodule", "narrow")
    duplicate = Candidate(a.verilog, "share")
    c = Candidate("module c; endmodule", "wildcard")
    survivors = dedupe([a, b, duplicate, c])
    assert len(survivors) == 3
    assert all(actual is expected for actual, expected in zip(survivors, [a, b, c]))
    assert not duplicate.alive
    assert duplicate.fail_reason == "duplicate of 'standard' candidate"


def test_dedupe_keeps_existing_dead_candidate_behavior():
    a = Candidate("module a; endmodule", "standard", alive=False,
                  fail_reason="previous verification failure")
    duplicate = Candidate(a.verilog, "narrow")
    b = Candidate("module b; endmodule", "share")
    assert dedupe([a, duplicate, b]) == [b]
    assert not a.alive and a.fail_reason == "previous verification failure"
    assert not duplicate.alive
    assert dedupe([]) == []


def test_selection_prefers_more_rungs_then_metric():
    a = Candidate("module a; endmodule", "standard",
                  ladder_rungs_passed=5, metrics={"lut_used": 60})
    b = Candidate("module b; endmodule", "narrow",
                  ladder_rungs_passed=5, metrics={"lut_used": 48})
    c = Candidate("module c; endmodule", "share",
                  ladder_rungs_passed=2, metrics={"lut_used": 1})
    w = select([a, b, c], "minimize_luts")
    assert w.mutation == "narrow"


def test_selection_none_when_all_dead():
    a = Candidate("x", "standard"); a.alive = False
    assert select([a], "minimize_luts") is None


def test_every_mutation_preserves_the_observable_contract():
    for objective in ("minimize_luts", "minimize_ffs", "maximize_freq", "minimize_power"):
        for name, prompt in mutation_prompts(objective, 4):
            for requirement in ("observable latency", "throughput", "interface", "reset semantics", "parameter behavior"):
                assert requirement in prompt, (name, requirement)
            assert "Do not add pipeline stages" in prompt


def test_pipeline_and_sharing_do_not_propose_a_new_schedule():
    frequency = dict(mutation_prompts("maximize_freq", 4))["pipeline"]
    sharing = dict(mutation_prompts("minimize_luts", 4))["share"]
    assert "retiming existing registers" in frequency
    assert "@latency declaration unchanged" in frequency
    assert "declare the new latency" not in frequency
    assert "original schedule already permits" in sharing
    assert "without changing any accepted input or output cycle" in sharing


def test_narrowing_preserves_high_bits_and_parameter_range():
    prompt = dict(mutation_prompts("minimize_luts", 4))["narrow"]
    assert "full legal input and parameter range" in prompt
    assert "high-bit effects" in prompt
