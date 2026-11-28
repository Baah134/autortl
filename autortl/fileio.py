"""Small file helpers shared by the harness, benchmark and tools.

These replace two idioms that were written out at dozens of call sites. They
add no behaviour: the same bytes are read and the same exceptions propagate.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def file_sha256(path) -> str:
    """SHA-256 hex digest of a file's exact bytes."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def text_sha256(text: str) -> str:
    """SHA-256 hex digest of text encoded as UTF-8."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_json(path):
    """Parse a UTF-8 JSON file."""
    return json.loads(Path(path).read_text(encoding="utf-8"))
