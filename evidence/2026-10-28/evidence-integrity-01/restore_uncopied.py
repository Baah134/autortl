"""Restore archive files that a manifest lists but the archive never received.

Reads the audit report taken before the correction, and for each `missing`
archive claim finds a file under logs/ (the ignored run folders the archives
were copied from) whose SHA-256 equals the recorded digest. A file is copied
only on an exact digest match and is re-hashed after writing. Manifests are
never edited. A source whose path ends with the claimed path is preferred over
another file that merely has the same bytes.

The inherited pre-resume validation manifest in seed-binding-live-recovery-01
is skipped: its entries describe the predecessor run and are proven from
seed-binding-quota-block-01 by tools/evidence_exceptions.json instead.

Usage: python restore_uncopied.py <audit-before.json> <restored.json>
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
SKIP ="evidence/2026-10-24/seed-binding-live-recovery-01/"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(report_path, out_path):
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    wanted = [row for row in report["failures"]
              if row["status"] == "missing" and not row["manifest"].startswith(SKIP)]
    names = {Path(row["path"].replace("\\", "/")).name for row in wanted}
    by_digest = {}
    for base, dirs, files in os.walk(ROOT / "logs"):
        for name in files:
            if name in names:
                path = Path(base) / name
                by_digest.setdefault(sha256(path), []).append(path)
    restored, unresolved = [], []
    for row in wanted:
        rel = row["path"].replace("\\", "/")
        target = ROOT / os.path.dirname(row["manifest"]) / rel
        sources = sorted(by_digest.get(row["sha256"], ()),
                         key=lambda p: (not p.as_posix().endswith("/" + rel), p.as_posix()))
        if not sources:
            unresolved.append(row)
            continue
        if target.exists():
            raise SystemExit(f"refusing to overwrite existing {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(sources[0], target)
        if sha256(target) != row["sha256"]:
            raise SystemExit(f"digest changed while copying {target}")
        restored.append({"manifest": row["manifest"], "path": rel, "sha256": row["sha256"],
                         "restored_from": sources[0].relative_to(ROOT).as_posix(),
                         "path_matched": sources[0].as_posix().endswith("/" + rel)})
    Path(out_path).write_text(json.dumps({"restored": restored, "unresolved": unresolved}, indent=2) + "\n",
                              encoding="utf-8", newline="\n")
    print(f"restored {len(restored)}, unresolved {len(unresolved)}, "
          f"by path {sum(r['path_matched'] for r in restored)}, by digest only "
          f"{sum(not r['path_matched'] for r in restored)}")
    return 1 if unresolved else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
