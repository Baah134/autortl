"""Bounded, model-free counter verification through the installed Vivado CLI.

Example: python scripts/check_counter_cli.py --bin-dir C:/AMDDesignTools/2025.2/Vivado/bin
Uses a fresh output directory and retains inputs, hashes, logs and reports.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from autortl.config import RunConfig
from autortl.tbqual import qualify
from autortl.vivado import xsim_run, run_synthesis, full_metrics
from autortl.metrics_gate import validate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bin-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    source = ROOT / "curriculum/tier0/counter"
    files = []
    hashes = {}
    for name in ("counter.v", "counter_tb.v"):
        path = out / name
        path.write_bytes((source / name).read_bytes())
        files.append(path)
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    cfg = RunConfig(mode="optimize", **{
        name + "_bin": str(args.bin_dir.resolve() / (name + ".bat"))
        for name in ("vivado", "xvlog", "xelab", "xsim")})
    result = {"source_sha256": hashes, "part": cfg.target_part,
              "period_ns": cfg.target_period_ns, "passed": False}
    try:
        sim_dir = out / "simulation"
        sim_dir.mkdir()
        ok, err, kind = xsim_run([files[0]], files[1], "counter_tb", cfg, sim_dir, timeout=60)
        result["simulation"] = {"passed": ok, "error": err, "kind": kind.value}
        if not ok:
            return 1
        ok, reason = qualify(files[0].read_text(), files[1], "counter", cfg, out)
        result["qualification"] = {"passed": ok, "reason": reason}
        if not ok:
            return 1
        impl = out / "implementation"
        impl.mkdir()
        ok, err, kind = run_synthesis([files[0]], "counter", cfg, impl, timeout=300)
        result["implementation"] = {"passed": ok, "error": err, "kind": kind.value}
        if not ok:
            return 1
        metrics = full_metrics(impl)
        metrics.sim_passed = True
        metrics.sim_error = ""
        validate(metrics, synthesis_ran=True)
        result["metrics"] = metrics.to_dict()
        result["passed"] = True
        return 0
    finally:
        (out / "result.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
