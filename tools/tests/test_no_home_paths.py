"""No committed file outside sealed evidence names a real Windows or Unix home directory.

The repository is public. Live docs, code and test fixtures use `<user>` or a
fictional `someone`; sealed evidence keeps its original bytes (their hashes are
audited), and `benchmark.archive` sanitises new evidence.
"""
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HOME = re.compile(r"(?:[A-Za-z]:(?:\\\\|\\|/)+Users(?:\\\\|\\|/)+|/home/|/Users/)([A-Za-z0-9._-]+)")
ALLOWED = {"someone", "user", "runner", "runneradmin", "me", "you", "name", "username", "example", "secret.txt", "alice"}  # alice: this file's own samples


def tracked_files():
    try:
        out = subprocess.run(["git", "ls-files", "-z", "--", ":!evidence"], cwd=ROOT, capture_output=True,
                             check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("git is not available")
    return [ROOT / name for name in out.decode("utf-8").split("\0") if name]


def test_no_real_home_directory_in_live_files():
    found = []
    for path in tracked_files():
        if path.suffix.lower() in {".png", ".jpg", ".bit", ".pdf", ".gz", ".zip"} or not path.is_file():
            continue
        text = path.read_bytes().decode("utf-8", errors="ignore")
        for match in HOME.finditer(text):
            if match.group(1).lower() not in ALLOWED:
                found.append(f"{path.relative_to(ROOT).as_posix()}: {match.group(0)}")
    assert not found, "replace with <user>:\n" + "\n".join(found[:20])


def test_pattern_catches_each_path_form():
    for sample in ("C:/Users/alice/x", "C:\\Users\\alice\\x", "C:\\\\Users\\\\alice", "/home/alice/x"):
        assert HOME.search(sample).group(1) == "alice"
    assert HOME.search("C:/Users/<user>/x") is None
