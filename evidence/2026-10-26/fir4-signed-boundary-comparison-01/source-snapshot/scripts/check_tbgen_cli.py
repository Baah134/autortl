"""Run positive and fault-injected generated-testbench cases with real Vivado."""
import argparse
import hashlib
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bin-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    config = RunConfig(mode="optimize", **{
        name + "_bin": str(args.bin_dir.resolve() / (name + ".bat"))
        for name in ("vivado", "xvlog", "xelab", "xsim")})
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
                  "source_sha256": hashlib.sha256((work / "dut.v").read_bytes()).hexdigest(),
                  "tb_sha256": hashlib.sha256((work / "tb.v").read_bytes()).hexdigest()}
        results.append(record)
        (out / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(json.dumps(record), flush=True)
    return 0 if all(item["ok"] for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
