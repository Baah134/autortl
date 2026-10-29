"""Program each archived harness-winner bitstream and rerun its board checks.

Copies each hardware report into OUT/<design>/ as soon as it is written.
"""
import json
import os
from pathlib import Path
import shutil
import sys

REPO = Path(r"C:\Users\prince.baah\Downloads\autortl-work")
SUITE = REPO / "hardware" / "basys3" / "harness_winners"
BITS = REPO / "evidence" / "2026-10-28" / "basys3-bitstreams-01" / "harness_winners"
OUT = Path(sys.argv[1])
os.chdir(SUITE)
sys.path.insert(0, str(SUITE))
from hwsuite.cli import main  # noqa: E402

OUT.mkdir(parents=True, exist_ok=True)
results = {}
for design in ("fir4", "elastic_dot4", "dot4_pipeline", "iterative_divider", "packet_fifo", "sync_fifo"):
    bit = str(BITS / f"{design}.bit")
    dest = OUT / design
    dest.mkdir(exist_ok=True)
    codes = {"program": main(["program", "--design", design, "--bit", bit])}
    shutil.copy(SUITE / "build" / design / "impl" / "program_console.txt", dest / "program_console.txt")
    codes["model_50000"] = main(["hw", "--design", design, "--bit", bit, "--port", "COM10", "--count", "50000"])
    shutil.copy(SUITE / "build" / design / "hw" / "model_50000.json", dest / "model_50000.json")
    codes["wrong_model_2000"] = main(["hw", "--design", design, "--bit", bit, "--port", "COM10",
                                      "--count", "2000", "--wrong-model"])
    shutil.copy(SUITE / "build" / design / "hw" / "wrong_model_2000.json", dest / "wrong_model_2000.json")
    results[design] = codes
    print(design, codes, flush=True)
(OUT / "exit_codes.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8", newline="\n")
sys.exit(0 if all(v == 0 for c in results.values() for v in c.values()) else 1)
