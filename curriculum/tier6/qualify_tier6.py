"""Qualify a tier6 entry's independent testbench against its reference and mutants.

The protocol and the code are tier4's: this file loads
curriculum/tier4/qualify_tier4.py and re-exports it, so tiers 4, 5 and 6 judge
qualification the same way. The testbench must PASS on qualification/reference.v
and FAIL every mutant in qualification/mutants.json with a raw assertion (a line
starting ``FAIL`` plus a ``TEST FAILED`` verdict). A watchdog, a missing verdict
or a compile error is not a detection.

    python curriculum/tier6/qualify_tier6.py <entry-dir> <out-dir> [--vivado BIN]

Importing this file launches no tools.
"""
import importlib.util
from pathlib import Path
import sys

_SOURCE = Path(__file__).resolve().parents[1] / "tier4" / "qualify_tier4.py"
_LOADER = importlib.util.spec_from_file_location("qualify_tier4", _SOURCE)
_SHARED = importlib.util.module_from_spec(_LOADER)
_LOADER.loader.exec_module(_SHARED)

DEFAULT_VIVADO = _SHARED.DEFAULT_VIVADO
load_entry = _SHARED.load_entry
judge = _SHARED.judge
simulate = _SHARED.simulate
main = _SHARED.main

if __name__ == "__main__":
    sys.exit(main())
