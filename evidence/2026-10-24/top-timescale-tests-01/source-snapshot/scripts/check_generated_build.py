"""Independently simulate a completed build's exact winner and declared children.

Never recursively collect Verilog: run directories also contain stubs and mutants.
The supplied TB must be independently authored and qualified before this check.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from autortl.config import RunConfig
from autortl.spec import DesignSpec
from autortl.state import atomic_write_text
from autortl.triage import FailureKind
from autortl.vivado import xsim_run


def prepare(run, testbench, output):
    run, testbench, output = Path(run).resolve(), Path(testbench).resolve(), Path(output).resolve()
    config = RunConfig.load(run / "config.json")
    if config.mode != "build" or config.spec_path is None:
        raise ValueError("requires a typed completed build")
    spec = DesignSpec.load(config.spec_path)
    summary = json.loads((run / "run_summary.json").read_text(encoding="utf-8"))
    if summary.get("status") != "done" or summary.get("top_module") != spec.top_name:
        raise ValueError("build has not completed with the declared top")
    sources = [run / (spec.top_name + "_best.v")]
    sources += [run / "modules" / m.name / (m.name + ".v") for m in spec.modules]
    # Read every required artifact before creating the fresh destination.
    inputs = [(p, p.read_bytes()) for p in sources + [testbench]]
    output.mkdir(parents=True, exist_ok=False)
    copied, identities = [], []
    for index, (original, data) in enumerate(inputs):
        target = output / ("tb.v" if index == len(sources) else f"source_{index}.v")
        target.write_bytes(data)
        copied.append(target)
        identities.append({"original": str(original), "copy": target.name,
                           "sha256": hashlib.sha256(data).hexdigest()})
    atomic_write_text(output / "inputs.json", json.dumps({"build": str(run),
        "scope": "Independent final simulation; no new synthesis or optimization claim.",
        "top": spec.top_name, "inputs": identities}, indent=2))
    return config, spec.top_name, copied[:-1], copied[-1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--tb", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    output = args.output.resolve()
    config, top, sources, tb = prepare(args.run, args.tb, output)
    passed, error, kind = xsim_run(sources, tb, top + "_tb", config, output, timeout=60)
    log = output / "sim_log.txt"
    raw = log.read_text(encoding="utf-8", errors="replace") if log.is_file() else ""
    ok = (passed is True and kind == FailureKind.DESIGN and
          re.search(r"(?m)^\s*TEST PASSED\s*$", raw) is not None and
          re.search(r"FAIL|watchdog|timeout|timed\s+out", raw, re.I) is None)
    result = {"ok": ok, "passed": passed, "error": error, "failure_kind": kind.value,
              "top": top, "scope": "Independent simulation of the saved winner and exact declared children."}
    atomic_write_text(output / "result.json", json.dumps(result, indent=2))
    manifest = {p.relative_to(output).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(output.iterdir()) if p.is_file()}
    atomic_write_text(output / "archive-manifest.json", json.dumps(manifest, indent=2))
    print(json.dumps(result), flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
