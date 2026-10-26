"""Budget accounting: LLM calls, Vivado minutes, wall clock.

Degrades gracefully: as budget depletes the orchestrator lowers best-of-N
and skips replans instead of dying mid-run.
"""
from __future__ import annotations
import json
import time
import math
from pathlib import Path
from .state import atomic_write_text


class Budget:
    def __init__(self, max_llm_calls: int, max_vivado_minutes: float,
                 max_wall_minutes: float, state_path: Path | None = None):
        self.max_llm_calls = max_llm_calls
        self.max_vivado_minutes = max_vivado_minutes
        self.max_wall_minutes = max_wall_minutes
        if type(max_llm_calls) is not int or max_llm_calls < 0:
            raise ValueError("max_llm_calls must be a nonnegative integer")
        for value in (max_vivado_minutes, max_wall_minutes):
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError("time budgets must be finite and nonnegative")
        self.llm_calls = 0
        self.vivado_seconds = 0.0
        self.start = time.time()
        self.state_path = Path(state_path) if state_path else None
        if self.state_path and self.state_path.exists():
            d = json.loads(self.state_path.read_text(encoding="utf-8"))
            self.llm_calls = d["llm_calls"]
            self.vivado_seconds = d["vivado_seconds"]
            elapsed = d["elapsed"]
            if type(self.llm_calls) is not int or self.llm_calls < 0:
                raise ValueError("invalid saved model-call count")
            for value in (self.vivado_seconds, elapsed):
                if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                    raise ValueError("invalid saved budget time")
            self.start = time.time() - elapsed

    def charge_llm(self, n: int = 1) -> None:
        if type(n) is not int or n < 0:
            raise ValueError("cannot refund model calls")
        self.llm_calls += n
        self._save()

    def charge_vivado(self, seconds: float) -> None:
        if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds < 0:
            raise ValueError("cannot refund tool time")
        self.vivado_seconds += seconds
        self._save()

    @property
    def wall_minutes(self) -> float:
        return max(0.0, time.time() - self.start) / 60.0

    def fraction_left(self) -> float:
        if min(self.max_llm_calls, self.max_vivado_minutes, self.max_wall_minutes) <= 0:
            return 0.0
        fracs = [
            1 - self.llm_calls / max(self.max_llm_calls, 1),
            1 - (self.vivado_seconds / 60.0) / max(self.max_vivado_minutes, 1e-9),
            1 - self.wall_minutes / max(self.max_wall_minutes, 1e-9),
        ]
        return max(0.0, min(fracs))

    def exhausted(self) -> bool:
        return self.fraction_left() <= 0.0

    def effective_best_of_n(self, configured_n: int) -> int:
        """Degrade N as budget depletes: full N above 50%, 2 above 20%, 1 below."""
        f = self.fraction_left()
        if f > 0.5:
            return configured_n
        if f > 0.2:
            return min(configured_n, 2)
        return 1

    def allow_replan(self) -> bool:
        return self.fraction_left() > 0.3

    def checkpoint(self) -> None:
        """Persist active wall time without charging calls or tool time."""
        self._save()

    def _save(self) -> None:
        if self.state_path:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_text(self.state_path, json.dumps({
                "llm_calls": self.llm_calls,
                "vivado_seconds": self.vivado_seconds,
                "elapsed": self.wall_minutes * 60,
            }))
