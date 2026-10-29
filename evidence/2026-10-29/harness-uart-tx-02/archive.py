"""Copy the fixed-harness UART TX run (04) and its checks into this folder.

Everything is copied byte for byte except simulator snapshots (xsim.dir/,
which holds compiled executables) and Vivado scratch folders (.Xil/). Those
are tool by-products, rebuilt by any rerun; every log, report, source, prompt
and journal entry is kept. archive-manifest.json then lists the SHA-256 of
every file here, and tools/evidence_audit.py checks it in CI.

    python archive.py <scratch dir holding the qualification and sim runs>
"""
import hashlib
import json
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SKIP_DIRS = {"xsim.dir", ".Xil"}
RUNS = {"run-04-done": "logs/harness-uart-tx-04"}
CONSOLES = {"run-04-done/console.txt": "logs/harness-uart-tx-04.console.txt"}
CHECKS = {"uart_tx_tb": "r04_uart_tx_tb", "verify-winner": "r04_verify_winner", "board-sim": "r04_board"}
BOARD = ROOT / "hardware/basys3/harness_built/uart_tx/board/build-run04"
BOARD_FILES = ["basys3_harness_uart_tx.bit", "build_console.txt", "timing_summary.rpt", "utilization.rpt",
               "harness_tx_utilization.rpt", "drc.rpt", "program_console.txt", "hw_chunked_100000.txt",
               "hw_chunked_20000_after.txt", "hw_wrong_baud_100000.txt",
               "hw_stream_30000.txt"]


def copy_tree(src, dst):
    for path in sorted(src.rglob("*")):
        rel = path.relative_to(src)
        if any(part in SKIP_DIRS for part in rel.parts) or not path.is_file():
            continue
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)


def main(scratch):
    scratch = Path(scratch)
    for name, src in RUNS.items():
        copy_tree(ROOT / src, HERE / name)
    for rel, src in CONSOLES.items():
        shutil.copyfile(ROOT / src, HERE / rel)
    for name, src in CHECKS.items():
        copy_tree(scratch / src, HERE / "checks" / name)
    (HERE / "board").mkdir(exist_ok=True)
    for name in BOARD_FILES:
        shutil.copyfile(BOARD / name, HERE / "board" / name)
    files = {p.relative_to(HERE).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(HERE.rglob("*")) if p.is_file() and p.name != "archive-manifest.json"}
    (HERE / "archive-manifest.json").write_text(json.dumps(files, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(files)} files archived")


if __name__ == "__main__":
    main(sys.argv[1])
