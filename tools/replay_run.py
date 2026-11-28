"""Replay a recorded run from its journal and compare what it rebuilds with what it recorded.

    python tools/replay_run.py --run <recorded run dir> --out <parent dir for the replay>

The harness under test is this checkout, or the one PYTHONPATH names (to
replay on an older commit, export it with `git archive` and point PYTHONPATH
at it).

Every model call and every Vivado result of a run is journaled (`journal/`),
so the orchestrator can run the whole run again with no model and no Vivado:
each stage returns its recorded result and restores its recorded artifacts.
What the harness writes around those results (state, facts, designs, the
winner, the summary) is rebuilt by the code under test. This tool does that
with every model and tool entry point replaced by one that refuses, then
compares the rebuilt files with the recorded ones. It is the acceptance test
for refactors that must not change behaviour (ROADMAP C6 item 4): replay
recorded runs on the old and the new code and require the same result.

The replay runs in a fresh directory, never in the recorded one. Recorded
files hold the run directory's absolute path, and hashes that cover those
files, so the copy is relocated: the old path is rewritten to the new one
(backslash, JSON-escaped and forward-slash forms) and every digest of a
rewritten file is replaced by the rewritten file's digest, repeated until
nothing changes. The replay directory's path is padded to the recorded
path's length, because the harness keeps fixed-length previews of reports
and a path of another length would move where they are cut.

Only the original run directory replays. An archived copy under `evidence/`
has home-directory paths sanitized, so its journal fails its own hash check
and the tool says so.

Comparison, per file outside `journal/` and `inputs/`:
- identical: same bytes after relocation;
- equivalent: JSON that is equal once a preview cut through the run path at
  the start or end of a string is allowed (the recorded and replayed paths
  are aligned character for character), or that only holds the digest of
  such a file;
- volatile, by name: `budget.json` (accounting; the replay makes no calls),
  `progress.md` (wall-clock stamps only), `metrics_cache.json` (keys hash a
  context that includes paths; values must match), `runtime.json` (the
  harness identity; reported, since a replay on new code is the point);
- live only: `events.jsonl` and tool byproducts that the journal never kept
  (simulator snapshots, journals, `.pb` files): written only while tools run;
- different, missing, extra: anything else. Any of these, or any refused
  call, fails the replay (exit 1).
"""
from __future__ import annotations

import argparse
import contextlib
import difflib
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # appended: PYTHONPATH=<other checkout> replays on that code

TOOL_ENTRY_POINTS = ("xvlog_check", "xsim_run", "run_synthesis", "full_metrics", "icarus_check")
# What fsm._stage keeps as stage artifacts, plus what the harness writes itself.
JOURNALED_SUFFIXES = (".v", ".sv", ".rpt", ".log", ".tcl", ".xdc")
JOURNALED_NAMES = ("sim_log.txt", "qualification.json")
HARNESS_SUFFIXES = (".json", ".jsonl", ".md")
LIVE_ONLY_NAMES = ("events.jsonl",)
SEED_PATTERNS = ("proposal_*.json",)  # written inside a stage, never kept as a stage artifact
VOLATILE = {"budget.json": "accounting (the replay makes no calls)",
            "progress.md": "wall-clock stamps",
            "metrics_cache.json": "cache keys hash a context that includes paths",
            "runtime.json": "harness identity"}
DIGEST = re.compile(rb"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])")
STAMP = re.compile(rb"^## \[\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\]", re.MULTILINE)


class ReplayError(RuntimeError):
    """The recorded run cannot be replayed as given."""


