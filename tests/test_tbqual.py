from autortl.tbqual import mutate


def test_mutation_changes_behavior():
    v = "module m; assign y = (a < b); endmodule"
    m = mutate(v)
    assert m is not None
    mutated, desc = m
    assert mutated != v and "<" in desc


def test_no_mutation_possible():
    assert mutate("module m; assign y = x; endmodule") is None
