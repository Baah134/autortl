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
