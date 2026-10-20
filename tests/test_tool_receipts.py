"""Durable subprocess exits, distinct from synthetic driver outcomes and log markers."""
import hashlib
import json
import subprocess
from unittest.mock import Mock

import pytest

from autortl import vivado
from autortl.contract_context import flow_evidence


def records(directory):
    return [json.loads(line) for line in (directory / "tool_exit_records.log").read_text().splitlines()]


def worker(monkeypatch, returncode=0):
    process = Mock(pid=1234, returncode=returncode)
    process.communicate.return_value = ("SYNTH_COMPLETE", "")
    monkeypatch.setattr(vivado.subprocess, "Popen", Mock(return_value=process))
    return process


@pytest.mark.parametrize("returncode", [0, 7, -9])
def test_process_receipt_records_actual_exit_and_log_hash(tmp_path, monkeypatch, returncode):
    worker(monkeypatch, returncode)
    log = tmp_path / "vivado_synth_output.log"
    result, _ = vivado._run(["C:/tools/vivado.bat", "-token", "secret-not-recorded"], tmp_path, 3, log)
    receipt, = records(tmp_path)
    assert result == returncode
    assert receipt["status"] == "exited"
    assert type(receipt["returncode"]) is int and receipt["returncode"] == returncode
    assert receipt["driver_returncode"] == returncode
    assert receipt["tool"] == "vivado" and receipt["pid"] == 1234
    assert receipt["executable"] == "C:/tools/vivado.bat"
    assert receipt["cwd"] == str(tmp_path.resolve())
    assert receipt["output_log_path"] == str(log.resolve())
    assert receipt["output_log_sha256"] == hashlib.sha256(log.read_bytes()).hexdigest()
    assert receipt["elapsed_seconds"] >= 0
    assert "secret-not-recorded" not in json.dumps(receipt)


@pytest.mark.parametrize("error,driver", [(FileNotFoundError("missing"), 127), (PermissionError("blocked"), 126)])
def test_launch_failure_does_not_invent_process_exit(tmp_path, monkeypatch, error, driver):
    monkeypatch.setattr(vivado.subprocess, "Popen", Mock(side_effect=error))
    assert vivado._run(["xvlog.bat"], tmp_path, 3, tmp_path / "xvlog.log")[0] == driver
    receipt, = records(tmp_path)
    assert receipt["status"] == "launch_failed"
    assert receipt["returncode"] is None and receipt["pid"] is None
    assert receipt["driver_returncode"] == driver


def test_timeout_remains_unsuccessful_even_when_cleanup_process_exit_is_zero(tmp_path, monkeypatch):
    process = worker(monkeypatch)
    process.communicate.side_effect = subprocess.TimeoutExpired("xsim", 3)
    monkeypatch.setattr(vivado, "_stop_tool", Mock(return_value=("TEST PASSED", "")))
    assert vivado._run(["xsim.bat"], tmp_path, 3, tmp_path / "xsim.log")[0] == 124
    receipt, = records(tmp_path)
    assert receipt["returncode"] == 0
    assert receipt["status"] == "timed_out" and receipt["driver_returncode"] == 124
    assert not flow_evidence(tmp_path)["tool_exit_evidence"]["latest_by_tool"]["xsim"]["successful"]


def test_cancellation_has_durable_receipt_and_preserves_original_interrupt(tmp_path, monkeypatch):
    process = worker(monkeypatch)
    interrupted = KeyboardInterrupt("cancel")
    process.communicate.side_effect = interrupted
    monkeypatch.setattr(vivado, "_stop_tool", Mock(return_value=("partial output", "")))
    with pytest.raises(KeyboardInterrupt) as raised:
        vivado._run(["xelab.bat"], tmp_path, 3, tmp_path / "xelab.log")
    assert raised.value is interrupted
    receipt, = records(tmp_path)
    assert receipt["status"] == "cancelled" and receipt["returncode"] == 0
    assert receipt["driver_returncode"] is None
    assert not flow_evidence(tmp_path)["tool_exit_evidence"]["latest_by_tool"]["xelab"]["successful"]


def test_receipt_history_is_appended_and_latest_failure_wins(tmp_path, monkeypatch):
    process = worker(monkeypatch)
    vivado._run(["xvlog.bat"], tmp_path, 3, tmp_path / "xvlog.log")
    process.returncode = 9
    vivado._run(["xvlog.bat"], tmp_path, 3, tmp_path / "xvlog.log")
    history = records(tmp_path)
    assert [r["returncode"] for r in history] == [0, 9]
    evidence = flow_evidence(tmp_path)["tool_exit_evidence"]
    assert evidence["schema_valid"] is True and evidence["history_count"] == 2
    assert evidence["latest_by_tool"]["xvlog"]["returncode"] == 9
    assert evidence["latest_by_tool"]["xvlog"]["successful"] is False
    assert set(evidence["missing_required_tools"]) == {"xelab", "xsim", "vivado"}


