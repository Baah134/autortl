from autortl.bestofn import Candidate, mutation_prompts, dedupe, select


def test_portfolio_matches_objective():
    names = [n for n, _ in mutation_prompts("maximize_freq", 4)]
    assert "pipeline" in names and "wildcard" in names


def test_dedupe_kills_cosmetic_duplicates():
    a = Candidate("module m; assign y = x; endmodule", "standard")
    b = Candidate("module m;  assign y=x;  endmodule // dup", "narrow")
    survivors = dedupe([a, b])
    assert len(survivors) == 1 and survivors[0].mutation == "standard"


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