class ReplayMiss(Exception):
    """The replay reached a model or tool call that the journal does not hold."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def path_forms(old: str, new: str) -> list[tuple[str, str]]:
    """The spellings of a run path in recorded files: native, JSON-escaped, forward-slash."""
    forms = [(old, new), (json.dumps(old)[1:-1], json.dumps(new)[1:-1]),
             (old.replace("\\", "/"), new.replace("\\", "/"))]
    return list(dict.fromkeys(forms))


def relocate(data: bytes, forms) -> bytes:
    for old, new in forms:
        data = data.replace(old.encode(), new.encode())
    return data


def relocate_all(files: dict, forms, extra: dict | None = None) -> dict:
    """Rewrite run paths, then rebind every digest of a rewritten file, to a fixed point.

    `files` maps any key to recorded bytes; `extra` maps further old digests to
    new ones (equivalent files found by the comparison).
    """
    moved = {key: relocate(data, forms) for key, data in files.items()}
    extra = {k.encode(): v.encode() for k, v in (extra or {}).items()}
    current = moved
    for _ in range(16):
        rebound = {sha256(files[k]).encode(): sha256(current[k]).encode()
                   for k in files if current[k] != files[k]}

        def swap(match, rebound=rebound):
            digest = rebound.get(match.group(), match.group())
            return extra.get(digest, digest)
        following = {key: DIGEST.sub(swap, data) for key, data in moved.items()}
        if following == current:
            return current
        current = following
    raise ReplayError("relocation did not reach a fixed point")


def replay_dir(run: Path, out: Path) -> Path:
    """A directory under `out` whose absolute path is exactly as long as the recorded one."""
    run, out = Path(run).resolve(), Path(out).resolve()
    padding = len(str(run)) - len(str(out)) - 1
    if padding < 1:
        raise ReplayError(f"--out {out} is too long: the replay path must be as long as the recorded "
                          f"path ({len(str(run))} characters); choose a shorter parent")
    return out / ("r" * padding)


def prepare(run: Path, out: Path) -> tuple[Path, list[tuple[str, str]]]:
    """Copy what a replay needs (inputs, journal, stage-written seeds) to a relocated directory."""
    run = Path(run).resolve()
    for name in ("config.json", "inputs.json", "journal", "inputs"):
        if not (run / name).exists():
            raise ReplayError(f"{run} has no {name}; not a recorded run directory")
    target = replay_dir(run, out)
    if target.exists():
        if not (target / "journal").is_dir():
            raise ReplayError(f"{target} exists and is not an earlier replay; refusing to delete it")
        shutil.rmtree(target)
    old = json.loads((run / "config.json").read_text(encoding="utf-8")).get("work_dir")
    if not old or Path(old).resolve() != run:
        raise ReplayError(f"{run}/config.json records work_dir {old!r}; replay the original run "
                          "directory, not a moved copy")
    forms = path_forms(old, str(target))
    keep = [p for name in ("journal", "inputs") for p in (run / name).rglob("*") if p.is_file()]
    keep += [run / "config.json", run / "inputs.json"]
    keep += [p for pattern in SEED_PATTERNS for p in run.rglob(pattern)
             if p.relative_to(run).parts[0] != "journal"]
    relocated = relocate_all({p.relative_to(run): p.read_bytes() for p in keep}, forms)
    for relative, data in relocated.items():
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    return target, forms


@contextlib.contextmanager
def offline(calls: list):
    """Replace every model and Vivado entry point with one that records the call and refuses."""
    from autortl import roles, tbqual, vivado
    # An older checkout may lack a later entry point (icarus_check); patch what exists.
    saved = [(vivado, name, getattr(vivado, name)) for name in TOOL_ENTRY_POINTS if hasattr(vivado, name)]
    saved += [(tbqual, "xsim_run", tbqual.xsim_run), (roles, "ask", roles.ask)]

    def refuse(label):
        def call(*args, **kwargs):
            calls.append(label)
            raise ReplayMiss(f"{label} was called; the journal holds no result for it")
        return call
    try:
        for module, name, _ in saved:
            setattr(module, name, refuse(f"{module.__name__}.{name}"))
        yield
    finally:
        for module, name, value in saved:
            setattr(module, name, value)


def replay(target: Path) -> tuple[dict, list[str]]:
    from autortl import fsm
    from autortl.config import RunConfig
    calls: list[str] = []
    with offline(calls):
        try:
            orchestrator = fsm.Orchestrator(RunConfig.load(target / "config.json"), target)
            # A live run appends unknown message IDs to data/; a replay leaves the repository alone.
            orchestrator.taxonomy.unknown_log = Path(os.devnull)
            summary = orchestrator.run()
        except ReplayMiss as exc:
            summary = {"status": "replay_miss", "error": str(exc)}
        except ValueError as exc:
            if "Stage evidence modified" in str(exc):
                raise ReplayError(f"the recorded journal fails its own hash check ({exc}); an archived "
                                  "copy is sanitized, replay the original run directory") from exc
            raise
    return summary, calls


def _edge_equal(recorded: str, replayed: str, forms) -> bool:
    """Equal strings, allowing a run path cut at either end by a fixed-length preview."""
    if recorded == replayed:
        return True
    if len(recorded) != len(replayed):
        return False
    for old, new in forms:
        for k in range(min(len(old), len(recorded)), 0, -1):
            if recorded.startswith(old[-k:]) and replayed.startswith(new[-k:]):
                recorded = new[-k:] + recorded[k:]
                break
        for k in range(min(len(old), len(recorded)), 0, -1):
            if recorded.endswith(old[:k]) and replayed.endswith(new[:k]):
                recorded = recorded[:-k] + new[:k]
                break
    return recorded == replayed


def _json_equal(recorded, replayed, forms) -> bool:
    if isinstance(recorded, dict) and isinstance(replayed, dict):
        return recorded.keys() == replayed.keys() and all(
            _json_equal(recorded[k], replayed[k], forms) for k in recorded)
    if isinstance(recorded, list) and isinstance(replayed, list):
        return len(recorded) == len(replayed) and all(
            _json_equal(a, b, forms) for a, b in zip(recorded, replayed))
    if isinstance(recorded, str) and isinstance(replayed, str):
        return _edge_equal(recorded, replayed, forms)
    return recorded == replayed


def _parse(name: str, data: bytes):
    text = data.decode("utf-8")
    if name.endswith(".jsonl"):
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    return json.loads(text)


def _equivalent(name: str, recorded: bytes, replayed: bytes, forms) -> bool:
    if not name.endswith((".json", ".jsonl")):
        return False
    try:
        return _json_equal(_parse(name, recorded), _parse(name, replayed), forms)
    except (UnicodeDecodeError, ValueError):
        return False


def _volatile_matches(name: str, recorded: bytes, replayed: bytes, forms) -> bool:
    if name in ("budget.json", "runtime.json"):
        return True
    if name == "progress.md":
        return STAMP.sub(b"## [stamp]", recorded) == STAMP.sub(b"## [stamp]", replayed)
    if name == "metrics_cache.json":
        try:
            a, b = json.loads(recorded), json.loads(replayed)
        except ValueError:
            return False
        key = lambda value: json.dumps(value, sort_keys=True)  # noqa: E731
        return _json_equal(sorted(a.values(), key=key), sorted(b.values(), key=key), forms)
    return False


def _live_only(relative: Path) -> bool:
    name = relative.name
    if name in LIVE_ONLY_NAMES:
        return True
    if name in JOURNALED_NAMES or relative.suffix in JOURNALED_SUFFIXES + HARNESS_SUFFIXES:
        return False
    return True


def compare(run: Path, target: Path, forms) -> dict:
    run, target = Path(run).resolve(), Path(target).resolve()

    def outputs(root):
        return {p.relative_to(root): p for p in root.rglob("*")
                if p.is_file() and p.relative_to(root).parts[0] not in ("journal", "inputs")}
    recorded_paths, replayed_paths = outputs(run), outputs(target)
    raw = {rel: p.read_bytes() for rel, p in recorded_paths.items()}
    # The journal and inputs take part in digest rebinding, as they did in prepare().
    raw.update({p.relative_to(run): p.read_bytes() for name in ("journal", "inputs")
                for p in (run / name).rglob("*") if p.is_file()})
    report = {"identical": [], "equivalent": [], "volatile": {}, "live_only": [], "different": [],
              "missing": [], "extra": sorted(str(r.as_posix()) for r in replayed_paths
                                             if r not in recorded_paths)}
    extra_digests: dict[str, str] = {}
    while True:
        recorded = relocate_all(raw, forms, extra_digests)
        found, settled = {}, {}
        for rel in sorted(recorded_paths):
            name = rel.as_posix()
            if rel not in replayed_paths:
                found[name] = "live_only" if _live_only(rel) else "missing"
                continue
            a, b = recorded[rel], replayed_paths[rel].read_bytes()
            if a == b:
                found[name] = "identical"
            elif rel.name in VOLATILE and rel.parent == Path(".") and _volatile_matches(rel.name, a, b, forms):
                found[name] = "volatile"
            elif _equivalent(rel.name, a, b, forms):
                found[name] = "equivalent"
                settled[sha256(a)] = sha256(b)
            else:
                found[name] = "different"
        if all(extra_digests.get(k) == v for k, v in settled.items()):
            break
        extra_digests.update(settled)
    for name, verdict in found.items():
        if verdict == "volatile":
            report["volatile"][name] = VOLATILE[Path(name).name]
        else:
            report[verdict].append(name)
    runtime = Path("runtime.json")
    report["runtime_changed"] = (runtime in recorded and (target / runtime).is_file()
                                 and recorded[runtime] != (target / runtime).read_bytes())
    report["ok"] = not (report["different"] or report["missing"] or report["extra"])
    report["_recorded"] = recorded
    return report


def _diff_excerpt(recorded: bytes, replayed: bytes, lines: int = 12) -> str:
    a = recorded.decode("utf-8", "replace").splitlines()
    b = replayed.decode("utf-8", "replace").splitlines()
    return "\n".join(list(difflib.unified_diff(a, b, "recorded", "replayed", lineterm="", n=0))[:lines])


def run_replay(run: Path, out: Path) -> dict:
    target, forms = prepare(run, out)
    summary, calls = replay(target)
    report = compare(run, target, forms)
    recorded = report.pop("_recorded")
    report.update({"replay_dir": str(target), "status": summary.get("status"),
                   "refused_calls": calls,
                   "excerpts": {name: _diff_excerpt(recorded[Path(name)], (target / name).read_bytes())
                                for name in report["different"][:5]}})
    report["ok"] = report["ok"] and not calls and summary.get("status") != "replay_miss"
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python tools/replay_run.py", description=__doc__.split("\n")[0])
    parser.add_argument("--run", required=True, type=Path, help="the recorded run directory (not an archive)")
    parser.add_argument("--out", required=True, type=Path, help="parent directory for the replay")
    a = parser.parse_args(argv)
    try:
        report = run_replay(a.run, a.out)
    except ReplayError as exc:
        print(f"replay refused: {exc}", file=sys.stderr)
        return 2
    counts = {key: len(report[key]) for key in ("identical", "equivalent", "volatile", "live_only",
                                                "different", "missing", "extra")}
    print(json.dumps({"ok": report["ok"], "status": report["status"], "replay_dir": report["replay_dir"],
                      "runtime_changed": report["runtime_changed"], "refused_calls": report["refused_calls"],
                      "counts": counts, "different": report["different"], "missing": report["missing"],
                      "extra": report["extra"], "volatile": report["volatile"]}, indent=1))
    for name, excerpt in report["excerpts"].items():  # stdout stays one JSON document
        print(f"\n--- {name}\n{excerpt}", file=sys.stderr)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
