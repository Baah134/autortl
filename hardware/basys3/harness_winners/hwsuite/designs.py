"""Design table (designs.json): which archived harness winner to run, how wide
its transactions are, and the fault its simulation must catch."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

SUITE = Path(__file__).resolve().parents[1]
REPO = SUITE.parents[2]


class DesignError(RuntimeError):
    pass


@dataclass(frozen=True)
class Design:
    name: str
    title: str
    module: str
    winner: Path
    sha256: str
    state: Path
    adapter: Path
    in_bytes: int
    out_bytes: int
    fault: dict
    overlap: bool        # contract allows accepting while a result retires

    def verify(self) -> None:
        """The winner must be byte-identical to the run's recorded best design."""
        if not self.winner.is_file():
            raise DesignError(f"{self.name}: winner not found: {self.winner}")
        actual = hashlib.sha256(self.winner.read_bytes()).hexdigest()
        if actual != self.sha256:
            raise DesignError(f"{self.name}: winner SHA-256 {actual} does not match recorded {self.sha256}")
        best = json.loads(self.state.read_text(encoding="utf-8")).get("best_sha256")
        if best != self.sha256:
            raise DesignError(f"{self.name}: run state best_sha256 {best} does not match {self.sha256}")
        if not self.adapter.is_file():
            raise DesignError(f"{self.name}: adapter not found: {self.adapter}")

    def faulted_source(self) -> str:
        """The winner with exactly one fault applied (for must-fail checks)."""
        text = self.winner.read_text(encoding="utf-8")
        find, replace = self.fault["find"], self.fault["replace"]
        occurrence = int(self.fault.get("occurrence", 1))
        start = -1
        for _ in range(occurrence):
            start = text.find(find, start + 1)
            if start < 0:
                raise DesignError(f"{self.name}: fault anchor occurrence {occurrence} not found")
        faulted = text[:start] + replace + text[start + len(find):]
        if faulted == text:
            raise DesignError(f"{self.name}: fault does not change the source")
        return faulted


def load(path: Path = SUITE / "designs.json") -> dict[str, Design]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    designs = {}
    for name, entry in raw.items():
        for key in ("in_bytes", "out_bytes"):
            value = entry[key]
            if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 8:
                raise DesignError(f"{name}: {key} must be an integer 1..8")
        if not isinstance(entry.get("overlap"), bool):
            raise DesignError(f"{name}: overlap must be true or false")
        designs[name] = Design(
            name=name, title=entry["title"], module=entry["module"],
            winner=REPO / entry["winner"], sha256=entry["sha256"], state=REPO / entry["state"],
            adapter=SUITE / entry["adapter"], in_bytes=entry["in_bytes"],
            out_bytes=entry["out_bytes"], fault=entry["fault"], overlap=entry["overlap"])
    return designs
