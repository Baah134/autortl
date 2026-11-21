"""Run positive and fault-injected generated-testbench cases with real Vivado."""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from autortl.config import RunConfig
from autortl.triage import FailureKind
from autortl.vivado import xsim_run
from tests.tbgen_live_cases import save
from autortl.doctor import tool_bins
from autortl.fileio import file_sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bin-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    config = RunConfig(mode="optimize", **tool_bins(args.bin_dir))
    results = []
    for case in save(out):
        work = out / case["case"]
        started = time.monotonic()
        passed, error, kind = xsim_run([work / "dut.v"], work / "tb.v", case["top"], config, work, timeout=60)
        detected = not passed and kind == FailureKind.DESIGN and (
            error.startswith("Testbench failures:") or error == "testbench reported failure")
        ok = passed if case["expected_pass"] else detected
        record = {**case, "ok": ok, "passed": passed, "error": error,
                  "failure_kind": kind.value, "seconds": time.monotonic() - started,
                  "source_sha256": file_sha256((work / "dut.v")),
                  "tb_sha256": file_sha256((work / "tb.v"))}
        results.append(record)
        (out / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(json.dumps(record), flush=True)
    return 0 if all(item["ok"] for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
