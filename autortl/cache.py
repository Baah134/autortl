"""Content-hash cache: identical Verilog is never synthesised twice.

Also hosts the contract-hash artifact cache used by incremental replanning
(Pothole 4): verified modules keyed by their contract hash survive replans.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path


def code_hash(verilog: str) -> str:
    """Hash after stripping comments + whitespace, so cosmetic differences dedupe."""
    s = re.sub(r"//.*", "", verilog)
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.DOTALL)
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\s*([^\w\s])\s*", r"\1", s)   # drop spaces around operators/punct
    return hashlib.sha256(s.encode()).hexdigest()[:16]


class MetricsCache:
    def __init__(self, path: Path):
        self.path = path
        self._data: dict = {}
        if path.exists():
            try:
                self._data = json.loads(path.read_text())
            except json.JSONDecodeError:
                self._data = {}

    def get(self, verilog: str) -> dict | None:
        return self._data.get(code_hash(verilog))

    def put(self, verilog: str, metrics: dict) -> None:
        self._data[code_hash(verilog)] = metrics
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, indent=1))


class ArtifactCache:
    """contract_hash -> {verilog, ladder, metrics}. Survives replans."""
    def __init__(self, path: Path):
        self.path = path
        self._data: dict = {}
        if path.exists():
            try:
                self._data = json.loads(path.read_text())
            except json.JSONDecodeError:
                self._data = {}

    def get(self, contract_hash: str) -> dict | None:
        return self._data.get(contract_hash)

    def put(self, contract_hash: str, verilog: str, metrics: dict) -> None:
        self._data[contract_hash] = {"verilog": verilog, "metrics": metrics}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, indent=1))
