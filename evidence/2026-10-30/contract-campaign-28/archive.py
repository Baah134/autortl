"""Copy the contract-campaign-28 gate into this folder.

Everything the gate wrote is copied byte for byte except simulator snapshots
(xsim.dir/) and Vivado scratch folders (.Xil/). The curriculum history at
the end of the gate and the exact runner are copied too, and role-report.md
summarizes each role's calls, verdicts and repairs (tools/role_report.py).
archive-manifest.json lists the SHA-256 of every file here.

    python archive.py
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NAME = "contract-campaign-28"
SKIP_DIRS = {"xsim.dir", ".Xil"}


def main():
    run = ROOT / "logs" / NAME
    for path in sorted(run.rglob("*")):
        rel = path.relative_to(run)
        if path.is_file() and not any(part in SKIP_DIRS for part in rel.parts):
            target = HERE / "run" / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
    for suffix in ("source-freeze.json", "tests.json", "prelaunch.json", "launch-result.json", "console.txt"):
        name = f"{NAME}-{suffix}" if suffix != "console.txt" else f"{NAME}.console.txt"
        shutil.copyfile(ROOT / "logs" / name, HERE / name)
    shutil.copyfile(ROOT / "curriculum" / "results.jsonl", HERE / f"history-at-{NAME}.jsonl")
    shutil.copyfile(ROOT / "tools" / "tier0_gate.py", HERE / "tier0_gate.py")
    report = subprocess.run([sys.executable, str(ROOT / "tools" / "role_report.py"), str(HERE / "run")],
                            capture_output=True, text=True, encoding="utf-8", check=True).stdout
    (HERE / "role-report.md").write_text(report, encoding="utf-8", newline="\n")
    files = {p.relative_to(HERE).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(HERE.rglob("*")) if p.is_file() and p.name != "archive-manifest.json"}
    (HERE / "archive-manifest.json").write_text(json.dumps(files, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(files)} files archived")


if __name__ == "__main__":
    main()
