"""Content-hash cache: identical Verilog is never synthesised twice.

Also hosts the contract-hash artifact cache used by incremental replanning
(Pothole 4): verified modules keyed by their contract hash survive replans.
"""
from __future__ import annotations
import hashlib
import json
import re
import copy
from pathlib import Path
from .state import atomic_write_text


def code_hash(verilog: str) -> str:
    """Hash after stripping comments + whitespace, so cosmetic differences dedupe."""
    s = re.sub(r"//.*", "", verilog)
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.DOTALL)
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\s*([^\w\s])\s*", r"\1", s)   # drop spaces around operators/punct
    return hashlib.sha256(s.encode()).hexdigest()[:16]


class MetricsCache:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._data: dict = {}
        if self.path.exists():
            try:
                loaded = json.loads(self.path.read_text(encoding="utf-8"))
                self._data = loaded if isinstance(loaded, dict) else {}
            except json.JSONDecodeError:
                self._data = {}

    @staticmethod
    def _context_key(verilog: str, context: dict) -> str:
        identity = {"source_hash": hashlib.sha256(verilog.encode()).hexdigest(),
                    "context": context}
        return "v2:" + hashlib.sha256(json.dumps(identity, sort_keys=True,
                                                separators=(",", ":")).encode()).hexdigest()

    def get(self, verilog: str, context: dict | None = None) -> dict | None:
        if context is None:
            return copy.deepcopy(self._data.get(code_hash(verilog)))
        entry = self.get_entry(verilog, context)
        return entry["metrics"] if entry else None

    def get_entry(self, verilog: str, context: dict) -> dict | None:
        entry = self._data.get(self._context_key(verilog, context))
        if not isinstance(entry, dict) or entry.get("schema_version") != 2:
            return None
        if entry.get("context") != context or entry.get("source_hash") != hashlib.sha256(verilog.encode()).hexdigest():
            return None
        artifacts = entry.get("artifacts", {})
        if not isinstance(artifacts, dict) or not artifacts or not isinstance(entry.get("artifact_dir"), str):
            return None
        if not isinstance(entry.get("metrics"), dict):
            return None
        root = Path(entry["artifact_dir"]).resolve()
        source_found = False
        report_found = False
        for relative, digest in artifacts.items():
            if not isinstance(relative, str) or not isinstance(digest, str):
                return None
            path = (root / relative).resolve()
            if not path.is_relative_to(root) or not path.is_file():
                return None
            try:
                data = path.read_bytes()
            except OSError:
                return None
            if hashlib.sha256(data).hexdigest() != digest:
                return None
            if path.suffix in (".v", ".sv"):
                try:
                    source_found |= data.decode("utf-8").replace("\r\n", "\n") == verilog.replace("\r\n", "\n")
                except UnicodeDecodeError:
                    return None
            report_found |= path.suffix == ".rpt"
        return copy.deepcopy(entry) if source_found and report_found else None

    def put(self, verilog: str, metrics: dict, context: dict | None = None,
            artifact_dir: Path | None = None) -> None:
        updated = copy.deepcopy(self._data)
        if context is None:
            updated[code_hash(verilog)] = copy.deepcopy(metrics)
        else:
            root = Path(artifact_dir).resolve() if artifact_dir else None
            artifacts = {}
            if root and root.is_dir():
                for path in sorted(root.rglob("*")):
                    if path.is_file() and path.suffix in (".v", ".sv", ".rpt", ".xdc", ".tcl"):
                        if not path.resolve().is_relative_to(root):
                            continue
                        artifacts[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
            updated[self._context_key(verilog, context)] = {
                "schema_version": 2, "source_hash": hashlib.sha256(verilog.encode()).hexdigest(),
                "context": copy.deepcopy(context), "metrics": copy.deepcopy(metrics),
                "artifact_dir": str(root) if root else None, "artifacts": artifacts}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(self.path, json.dumps(updated, indent=1, allow_nan=False))
        self._data = updated


class ArtifactCache:
    """contract_hash -> {verilog, ladder, metrics}. Survives replans."""
    def __init__(self, path: Path):
        self.path = Path(path)
        self._data: dict = {}
        if self.path.exists():
            try:
                loaded = json.loads(self.path.read_text(encoding="utf-8"))
                self._data = loaded if isinstance(loaded, dict) else {}
            except json.JSONDecodeError:
                self._data = {}

    def get(self, contract_hash: str) -> dict | None:
        return copy.deepcopy(self._data.get(contract_hash))

    def put(self, contract_hash: str, verilog: str, metrics: dict) -> None:
        updated = copy.deepcopy(self._data)
        updated[contract_hash] = {"verilog": verilog, "metrics": copy.deepcopy(metrics)}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(self.path, json.dumps(updated, indent=1, allow_nan=False))
        self._data = updated
