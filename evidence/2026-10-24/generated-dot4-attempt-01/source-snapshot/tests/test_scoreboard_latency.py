"""Regress a real zero-cycle false positive in a one-cycle streaming contract."""
from tests.tbgen_live_cases import cases
from autortl.tbgen import generate_scoreboard_tb


def rendered(latency):
    _, spec, _, _, _ = next(row for row in cases() if row[0] == "scoreboard_good")
    spec.latency = latency
    rows = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
    return generate_scoreboard_tb(spec, rows, [{"y": 3, "z": 3}, {"y": 7, "z": 7}])


def test_scoreboard_records_input_acceptance_before_output_comparison():
    text = rendered(1)
    assert "integer _autortl_accepted_cycle [0:1]" in text
    capture = text.index("_autortl_accepted_cycle[_autortl_push]=_autortl_cycle;")
    comparison = text.index("_autortl_cycle - _autortl_accepted_cycle[_autortl_pop] < 1")
    assert capture < comparison
    # Unexpected output must be diagnosed before indexing an unaccepted transaction.
    assert text.index("FAIL unexpected output transaction") < text.index("end else begin", capture) < comparison
    assert "FAIL output before minimum transfer latency" in text


def test_zero_latency_still_allows_same_edge_transfer():
    assert "_autortl_accepted_cycle[_autortl_pop] < 0" in rendered(0)


def test_supported_large_latency_extends_drain_window():
    text = rendered(1024)
    assert "_autortl_cycle<2104" in text
    assert "_autortl_accepted_cycle[_autortl_pop] < 1024" in text


def test_serial_device_gets_latency_allowance_for_every_transaction():
    text = rendered(100)
    # Two serial operations each need their own100-cycle computation budget.
    assert "_autortl_cycle<256" in text
