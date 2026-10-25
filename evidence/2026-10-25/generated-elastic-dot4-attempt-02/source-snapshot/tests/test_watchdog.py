from autortl.watchdog import inspect


def test_stagnation_fires():
    hist = [{"is_best": True}] + [{"is_best": False}] * 3
    sigs = inspect(hist, [], [], 1.0)
    assert any(s.kind == "STAGNATION" for s in sigs)


def test_churn_fires_on_identical_code():
    code = "module m; assign y = x; endmodule"
    sigs = inspect([], [code, code + "  // comment"], [], 1.0)
    assert any(s.kind == "CHURN" for s in sigs)


def test_repeated_error_fires():
    err = "ERROR: [Synth 8-327] latch on y"
    sigs = inspect([], [], [err, err, err], 1.0)
    assert any(s.kind == "REPEATED_ERROR" for s in sigs)


def test_budget_anomaly_fires():
    hist = [{"is_best": True}, {"is_best": False}, {"is_best": False}]
    sigs = inspect(hist, [], [], 0.4)
    assert any(s.kind == "BUDGET_ANOMALY" for s in sigs)


def test_quiet_when_healthy():
    hist = [{"is_best": True}, {"is_best": False}, {"is_best": True}]
    assert inspect(hist, ["a"], ["e1", "e2"], 0.9) == []
