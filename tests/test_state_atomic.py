"""Atomic checkpoint replacement under bounded Windows sharing contention."""
import ctypes
import os
import threading
from pathlib import Path

import pytest

from autortl import state


def contention(code=5, message="target temporarily locked"):
    error = PermissionError(message)
    error.winerror = code
    return error


def configure_windows(monkeypatch, windows=True):
    monkeypatch.setattr(state, "_WINDOWS", windows)
    sleeps = []
    monkeypatch.setattr(state.time, "sleep", sleeps.append)
    return sleeps


@pytest.mark.parametrize("code", [5, 32, 33])
def test_transient_windows_contention_retries_same_temp_then_atomically_replaces(tmp_path, monkeypatch, code):
    path = tmp_path / "budget.json"
    path.write_text("old")
    sleeps = configure_windows(monkeypatch)
    original_replace = state.os.replace
    calls = []
    def replace(source, destination):
        calls.append((source, destination))
        assert path.read_text() == "old"
        assert Path(source).read_text() == "new"
        if len(calls) < 3:
            raise contention(code)
        return original_replace(source, destination)
    monkeypatch.setattr(state.os, "replace", replace)
    state.atomic_write_text(path, "new")
    assert path.read_text() == "new"
    assert len(calls) == 3 and len(set(calls)) == 1
    assert sleeps == [.01, .02]
    assert not list(tmp_path.glob("*.tmp"))


def test_exhausted_contention_preserves_old_checkpoint_and_original_exception(tmp_path, monkeypatch):
    path = tmp_path / "state.json"
    path.write_text("old")
    sleeps = configure_windows(monkeypatch)
    errors = []
    def replace(*args):
        error = contention(32, "attempt " + str(len(errors)))
        errors.append(error)
        raise error
    monkeypatch.setattr(state.os, "replace", replace)
    with pytest.raises(PermissionError) as raised:
        state.atomic_write_text(path, "new")
    # Classified as infrastructure, with the original contention kept as its cause
    # (taxonomy: checkpoint_replace_denied).
    assert isinstance(raised.value, state.CheckpointLockedError)
    assert raised.value.__cause__ is errors[0] and raised.value.winerror == 32
    assert "resume" in str(raised.value) and str(path) in str(raised.value)
    assert len(errors) == 7
    assert sleeps == [.01, .02, .04, .08, .16, .32]
    assert sum(sleeps) < 1
    assert path.read_text() == "old" and not list(tmp_path.glob("*.tmp"))


@pytest.mark.parametrize("windows,code", [(False, 5), (True, 2), (True, None)])
def test_nonretryable_replace_errors_fail_once(tmp_path, monkeypatch, windows, code):
    path = tmp_path / "state.json"
    path.write_text("old")
    sleeps = configure_windows(monkeypatch, windows)
    error = contention(code) if code is not None else PermissionError("no Windows error code")
    calls = []
    def replace(*args):
        calls.append(args)
        raise error
    monkeypatch.setattr(state.os, "replace", replace)
    with pytest.raises(PermissionError) as raised:
        state.atomic_write_text(path, "new")
    assert raised.value is error
    assert len(calls) == 1 and not sleeps
    assert path.read_text() == "old" and not list(tmp_path.glob("*.tmp"))


@pytest.mark.parametrize("failure_stage", ["fsync", "replace"])
def test_cleanup_failure_cannot_mask_original_write_error(tmp_path, monkeypatch, failure_stage):
    path = tmp_path / "state.json"
    path.write_text("old")
    error = OSError("original " + failure_stage + " failure")
    def fail(*args):
        raise error
    monkeypatch.setattr(state.os, failure_stage, fail)
    monkeypatch.setattr(state.os, "unlink", lambda *args: (_ for _ in ()).throw(PermissionError("cleanup blocked")))
    with pytest.raises(OSError) as raised:
        state.atomic_write_text(path, "new")
    assert raised.value is error
    assert path.read_text() == "old"


@pytest.mark.skipif(os.name != "nt", reason="Windows sharing semantics")
def test_real_windows_reader_that_never_lets_go_is_classified(tmp_path):
    # What crashed run 02: a reader holding a run file open, like `tail -F`.
    from ctypes import wintypes
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
                       wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    create.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    path = tmp_path / "events.jsonl"
    path.write_text("old")
    handle = create(str(path), 0x80000000, 0x1 | 0x2, None, 3, 0x80, None)   # read, share read+write, not delete
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        with pytest.raises(state.CheckpointLockedError) as raised:
            state.atomic_write_text(path, "new")
        assert raised.value.winerror in (5, 32, 33) and "resume" in str(raised.value)
    finally:
        kernel.CloseHandle(handle)
    assert path.read_text() == "old" and not list(tmp_path.glob(".events.jsonl.*.tmp"))


@pytest.mark.skipif(os.name != "nt", reason="Windows sharing semantics")
def test_real_windows_read_handle_releases_and_checkpoint_replace_recovers(tmp_path, monkeypatch):
    from ctypes import wintypes
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
                       wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    create.restype = wintypes.HANDLE
    close = kernel.CloseHandle
    close.argtypes = [wintypes.HANDLE]
    close.restype = wintypes.BOOL
    path = tmp_path / "budget.json"
    path.write_text("old")
    handle = create(str(path), 0x80000000, 0x1, None, 3, 0x80, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    handle_closed = threading.Event()
    # Verify the intended lock exists before exercising the writer's recovery.
    probe = tmp_path / "probe.tmp"
    probe.write_text("probe")
    try:
        with pytest.raises(OSError) as locked:
            os.replace(probe, path)
        assert locked.value.winerror in (5, 32, 33)
        released = threading.Event()
        release_errors = []
        observed_retries = []
        real_sleep = state.time.sleep
        def release_after_contention(delay):
            observed_retries.append(delay)
            if len(observed_retries) == 1:
                released.set()
            real_sleep(delay)
        def release():
            if released.wait(2):
                if not close(handle):
                    release_errors.append(ctypes.get_last_error())
                else:
                    handle_closed.set()
        worker = threading.Thread(target=release, daemon=True)
        monkeypatch.setattr(state.time, "sleep", release_after_contention)
        worker.start()
        try:
            state.atomic_write_text(path, "new")
        finally:
            released.set()
            worker.join(2)
        assert not worker.is_alive() and not release_errors
        assert observed_retries
        assert path.read_text() == "new"
        assert not list(tmp_path.glob(".budget.json.*.tmp"))
    finally:
        if not handle_closed.is_set():
            close(handle)
