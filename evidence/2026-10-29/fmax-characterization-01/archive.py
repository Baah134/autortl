"""Copy the Fmax sweep and the packet FIFO doctor-options check into this folder.

Every attempt's TCL, reports and Vivado console output are kept; only Vivado
scratch folders (.Xil/) are left out. archive-manifest.json then lists the
SHA-256 of every file here, and tools/evidence_audit.py checks it in CI.

    python archive.py <scratch dir holding fmax_run and packet_doctor_knobs>
"""
import hashlib
import json
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
SOURCES = {"sweep": "fmax_run", "packet-fifo-with-doctor-options": "packet_doctor_knobs/both"}


def main(scratch):
    scratch = Path(scratch)
    for name, src in SOURCES.items():
        root = scratch / src
        for path in sorted(root.rglob("*")):
            rel = path.relative_to(root)
            if path.is_file() and ".Xil" not in rel.parts:
                target = HERE / name / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
    files = {p.relative_to(HERE).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(HERE.rglob("*")) if p.is_file() and p.name != "archive-manifest.json"}
    (HERE / "archive-manifest.json").write_text(json.dumps(files, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(files)} files archived")


if __name__ == "__main__":
    main(sys.argv[1])
