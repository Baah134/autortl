#!/usr/bin/env python3
"""AutoRTL v4 CLI.

  python run.py optimize --design d.v --tb d_tb.v --top d --objective minimize_luts
  python run.py build    --spec designs/uart/spec.md --objective maximize_freq
  python run.py resume   --run logs/run_v4_.../
  python run.py bench    --tier 0
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from autortl.config import RunConfig
from autortl.fsm import Orchestrator


def main():
    ap = argparse.ArgumentParser(prog="autortl")
    sub = ap.add_subparsers(dest="cmd", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--target_part", default="xc7a35tcpg236-1")
    common.add_argument("--target_freq_mhz", type=float, default=100.0)
    common.add_argument("--objective", default="minimize_luts",
                        choices=["minimize_luts", "minimize_ffs",
                                 "maximize_freq", "minimize_power"])
    common.add_argument("--iterations", type=int, default=10)
    common.add_argument("--best_of_n", type=int, default=4)
    common.add_argument("--vivado", default="vivado")
    common.add_argument("--xvlog", default="xvlog")
    common.add_argument("--xelab", default="xelab")
    common.add_argument("--xsim", default="xsim")
    common.add_argument("--route", default=None,
                        help="override e.g. generator=openrouter.nemotron-super")

    p_opt = sub.add_parser("optimize", parents=[common])
    p_opt.add_argument("--design", required=True, type=Path)
    p_opt.add_argument("--tb", type=Path, default=None)
    p_opt.add_argument("--top", required=True)

    p_bld = sub.add_parser("build", parents=[common])
    p_bld.add_argument("--spec", required=True, type=Path)

    p_res = sub.add_parser("resume", parents=[common])
    p_res.add_argument("--run", required=True, type=Path)
    p_res.add_argument("--design", type=Path, default=None)
    p_res.add_argument("--tb", type=Path, default=None)
    p_res.add_argument("--top", default="")

    p_bch = sub.add_parser("bench")
    p_bch.add_argument("--tier", type=int, required=True)

    a = ap.parse_args()

    if a.cmd == "bench":
        from curriculum.runner import run_tier
        sys.exit(run_tier(a.tier))

    kw = dict(target_part=a.target_part, target_freq_mhz=a.target_freq_mhz,
              objective=a.objective, max_iterations=a.iterations,
              best_of_n=a.best_of_n, vivado_bin=a.vivado, xvlog_bin=a.xvlog,
              xelab_bin=a.xelab, xsim_bin=a.xsim)

    if a.cmd == "optimize":
        cfg = RunConfig(mode="optimize", top_module=a.top, design_path=a.design,
                        testbench_path=a.tb, **kw)
        orch = Orchestrator(cfg)
    elif a.cmd == "build":
        cfg = RunConfig(mode="build", spec_path=a.spec, **kw)
        orch = Orchestrator(cfg)
    else:  # resume
        cfg = RunConfig(mode="optimize", top_module=a.top,
                        design_path=a.design, testbench_path=a.tb, **kw)
        orch = Orchestrator(cfg, run_dir=a.run)

    summary = orch.run()
    print(json.dumps({k: v for k, v in summary.items()
                      if k in ("status", "best_iteration", "run_dir")}, indent=2))


if __name__ == "__main__":
    main()
