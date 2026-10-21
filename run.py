#!/usr/bin/env python3
"""AutoRTL v4 CLI.

  python run.py optimize --design d.v --tb d_tb.v --top d --objective minimize_luts
  python run.py build    --spec designs/uart/spec.md --objective maximize_freq
  python run.py resume   --run logs/run_v4_.../
  python run.py bench    --tier 0
"""
import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from autortl.config import RunConfig
from autortl.fsm import Orchestrator


def main(argv=None):
    ap = argparse.ArgumentParser(prog="autortl")
    sub = ap.add_subparsers(dest="cmd", required=True)

    common = argparse.ArgumentParser(add_help=False, argument_default=argparse.SUPPRESS)
    common.add_argument("--target_part", "--target-part")
    common.add_argument("--target_freq_mhz", "--target-freq-mhz", type=float)
    common.add_argument("--objective",
                        choices=["minimize_luts", "minimize_ffs",
                                 "maximize_freq", "minimize_power"])
    common.add_argument("--iterations", type=int)
    common.add_argument("--best_of_n", "--best-of-n", type=int)
    common.add_argument("--vivado")
    common.add_argument("--xvlog")
    common.add_argument("--xelab")
    common.add_argument("--xsim")
    common.add_argument("--output-dir", "--work-dir", type=Path,
                        help="exact new run directory (benchmark: campaign output root)")
    common.add_argument("--max-llm-calls", type=int)
    common.add_argument("--max-vivado-minutes", type=float)
    common.add_argument("--max-wall-minutes", type=float)
    common.add_argument("--max-infra-retries", type=int)
    common.add_argument("--route", help="unsupported: routing is Codex-only")

    p_opt = sub.add_parser("optimize", parents=[common])
    p_opt.add_argument("--design", required=True, type=Path)
    p_opt.add_argument("--tb", type=Path, default=None)
    p_opt.add_argument("--top", required=True)

    p_bld = sub.add_parser("build", parents=[common])
    p_bld.add_argument("--spec", required=True, type=Path)
    p_bld.add_argument("--tb", type=Path, default=None,
                       help="independent integration testbench")
    p_bld.add_argument("--top", default="")
    p_bld.add_argument("--generate-golden", action="store_true",
                       help="generate and qualify a unit oracle even when an independent --tb is supplied")

    p_res = sub.add_parser("resume", help="load config.json; no configuration overrides")
    p_res.add_argument("--run", required=True, type=Path)

    p_bch = sub.add_parser("bench", parents=[common])
    p_bch.add_argument("--tier", type=int, required=True)
    p_bch.add_argument("--entries", nargs="+", help="run only named entries; never holds the full tier")

    a = ap.parse_args(argv)
    if hasattr(a, "route"):
        ap.error("--route is unsupported; all roles use the configured Codex route")

    if a.cmd == "resume":
        try:
            cfg = RunConfig.load(a.run.resolve() / "config.json")
        except (OSError, ValueError, TypeError) as exc:
            ap.error(f"cannot resume saved configuration: {exc}")
        orch = Orchestrator(cfg, run_dir=a.run.resolve())
    else:
        names = {"target_part": "target_part", "target_freq_mhz": "target_freq_mhz",
                 "objective": "objective", "iterations": "max_iterations",
                 "best_of_n": "best_of_n", "vivado": "vivado_bin", "xvlog": "xvlog_bin",
                 "xelab": "xelab_bin", "xsim": "xsim_bin", "max_llm_calls": "max_llm_calls",
                 "max_vivado_minutes": "max_vivado_minutes", "max_wall_minutes": "max_wall_minutes",
                 "max_infra_retries": "max_infra_retries"}
        kw = {dest: getattr(a, source) for source, dest in names.items() if hasattr(a, source)}
        for key in ("max_iterations", "best_of_n", "target_freq_mhz"):
            if key in kw and (not math.isfinite(kw[key]) or kw[key] <= 0):
                ap.error(f"{key} must be positive")
        for key in ("max_llm_calls", "max_vivado_minutes", "max_wall_minutes", "max_infra_retries"):
            if key in kw and (not math.isfinite(kw[key]) or kw[key] < 0):
                ap.error(f"{key} cannot be negative")

    if a.cmd == "bench":
        from curriculum.runner import run_tier
        if hasattr(a, "output_dir"):
            kw["output_root"] = a.output_dir.resolve()
        if a.entries:
            kw["entries"] = a.entries
        return run_tier(a.tier, **kw)

    if a.cmd == "optimize":
        cfg = RunConfig(mode="optimize", top_module=a.top, design_path=a.design,
                        testbench_path=a.tb, **kw)
        orch = Orchestrator(cfg, run_dir=a.output_dir.resolve() if hasattr(a, "output_dir") else None)
    elif a.cmd == "build":
        cfg = RunConfig(mode="build", spec_path=a.spec, testbench_path=a.tb,
                        top_module=a.top, generate_golden=a.generate_golden, **kw)
        orch = Orchestrator(cfg, run_dir=a.output_dir.resolve() if hasattr(a, "output_dir") else None)

    summary = orch.run()
    print(json.dumps({k: v for k, v in summary.items()
                      if k in ("status", "best_iteration", "timing_closed", "improvement_kind", "run_dir")}, indent=2))
    return 0 if summary.get("status") == "done" else 1


if __name__ == "__main__":
    sys.exit(main())
