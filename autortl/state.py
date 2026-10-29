"""State files on disk — the only channel between roles, and the resume source.

contract.md   fixed harness optimization contract (immutable after creation)
plan.md       rewritten by planner
progress.md   append-only
designs.jsonl one line per iteration
state.json    FSM position + best pointers (crash-resume)
"""
from __future__ import annotations
import json
import re
import os
import tempfile
import time
import hashlib
from datetime import datetime
from pathlib import Path


_WINDOWS = os.name == "nt"
_REPLACE_RETRY_DELAYS = (.01, .02, .04, .08, .16, .32)


class CheckpointLockedError(PermissionError):
    """Another process held a checkpoint open for the whole bounded retry.

    Infrastructure, not a design outcome (taxonomy: checkpoint_replace_denied).
    The previous checkpoint is intact, so `run.py resume` continues once the
    other process lets go. A PermissionError, so existing handlers still apply.
    """


def _replace_checkpoint(temporary: str, path: Path) -> None:
    """Retry only known Windows sharing/access contention, for at most 0.63s.

    Reuse the flushed sibling file throughout. Never remove the old target to
    work around a lock: replacement must remain atomic, including on failure.
    Contention that outlasts the retry is raised as CheckpointLockedError.
    """
    first_error = None
    for attempt in range(len(_REPLACE_RETRY_DELAYS) + 1):
        try:
            os.replace(temporary, path)
            return
        except OSError as exc:
            if not _WINDOWS or getattr(exc, "winerror", None) not in (5, 32, 33):
                raise
            if first_error is None:
                first_error = exc
            if attempt == len(_REPLACE_RETRY_DELAYS):
                locked = CheckpointLockedError(
                    first_error.errno, f"checkpoint {path} stayed locked by another process for "
                    f"{sum(_REPLACE_RETRY_DELAYS):.2f}s (WinError {first_error.winerror}); the previous checkpoint "
                    "is intact. Close whatever holds it open (for example a `tail -F` of a run file) and run "
                    "`run.py resume`", str(path))
                locked.winerror = first_error.winerror
                raise locked from first_error
            time.sleep(_REPLACE_RETRY_DELAYS[attempt])


def atomic_write_text(path: Path, text: str) -> None:
    """Single-writer checkpoint: flush a sibling, then atomically replace.

    Windows sharing contention gets bounded retry. Failed replacement leaves the
    previous checkpoint intact; cleanup must never hide the original write error.
    This does not make external tool execution and budget charging transactional.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    write_failed = False
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        _replace_checkpoint(temporary, path)
    except BaseException:
        write_failed = True
        raise
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        except OSError:
            if not write_failed:
                raise


class RunState:
    def __init__(self, run_dir: Path):
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)

    @property
    def contract_path(self): return self.run_dir / "contract.md"
    @property
    def plan_path(self): return self.run_dir / "plan.md"
    @property
    def progress_path(self): return self.run_dir / "progress.md"
    @property
    def designs_path(self): return self.run_dir / "designs.jsonl"
    @property
    def fsm_path(self): return self.run_dir / "state.json"
    @property
    def spec_path(self): return self.run_dir / "design_spec.json"
    @property
    def events_path(self): return self.run_dir / "events.jsonl"

    def iter_dir(self, iteration: int) -> Path:
        d = self.run_dir / f"iter_{iteration:03d}"
        d.mkdir(parents=True, exist_ok=True)
        return d

    # contract / plan
    def write_contract(self, text: str): atomic_write_text(self.contract_path, text)
    def read_contract(self) -> str:
        return self.contract_path.read_text(encoding="utf-8") if self.contract_path.exists() else ""
    def write_plan(self, text: str): atomic_write_text(self.plan_path, text)
    def read_plan(self) -> str:
        return self.plan_path.read_text(encoding="utf-8") if self.plan_path.exists() else ""

    def extract_instruction(self) -> str:
        m = re.search(r"##\s*Instruction for generator\s*\n(.+?)(?=\n##|\Z)",
                      self.read_plan(), re.DOTALL)
        return m.group(1).strip() if m else self.read_plan()

    # progress
    def append_progress(self, iteration: int, summary: str, outcome: str,
                        event_id: str | None = None) -> None:
        identity = event_id or f"progress:{iteration}:{outcome}"
        marker = "<!-- event:" + hashlib.sha256(identity.encode()).hexdigest() + " -->"
        previous = self.progress_path.read_text(encoding="utf-8") if self.progress_path.exists() else ""
        if marker in previous:
            return
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        atomic_write_text(self.progress_path, previous +
                          f"\n{marker}\n## [{ts}] iter {iteration:03d} | {outcome}\n- {summary[:300]}\n")

    def read_progress(self, tail_lines: int = 60) -> str:
        if not self.progress_path.exists():
            return "(no progress yet)"
        return "\n".join(self.progress_path.read_text(encoding="utf-8").splitlines()[-tail_lines:])

    # designs
    def append_design(self, entry: dict) -> None:
        if "iteration" not in entry:
            raise ValueError("design history requires iteration")
        entries = self.read_designs()
        for existing in entries:
            if existing["iteration"] == entry["iteration"]:
                if existing != entry:
                    raise ValueError("conflicting design history for iteration")
                return
        atomic_write_text(self.designs_path,
                          "".join(json.dumps(e) + "\n" for e in entries + [entry]))

    def append_event(self, entry: dict, event_id: str | None = None) -> None:
        """Append immutable structured evidence; duplicate IDs are idempotent."""
        record = dict(entry)
        identity = event_id or record.get("event_id")
        if not identity:
            identity = hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()
        record["event_id"] = identity
        entries = self.read_events()
        for existing in entries:
            if existing["event_id"] == identity:
                if existing != record:
                    raise ValueError("conflicting immutable event")
                return
        atomic_write_text(self.events_path,
                          "".join(json.dumps(e) + "\n" for e in entries + [record]))

    def read_events(self) -> list[dict]:
        if not self.events_path.exists():
            return []
        return [json.loads(line) for line in self.events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()]

    def read_designs(self) -> list[dict]:
        if not self.designs_path.exists():
            return []
        return [json.loads(l) for l in self.designs_path.read_text(encoding="utf-8").splitlines()
                if l.strip()]

    # evaluations
    def write_evaluation(self, iteration: int, report: str) -> None:
        atomic_write_text(self.iter_dir(iteration) / "evaluation.md", report)

    def read_recent_evaluations(self, n: int = 3) -> list[str]:
        out = []
        for e in self.read_designs()[-n:]:
            p = self.iter_dir(e["iteration"]) / "evaluation.md"
            if p.exists():
                out.append(p.read_text(encoding="utf-8"))
        return out

    # fsm serialization
    def save_fsm(self, d: dict) -> None:
        atomic_write_text(self.fsm_path, json.dumps(d, indent=1, default=str))

    def load_fsm(self) -> dict | None:
        if self.fsm_path.exists():
            return json.loads(self.fsm_path.read_text(encoding="utf-8"))
        return None
