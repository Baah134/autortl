"""Archive a graded benchmark attempt as an evidence folder.

    python -m benchmark.archive --attempt DIR --out evidence/<date>/<name> [--catalog C.json --title "..."]

Copies what a reader needs to check the result, with home-directory paths
replaced by `<home>`: the frozen benchmark manifest (as
`benchmark_registration.json`; a file whose name contains "manifest" would be
audited as an archive manifest of this folder, and its hashes refer to the
external dataset), the runtime identity, the campaign log, the graded
`summary.json`, a `cells.json` (per cell: run record without its command line,
verdict, run-summary status), every sealed RTL file, the rendered report, and
an `archive-manifest.json` of SHA-256 digests. It refuses an ungraded attempt
and never overwrites an existing folder. The README is written by the
coordinator, who must state identity, protocol, results and limits.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from . import report
from autortl.fileio import file_sha256, read_json

HOME = re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+[^\\/\"' ]+|/(?:home|Users)/[^/\"' ]+")
SUMMARY_KEYS = ("status", "failure_kind", "error", "errors", "edit_scope", "top_module", "timing_closed",
                "verification_policy")
LOG_NAMES = ("campaign.log", "run_all.log")


class ArchiveError(ValueError):
    """The attempt is not ready to archive, or sanitising failed."""


def sanitize(text: str) -> str:
    return HOME.sub("<home>", text).replace("\r\n", "\n")


def archive_attempt(attempt: Path, out: Path, *, catalog: dict | None = None,
                    title: str = "VerilogEval comparison", forbidden: tuple[str, ...] = ()) -> dict:
    """Write the evidence folder; return its archive manifest (name -> sha256)."""
    attempt, out = Path(attempt), Path(out)
    summary_path = attempt / "grades" / "summary.json"
    if not summary_path.is_file():
        raise ArchiveError("attempt has no grades/summary.json; grade it first")
    rows = read_json(summary_path)
    out.mkdir(parents=True, exist_ok=False)

    def put(name: str, text: str) -> None:
        text = sanitize(text)
        for word in forbidden:  # e.g. a user name that must never be published
            if word and word.lower() in text.lower():
                raise ArchiveError(f"{name} still contains a forbidden word after sanitising")
        target = out / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="\n")

    put("benchmark_registration.json", (attempt / "manifest.json").read_text(encoding="utf-8"))
    identity = attempt / "runtime-identity.txt"
    if identity.is_file():
        put("runtime-identity.txt", identity.read_text(encoding="utf-8"))
    for name in LOG_NAMES:
        if (attempt / name).is_file():
            put(name, (attempt / name).read_text(encoding="utf-8", errors="replace"))
    put("summary.json", json.dumps(rows, indent=1) + "\n")
    cells = {}
    for run in sorted((attempt / "runs").glob("*/run.json")):
        name = run.parent.name
        record = read_json(run)
        record.get("accounting", {}).pop("command", None)
        entry = {"run": record}
        verdict = attempt / "grades" / name / "verdict.json"
        if verdict.is_file():
            entry["verdict"] = read_json(verdict)
        run_summary = run.parent / "run" / "run_summary.json"
        if run_summary.is_file():
            data = read_json(run_summary)
            entry["run_summary"] = {key: data.get(key) for key in SUMMARY_KEYS if key in data}
        cells[name] = entry
        rtl_root = run.parent / "submission" / "rtl"
        for source in sorted(p for p in rtl_root.rglob("*") if p.suffix in (".v", ".sv")) if rtl_root.is_dir() else []:
            flat = source.relative_to(rtl_root).as_posix().replace("/", "__")
            put(f"rtl/{name}__{flat}", source.read_text(encoding="utf-8", errors="replace"))
    put("cells.json", json.dumps(cells, indent=1) + "\n")
    for row in rows:
        row.setdefault("trial", 0)
    stats = report.summarize(rows, catalog)
    put("report.md", report.render_markdown(stats, title))
    put("report.json", json.dumps(stats, indent=1) + "\n")
    manifest = {p.relative_to(out).as_posix(): file_sha256(p)
                for p in sorted(out.rglob("*")) if p.is_file()}
    (out / "archive-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    return manifest


def seal(out: Path) -> dict:
    """Rewrite archive-manifest.json after the coordinator adds README.md."""
    out = Path(out)
    manifest = {p.relative_to(out).as_posix(): file_sha256(p)
                for p in sorted(out.rglob("*")) if p.is_file() and p.name != "archive-manifest.json"}
    (out / "archive-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    return manifest


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m benchmark.archive")
    parser.add_argument("--attempt", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--title", default="VerilogEval comparison")
    parser.add_argument("--forbid", action="append", default=[], help="word that must not appear in any archived file")
    parser.add_argument("--seal", action="store_true", help="only rewrite archive-manifest.json for --out")
    a = parser.parse_args(argv)
    if a.seal:
        print(json.dumps({"sealed": len(seal(a.out))}))
        return 0
    if a.attempt is None:
        parser.error("--attempt is required unless --seal is given")
    catalog = read_json(a.catalog) if a.catalog else None
    manifest = archive_attempt(a.attempt, a.out, catalog=catalog, title=a.title, forbidden=tuple(a.forbid))
    print(json.dumps({"files": len(manifest), "out": str(a.out)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