def test_context_caps_receipts_and_hashes_complete_file(tmp_path, monkeypatch):
    worker(monkeypatch)
    vivado._run(["xvlog.bat"], tmp_path, 3, tmp_path / "xvlog.log")
    template, = records(tmp_path)
    path = tmp_path / "tool_exit_records.log"
    path.write_text("".join(json.dumps(dict(template, pid=n+1)) + "\n" for n in range(40)))
    evidence = flow_evidence(tmp_path)["tool_exit_evidence"]
    assert evidence["history_count"] == 40 and evidence["truncated"] is True
    assert len(evidence["records"]) == 32
    assert evidence["records"][0]["pid"] == 9 and evidence["records"][-1]["pid"] == 40
    assert evidence["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert evidence["path"] == str(path.resolve())


@pytest.mark.parametrize("field,value", [
    ("returncode", True), ("returncode", "0"), ("driver_returncode", False),
    ("pid", True), ("elapsed_seconds", float("nan")), ("status", "passed"),
    ("output_log_sha256", "not-a-hash"), ("tool", ""),
])
def test_invalid_receipt_schema_cannot_become_success(tmp_path, monkeypatch, field, value):
    worker(monkeypatch)
    vivado._run(["xvlog.bat"], tmp_path, 3, tmp_path / "xvlog.log")
    valid, = records(tmp_path)
    path = tmp_path / "tool_exit_records.log"
    path.write_text(json.dumps(valid) + "\n" + json.dumps(dict(valid, **{field: value})) + "\n")
    evidence = flow_evidence(tmp_path)["tool_exit_evidence"]
    assert evidence["schema_valid"] is False
    assert not evidence["latest_by_tool"]
    assert set(evidence["missing_required_tools"]) == {"xvlog", "xelab", "xsim", "vivado"}


def test_malformed_receipt_and_missing_evidence_fail_closed(tmp_path):
    evidence = flow_evidence(tmp_path)["tool_exit_evidence"]
    assert evidence["status"] == "missing" and not evidence["latest_by_tool"]
    path = tmp_path / "tool_exit_records.log"
    path.write_text('{"returncode":0}\nnot json\n')
    evidence = flow_evidence(tmp_path)["tool_exit_evidence"]
    assert evidence["status"] == "invalid" and evidence["schema_valid"] is False
    assert not evidence["latest_by_tool"]


def test_success_does_not_return_before_receipt_is_durable(tmp_path, monkeypatch):
    worker(monkeypatch)
    error = PermissionError("receipt storage blocked")
    monkeypatch.setattr(vivado, "_append_tool_exit_record", Mock(side_effect=error))
    with pytest.raises(PermissionError) as raised:
        vivado._run(["xvlog.bat"], tmp_path, 3, tmp_path / "xvlog.log")
    assert raised.value is error


def test_cancellation_receipt_write_failure_does_not_mask_interrupt(tmp_path, monkeypatch):
    process = worker(monkeypatch)
    error = KeyboardInterrupt("cancelled by user")
    process.communicate.side_effect = error
    monkeypatch.setattr(vivado, "_stop_tool", Mock(return_value=("", "")))
    monkeypatch.setattr(vivado, "_append_tool_exit_record", Mock(side_effect=PermissionError("receipt blocked")))
    with pytest.raises(KeyboardInterrupt) as raised:
        vivado._run(["xsim.bat"], tmp_path, 3, tmp_path / "xsim.log")
    assert raised.value is error
    assert any("receipt could not be saved" in note for note in error.__notes__)


def test_interrupted_launch_has_cancelled_receipt(tmp_path, monkeypatch):
    monkeypatch.setattr(vivado.subprocess, "Popen", Mock(side_effect=KeyboardInterrupt("during launch")))
    with pytest.raises(KeyboardInterrupt):
        vivado._run(["xvlog.bat"], tmp_path, 3, tmp_path / "xvlog.log")
    receipt, = records(tmp_path)
    assert receipt["status"] == "cancelled" and receipt["returncode"] is None
    assert receipt["driver_returncode"] is None and receipt["pid"] is None


@pytest.mark.parametrize("actual", [None, True, "0"])
def test_noninteger_process_code_is_unknown_never_zero(tmp_path, monkeypatch, actual):
    worker(monkeypatch, actual)
    result, _ = vivado._run(["xvlog.bat"], tmp_path, 3, tmp_path / "xvlog.log")
    assert result != 0
    receipt, = records(tmp_path)
    assert receipt["returncode"] is None
    assert not flow_evidence(tmp_path)["tool_exit_evidence"]["latest_by_tool"]["xvlog"]["successful"]


@pytest.mark.parametrize("tamper,status", [("change", "mismatch"), ("delete", "missing"), ("null_digest", "missing_hash")])
def test_latest_zero_exit_requires_matching_retained_output_log(tmp_path, monkeypatch, tamper, status):
    worker(monkeypatch)
    log = tmp_path / "xvlog.log"
    vivado._run(["xvlog.bat"], tmp_path, 3, log)
    if tamper == "change":
        log.write_text("tampered output")
    elif tamper == "delete":
        log.unlink()
    else:
        receipt, = records(tmp_path)
        receipt["output_log_sha256"] = None
        (tmp_path / "tool_exit_records.log").write_text(json.dumps(receipt) + "\n")
    evidence = flow_evidence(tmp_path)["tool_exit_evidence"]
    assert evidence["schema_valid"] is True
    latest = evidence["latest_by_tool"]["xvlog"]
    assert latest["returncode"] == 0
    assert latest["successful"] is False and latest["log_verified"] is False
    assert latest["log_status"] == status


def test_only_latest_receipt_log_hash_is_checked_after_legitimate_overwrite(tmp_path, monkeypatch):
    process = worker(monkeypatch)
    log = tmp_path / "xvlog.log"
    vivado._run(["xvlog.bat"], tmp_path, 3, log)
    first, = records(tmp_path)
    process.communicate.return_value = ("second successful invocation", "")
    vivado._run(["xvlog.bat"], tmp_path, 3, log)
    assert first["output_log_sha256"] != hashlib.sha256(log.read_bytes()).hexdigest()
    latest = flow_evidence(tmp_path)["tool_exit_evidence"]["latest_by_tool"]["xvlog"]
    assert latest["successful"] is True and latest["log_status"] == "verified"
