"""Deterministic watchdog: system-level pathology detection from state files.

No LLM. Emits typed signals the FSM consumes. The optional LLM diagnosis
layer only runs when these mechanical checks fire something unclassifiable.
"""
from __future__ import annotations
from dataclasses import dataclass
from .cache import code_hash


@dataclass
class Signal:
    kind: str          # STAGNATION | CHURN | REPEATED_ERROR | BUDGET_ANOMALY
    detail: str


def inspect(history: list[dict], recent_codes: list[str],
            recent_errors: list[str], budget_fraction: float) -> list[Signal]:
    signals: list[Signal] = []

    # STAGNATION: >=3 consecutive iterations without a new best
    tail = history[-3:]
    if len(tail) == 3 and not any(h.get("is_best") for h in tail):
        signals.append(Signal("STAGNATION", "3 consecutive iterations without improvement"))

    # CHURN: last two generated candidates hash-identical
    if len(recent_codes) >= 2 and code_hash(recent_codes[-1]) == code_hash(recent_codes[-2]):
        signals.append(Signal("CHURN", "generator produced identical code twice running"))

    # REPEATED_ERROR: same error signature 3x
    if len(recent_errors) >= 3 and len(set(e[:120] for e in recent_errors[-3:])) == 1:
        signals.append(Signal("REPEATED_ERROR",
                              f"same error 3x: {recent_errors[-1][:120]}"))

    # BUDGET_ANOMALY: >50% budget gone with zero accepted designs
    if budget_fraction < 0.5 and history and not any(h.get("is_best") for h in history[1:]):
        signals.append(Signal("BUDGET_ANOMALY",
                              "over half the budget spent with no improvement"))
    return signals
