"""Design table (designs.json): which archived harness winner to run, how wide
its transactions are, and the fault its simulation must catch."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

SUITE = Path(__file__).resolve().parents[1]
REPO = SUITE.parents[2]
# Widest transaction side (AES-128 takes a 16-byte key and a 16-byte block).
# stream_shell counts bytes in 8 bits; scripts/build.tcl and the bench's
# MAX_BYTES use the same bound.
MAX_BYTES = 32


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
    # Only for a run that ended before writing best_sha256 (budget exhausted):
    # {"iteration": N, "facts": <iter_00N/evaluation_facts.json>, "reason": ...}.
    # The winner is then that iteration's candidate, pinned by the SHA-256 its
    # evaluation recorded; see _verify_pinned_iteration.
    best_pin: dict | None = None

    def verify(self) -> None:
        """The winner must be byte-identical to the run's recorded best design."""
        if not self.winner.is_file():
            raise DesignError(f"{self.name}: winner not found: {self.winner}")
        actual = hashlib.sha256(self.winner.read_bytes()).hexdigest()
        if actual != self.sha256:
            raise DesignError(f"{self.name}: winner SHA-256 {actual} does not match recorded {self.sha256}")
        state = json.loads(self.state.read_text(encoding="utf-8"))
        best = state.get("best_sha256")
        if self.best_pin is None:
            if best != self.sha256:
                raise DesignError(f"{self.name}: run state best_sha256 {best} does not match {self.sha256}")
        else:
            self._verify_pinned_iteration(state)
        if not self.adapter.is_file():
            raise DesignError(f"{self.name}: adapter not found: {self.adapter}")

    def _verify_pinned_iteration(self, state: dict) -> None:
        """A run that ended without best_sha256: the winner must be the
        candidate of the run's best_iteration, whose evaluation recorded this
        SHA-256, a passed simulation and met timing, and which the run's
        design log marks as accepted and best."""
        pin = self.best_pin
        iteration = pin.get("iteration")
        if type(iteration) is not int or not pin.get("reason"):
            raise DesignError(f"{self.name}: best_pin needs an integer iteration and a reason")
        if state.get("best_sha256") not in (None, self.sha256):
            raise DesignError(f"{self.name}: run state records best_sha256 {state['best_sha256']}; use it, not a pin")
        if state.get("best_iteration") != iteration:
            raise DesignError(f"{self.name}: run state best_iteration {state.get('best_iteration')} is not pinned {iteration}")
        iteration_dir = self.state.parent / f"iter_{iteration:03d}"
        if iteration_dir not in self.winner.parents or self.facts().parent != iteration_dir:
            raise DesignError(f"{self.name}: winner and facts must come from {iteration_dir.name}")
        facts = json.loads(self.facts().read_text(encoding="utf-8"))
        if facts.get("candidate_source", {}).get("sha256") != self.sha256:
            raise DesignError(f"{self.name}: {iteration_dir.name} evaluation did not record SHA-256 {self.sha256}")
        metrics = facts.get("candidate_metrics", {})
        if metrics.get("sim_passed") is not True or metrics.get("timing_met") is not True:
            raise DesignError(f"{self.name}: {iteration_dir.name} candidate did not pass simulation and timing")
        rows = [json.loads(line) for line in
                (self.state.parent / "designs.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
        row = [r for r in rows if r.get("iteration") == iteration]
        if len(row) != 1 or row[0].get("is_best") is not True or row[0].get("recommendation") != "ACCEPT":
            raise DesignError(f"{self.name}: designs.jsonl does not mark iteration {iteration} as the accepted best")

    def facts(self) -> Path:
        return REPO / self.best_pin["facts"]

    def measurement(self) -> tuple[Path, dict]:
        """The harness's own measurement of this winner: the run summary's
        best_metrics, or a pinned iteration's candidate_metrics."""
        if self.best_pin is None:
            source = self.state.parent / "run_summary.json"
            return source, json.loads(source.read_text(encoding="utf-8"))["best_metrics"]
        return self.facts(), json.loads(self.facts().read_text(encoding="utf-8"))["candidate_metrics"]

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
            if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= MAX_BYTES:
                raise DesignError(f"{name}: {key} must be an integer 1..{MAX_BYTES}")
        if not isinstance(entry.get("overlap"), bool):
            raise DesignError(f"{name}: overlap must be true or false")
        designs[name] = Design(
            name=name, title=entry["title"], module=entry["module"],
            winner=REPO / entry["winner"], sha256=entry["sha256"], state=REPO / entry["state"],
            adapter=SUITE / entry["adapter"], in_bytes=entry["in_bytes"],
            out_bytes=entry["out_bytes"], fault=entry["fault"], overlap=entry["overlap"],
            best_pin=entry.get("best_pin"))
    return designs
