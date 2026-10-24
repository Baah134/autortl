import pytest
from autortl.spec import ModuleSpec, Port
from autortl.tbgen import generate_fixed_latency_tb, generate_scoreboard_tb
from tests.tbgen_live_cases import cases, save


def spec(latency=0):
    clock = [Port("clk", "input", 1), Port("rst", "input", 1)] if latency else []
    return ModuleSpec("m", "adder", clock + [Port("a", "input", 8), Port("y", "output", 8)], latency=latency)


@pytest.mark.parametrize("latency", [0,1,3])
def test_finite_drain_and_explicit_edge_convention(latency):
    text = generate_fixed_latency_tb(spec(latency), [{"a": 1}, {"a": 2}], [{"y": 1}, {"y": 2}])
    assert f"_autortl_cycle<{2 + max(latency-1,0)}" in text
    assert f"_autortl_index = _autortl_cycle - {max(latency-1,0)}" in text
    assert "watchdog timeout" in text
    if latency:
        released = text.split("rst = 1'b0;")[1]
        assert "repeat" not in released
        assert "@(posedge _autortl_clk);\n#1;" in released
    else:
        assert ".clk(" not in text and ".rst(" not in text
        assert "@(posedge" not in text


@pytest.mark.parametrize("change", ["missing_expected", "extra_expected", "empty", "negative", "no_reset", "inout", "duplicate", "clock_domain"])
def test_malformed_contract_or_vectors_fail_closed(change):
    s = spec(1)
    stimulus, expected = [{"a": 1}], [{"y": 1}]
    if change == "missing_expected": expected = [{}]
    elif change == "extra_expected": expected = [{"y": 1, "other": 1}]
    elif change == "empty": stimulus, expected = [], []
    elif change == "negative": expected = [{"y": -1}]
    elif change == "no_reset": s.ports = [p for p in s.ports if p.name != "rst"]
    elif change == "inout": s.ports[-1].direction = "inout"
    elif change == "duplicate": s.ports += [Port("y", "output", 8)]
    else: s.ports[-1].clock_domain = "clk2"
    with pytest.raises(ValueError): generate_fixed_latency_tb(s, stimulus, expected)


def test_scoreboard_checks_all_ports_and_accepted_transfers():
    text = next(row[3] for row in cases() if row[0] == "scoreboard_good")
    for signal in ("a", "b"):
        assert f"{signal} = _autortl_stim_{signal}[_autortl_push]" in text
    for signal in ("y", "z"):
        assert f"{signal} !== _autortl_exp_{signal}[_autortl_pop]" in text
        assert f"{signal} !== _autortl_held_{signal}" in text
    assert "sample accepted transfers BEFORE NBA" in text
    assert "in_valid === 1'b1 && in_ready === 1'b1" in text
    assert "out_valid === 1'b1 && out_ready === 1'b1" in text
    assert "scoreboard did not drain" in text
    assert "unexpected output transaction" in text


def test_missing_handshake_controls_rejected():
    s = spec(1)
    s.compare_mode = "scoreboard"
    with pytest.raises(ValueError):
        generate_scoreboard_tb(s, [{"a": 1}], [{"y": 1}])


def test_live_fixture_writer_preserves_expected_verdicts(tmp_path):
    manifest = save(tmp_path)
    assert len(manifest) == 9
    assert sum(row["expected_pass"] for row in manifest) == 5
    for row in manifest:
        assert (tmp_path / row["case"] / "dut.v").exists()
        assert "TEST PASSED" in (tmp_path / row["case"] / "tb.v").read_text()
