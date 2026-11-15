"""Run every registered cell of a frozen manifest, one at a time, safely.

    python -m benchmark.campaign --manifest M.json --dataset D --attempt DIR [--model X] [--max-cells N]

Order is trial-major (a complete trial 0 over every task before trial 1), tasks
in manifest order, arms single_call, ablation, full. A cell whose output
directory exists is never rerun, so the command is safe to restart after an
interruption. The campaign stops, without spending further cells, when:

- a cell ends `model_blocked` (quota or authentication): exit code 3;
- `--max-interrupted` consecutive cells end `interrupted` (infrastructure): exit 4.

Progress is appended to `<attempt>/campaign.log` as JSON lines. Grading is a
separate step (`python -m benchmark.report grade`) that refuses to start until
every cell is sealed.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from . import artifacts, pilot
from . import verilogeval as ve

ARM_ORDER = ("single_call", "ablation", "full")
EXIT_DONE, EXIT_MODEL_BLOCKED, EXIT_INTERRUPTED = 0, 3, 4


def ordered_cells(manifest: dict) -> list[tuple[str, str, int]]:
    """(task, arm, trial) in trial-major, manifest-task, fixed-arm order."""
    tasks = [t["id"] for t in manifest["tasks"]]
    registered = {(c["task"], c["arm"], c["trial"]) for c in manifest["cells"]}
    trials = sorted({c["trial"] for c in manifest["cells"]})
    return [(task, arm, trial) for trial in trials for task in tasks for arm in ARM_ORDER
            if (task, arm, trial) in registered]


def cell_dir(attempt: Path, cell: tuple[str, str, int]) -> Path:
    return Path(attempt) / "runs" / f"{cell[0]}-{cell[1]}-{cell[2]}"


def run_cell(manifest: dict, task: ve.Task, cell: tuple[str, str, int], out_dir: Path,
             model: str | None = None) -> dict:
    """Dispatch one cell to its arm runner (pilot settings and budgets from the manifest)."""
    _, arm, trial = cell
    if arm == "single_call":
        return pilot.run_single_call(manifest, task, out_dir, trial=trial, model=model)
    return pilot.run_full(manifest, task, out_dir, trial=trial, model=model, arm=arm)


def run_campaign(manifest: dict, dataset: Path, attempt: Path, *, model: str | None = None,
                 max_cells: int | None = None, max_interrupted: int = 3, runner=run_cell,
                 clock=time.time) -> dict:
    """Run pending cells in order; return {"exit", "ran", "skipped", "pending", "reason"}."""
    attempt = Path(attempt)
    (attempt / "runs").mkdir(parents=True, exist_ok=True)
    log = attempt / "campaign.log"
    cells = ordered_cells(manifest)
    ran = skipped = streak = 0

    def note(**event):
        with log.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"at": round(clock(), 3), **event}) + "\n")

    def finish(code, reason):
        pending = sum(not cell_dir(attempt, c).exists() for c in cells)
        note(event="stop", exit=code, reason=reason, ran=ran, skipped=skipped, pending=pending)
        return {"exit": code, "ran": ran, "skipped": skipped, "pending": pending, "reason": reason}

    for cell in cells:
        out_dir = cell_dir(attempt, cell)
        if out_dir.exists():  # sealed, or spent by an interrupted launch: never rerun
            skipped += 1
            continue
        if max_cells is not None and ran >= max_cells:
            return finish(EXIT_DONE, "max_cells reached")
        note(event="start", task=cell[0], arm=cell[1], trial=cell[2])
        record = runner(manifest, ve.load_task(dataset, cell[0]), cell, out_dir, model)
        ran += 1
        termination = record["termination"]
        note(event="sealed", task=cell[0], arm=cell[1], trial=cell[2], kind=record["kind"],
             termination=termination, receipt_id=record["receipt_id"])
        if termination == "model_blocked":
            return finish(EXIT_MODEL_BLOCKED, f"model blocked at {cell[0]} {cell[1]} trial {cell[2]}")
        streak = streak + 1 if termination == "interrupted" else 0
        if streak >= max_interrupted:
            return finish(EXIT_INTERRUPTED, f"{streak} consecutive interrupted cells")
    return finish(EXIT_DONE, "all cells attempted")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m benchmark.campaign")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--attempt", required=True, type=Path)
    parser.add_argument("--model")
    parser.add_argument("--max-cells", type=int)
    parser.add_argument("--max-interrupted", type=int, default=3)
    a = parser.parse_args(argv)
    manifest = artifacts.load_manifest(a.manifest, public_root=a.dataset, private_root=a.dataset)
    result = run_campaign(manifest, a.dataset, a.attempt, model=a.model, max_cells=a.max_cells,
                          max_interrupted=a.max_interrupted)
    print(json.dumps(result, indent=2))
    return result["exit"]


if __name__ == "__main__":
    sys.exit(main())
