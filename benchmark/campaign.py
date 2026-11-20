"""Run every registered cell of a frozen manifest, one at a time, safely.

    python -m benchmark.campaign --manifest M.json --dataset D --attempt DIR [--model X]
                                 [--wait-minutes 20] [--max-wait-hours 12] [--max-cells N]

Order is trial-major (a complete trial 0 over every task before trial 1), tasks
in manifest order, arms single_call, ablation, full. A cell whose output
directory exists is never rerun, so the command is safe to restart. A cell
left with a directory but no sealed record (its process died mid-run) is sealed
`interrupted` with no submission, so grading is never blocked and the cell is
excluded from rates as infrastructure; it is never rerun.

Model availability. Before the first pending cell, and again after any cell
ends `model_blocked`, the campaign sends one tiny probe call. While the model
is blocked (quota or authentication) no cell is started, so a block never
spends more than the one cell that discovered it. Without `--wait-minutes` a
blocked probe ends the campaign with exit code 3; with it, the campaign probes
again every N minutes (up to `--max-wait-hours` in one wait) and then continues.

It also stops when `--max-interrupted` consecutive cells end `interrupted`
(infrastructure; exit code 4). Progress is appended to `<attempt>/campaign.log`
as JSON lines. Grading is a separate step (`python -m benchmark.report grade`)
that refuses to start until every cell is sealed; cells that ended on
infrastructure are excluded from its rates.
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
PROBE_PROMPT = "Reply with the single word OK."


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


def seal_spent(manifest: dict, cell: tuple[str, str, int], out_dir: Path) -> dict | None:
    """Seal a cell whose run died before sealing; None if it is already sealed.

    Reuses a receipt that was published before the process died; otherwise
    records a missing submission with termination `interrupted`. The run's own
    partial files stay in place for inspection.
    """
    out_dir = Path(out_dir)
    if (out_dir / "run.json").is_file():
        return None
    selected = pilot._cell(manifest, cell[0], cell[1], cell[2])
    submission = out_dir / "submission"
    receipt_file = submission / "receipt.json"
    if receipt_file.is_file():
        receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
        receipt = artifacts.load_artifact(submission, expected_id=receipt["id"])
    else:
        if submission.exists():  # a half-written receipt directory cannot be reused
            submission = out_dir / "submission-interrupted"
        receipt = artifacts.record_missing(manifest, {"task": cell[0], "trial": cell[2], "arm": cell[1]},
                                           destination=submission, termination="interrupted")
    record = pilot._finish(out_dir, selected, receipt, {"spent_unsealed": True,
                                                        "note": "process ended before the cell was sealed"})
    if submission.name != "submission":
        record["submission_dir"] = submission.name
        (out_dir / "run.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def model_available(model: str | None = None, ask=None) -> tuple[bool, str]:
    """One tiny model call outside any cell; (False, reason) when the model is blocked."""
    from autortl.budget import Budget
    from llm import client

    try:
        (ask or client.ask)("generator", PROBE_PROMPT, system="", budget=Budget(1, 1.0, 5.0), model=model)
        return True, ""
    except client.ModelCallError as exc:
        return False, f"{exc.code}: {str(exc)[:200]}"
    except RuntimeError as exc:
        if not str(exc).startswith("LLM_BUDGET:"):
            raise
        return False, str(exc)


def run_campaign(manifest: dict, dataset: Path, attempt: Path, *, model: str | None = None,
                 max_cells: int | None = None, max_interrupted: int = 3, runner=run_cell,
                 clock=time.time, probe=None, wait_seconds: float | None = None,
                 max_wait_seconds: float = 12 * 3600, sleep=time.sleep) -> dict:
    """Run pending cells in order; return {"exit", "ran", "skipped", "pending", "reason"}.

    probe: callable() -> (ok, reason), or None to skip availability checks.
    wait_seconds: None stops on a blocked probe; a number waits and probes again.
    """
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

    def available(where):
        """True when a cell may start; False means stop (the reason is logged by the caller)."""
        if probe is None:
            return True, ""
        waited = 0.0
        while True:
            ok, reason = probe()
            if ok:
                if waited:
                    note(event="model_available", after_seconds=round(waited))
                return True, ""
            if wait_seconds is None or waited + wait_seconds > max_wait_seconds:
                return False, f"model blocked {where}: {reason}"
            note(event="waiting_for_model", where=where, reason=reason, retry_in_seconds=wait_seconds)
            sleep(wait_seconds)
            waited += wait_seconds

    checked = False
    for cell in cells:
        out_dir = cell_dir(attempt, cell)
        if out_dir.exists():  # sealed, or spent by an interrupted launch: never rerun
            sealed = seal_spent(manifest, cell, out_dir)
            if sealed is not None:
                note(event="sealed_spent", task=cell[0], arm=cell[1], trial=cell[2],
                     kind=sealed["kind"], termination=sealed["termination"], receipt_id=sealed["receipt_id"])
            skipped += 1
            continue
        if max_cells is not None and ran >= max_cells:
            return finish(EXIT_DONE, "max_cells reached")
        if not checked:
            ok, reason = available(f"before {cell[0]} {cell[1]} trial {cell[2]}")
            if not ok:
                return finish(EXIT_MODEL_BLOCKED, reason)
            checked = True
        note(event="start", task=cell[0], arm=cell[1], trial=cell[2])
        record = runner(manifest, ve.load_task(dataset, cell[0]), cell, out_dir, model)
        ran += 1
        termination = record["termination"]
        note(event="sealed", task=cell[0], arm=cell[1], trial=cell[2], kind=record["kind"],
             termination=termination, receipt_id=record["receipt_id"])
        # A harness cell that hits the quota is sealed `interrupted` (its run summary is an
        # infrastructure stop), so both terminations trigger an availability check.
        if termination in ("model_blocked", "interrupted"):
            where = f"at {cell[0]} {cell[1]} trial {cell[2]}"
            if probe is None:
                if termination == "model_blocked":
                    return finish(EXIT_MODEL_BLOCKED, f"model blocked {where}")
            else:
                ok, reason = available(where)
                if not ok:
                    return finish(EXIT_MODEL_BLOCKED, reason)
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
    parser.add_argument("--wait-minutes", type=float,
                        help="while the model is blocked, probe again every N minutes instead of stopping")
    parser.add_argument("--max-wait-hours", type=float, default=12.0)
    parser.add_argument("--no-probe", action="store_true", help="skip model availability checks")
    a = parser.parse_args(argv)
    if a.wait_minutes is not None and a.wait_minutes < 1:
        parser.error("--wait-minutes must be at least 1")
    manifest = artifacts.load_manifest(a.manifest, public_root=a.dataset, private_root=a.dataset)
    result = run_campaign(manifest, a.dataset, a.attempt, model=a.model, max_cells=a.max_cells,
                          max_interrupted=a.max_interrupted,
                          probe=None if a.no_probe else (lambda: model_available(a.model)),
                          wait_seconds=None if a.wait_minutes is None else a.wait_minutes * 60,
                          max_wait_seconds=a.max_wait_hours * 3600)
    print(json.dumps(result, indent=2))
    return result["exit"]


if __name__ == "__main__":
    sys.exit(main())
