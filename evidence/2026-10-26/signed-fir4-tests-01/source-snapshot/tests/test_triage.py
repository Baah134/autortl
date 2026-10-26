from autortl.triage import classify, FailureKind


def test_license_is_infra():
    assert classify("ERROR: could not obtain license for Synthesis") == FailureKind.INFRA


def test_file_lock_is_infra():
    assert classify("cannot create file x.wdb: used by another process") == FailureKind.INFRA


def test_timeout_is_infra():
    assert classify("timed out after 300s") == FailureKind.INFRA


def test_http_429_is_infra():
    assert classify("HTTP 429 Too Many Requests") == FailureKind.INFRA


def test_synth_message_is_design():
    assert classify("WARNING: [Synth 8-327] inferring latch") == FailureKind.DESIGN


def test_testbench_fail_is_design():
    assert classify("TEST FAILED: 3 errors") == FailureKind.DESIGN


def test_unknown_is_unknown():
    assert classify("something inexplicable happened") == FailureKind.UNKNOWN
