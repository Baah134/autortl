"""Simulation vectors: stimulus and expected bytes from the reference model,
with a restart (UART break) in the middle that resets the model."""
from __future__ import annotations

from pathlib import Path
import random

from .models import model_for


def build(design: str, count: int, restart_at: int, seed: int = 2026):
    """Return (stimulus transactions, expected results) with one mid-stream restart."""
    if not 0 < restart_at < count:
        raise ValueError("restart_at must fall inside the stream")
    model = model_for(design)
    rng = random.Random(seed)
    first = model.stimulus(rng, restart_at)
    second = model.stimulus(rng, count - restart_at)  # leading cases again after the restart
    stimulus = first + second
    expected = []
    for index, tx in enumerate(stimulus):
        if index == restart_at:
            model.reset()
        expected.append(model.step(tx))
    return stimulus, expected


def write(directory: Path, stimulus, expected) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "stim.hex").write_text("".join(f"{b:02x}\n" for tx in stimulus for b in tx), encoding="ascii")
    (directory / "expect.hex").write_text("".join(f"{b:02x}\n" for out in expected for b in out), encoding="ascii")
