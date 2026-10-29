"""Restore archive files that a manifest lists but the archive never received.

Reads the audit report taken before the correction, and for each `missing`
archive claim finds a file under logs/ (the ignored run folders the archives
were copied from) whose SHA-256 equals the recorded digest. A file is copied
only on an exact digest match and is re-hashed after writing. Manifests are
never edited.

Provenance: identical bytes often exist in several runs (a compiled
simulator snapshot of the same testbench, say). For each manifest the source
run is the top-level logs/ folder that holds the most of its missing files
at their recorded relative paths: the run the manifest was built from. Each
file comes from that run when it has it, then from another run at the same
relative path, then from any file with the same digest. restored.json
records which applied.

A target that already exists with the recorded digest is recorded, not
copied again, so the record can be rebuilt after the restore. Any other
existing target is an error.

The inherited pre-resume validation manifest in seed-binding-live-recovery-01
is skipped: its entries describe the predecessor run and are proven from
seed-binding-quota-block-01 by tools/evidence_exceptions.json instead.

Usage: python restore_uncopied.py <audit-before.json> <restored.json>
"""
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
LOGS = ROOT / "logs"
SKIP = "evidence/2026-10-24/seed-binding-live-recovery-01/"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_of(path):
    return path.relative_to(LOGS).parts[0]


def main(report_path, out_path):
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    wanted = [row for row in report["failures"]
              if row["status"] == "missing" and not row["manifest"].startswith(SKIP)]
    names = {Path(row["path"].replace("\\", "/")).name for row in wanted}
    by_digest = defaultdict(list)
    for base, dirs, files in os.walk(LOGS):
        for name in files:
            if name in names:
                path = Path(base) / name
                by_digest[sha256(path)].append(path)

    def at_path(row):
        rel = row["path"].replace("\\", "/")
        return [p for p in by_digest.get(row["sha256"], ()) if p.as_posix().endswith("/" + rel)]

    home = {}
    for manifest in sorted({row["manifest"] for row in wanted}):
        votes = Counter(run for row in wanted if row["manifest"] == manifest
                        for run in {run_of(p) for p in at_path(row)})
        home[manifest] = min(votes, key=lambda run: (-votes[run], run)) if votes else None

    restored, unresolved = [], []
    for row in wanted:
        rel = row["path"].replace("\\", "/")
        target = ROOT / os.path.dirname(row["manifest"]) / rel
        matched = at_path(row)
        own = sorted(p for p in matched if run_of(p) == home[row["manifest"]])
        if own:
            source, how = own[0], "manifest_run"
        elif matched:
            source, how = sorted(matched)[0], "same_path_other_run"
        elif by_digest.get(row["sha256"]):
            source, how = sorted(by_digest[row["sha256"]])[0], "digest_only"
        else:
            unresolved.append(row)
            continue
        if target.exists():
            if sha256(target) != row["sha256"]:
                raise SystemExit(f"refusing to overwrite {target}: it exists with another digest")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            if sha256(target) != row["sha256"]:
                raise SystemExit(f"digest changed while copying {target}")
        restored.append({"manifest": row["manifest"], "path": rel, "sha256": row["sha256"],
                         "manifest_run": f"logs/{home[row['manifest']]}" if home[row["manifest"]] else None,
                         "restored_from": source.relative_to(ROOT).as_posix(), "source": how})
    Path(out_path).write_text(json.dumps({"restored": restored, "unresolved": unresolved}, indent=2) + "\n",
                              encoding="utf-8", newline="\n")
    print(f"restored {len(restored)}, unresolved {len(unresolved)}: {dict(Counter(r['source'] for r in restored))}")
    return 1 if unresolved else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
