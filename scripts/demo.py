"""Simulated walkthrough of one optimize run. It measures nothing.

    python scripts/demo.py [--output-dir DIR]

This runs the real Orchestrator (state, journal, budget, resume checkpoints
and acceptance gates) on curriculum/tier0/mux4 for one iteration. The model
roles and the Vivado tool functions are replaced by fixed stand-ins, as in
tests/test_fsm_resume.py, so it needs no Vivado, no model login and no
network. Every LUT count and slack it prints is made up.

Use it to see what a run writes and where. Use `run.py optimize` for a real
measurement.
"""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from autortl import fsm, roles  # noqa: E402
from autortl.config import RunConfig  # noqa: E402
from autortl.report_parser import VivadoMetrics  # noqa: E402
from autortl.roles import Evaluation  # noqa: E402
from autortl.triage import FailureKind  # noqa: E402

DESIGN = ROOT / "curriculum" / "tier0" / "mux4"
BANNER = "SIMULATED WALKTHROUGH: no model, no Vivado. The numbers below are fixed stand-ins and measure nothing."
# The stand-in generator's candidate: the same mux written as a continuous select.
CANDIDATE = """`timescale 1ns/1ps
module mux4 (
    input  wire clk,
    input  wire rst,
    input  wire [7:0] a, b, c, d,
    input  wire [1:0] sel,
    output reg  [7:0] y
);
    wire [7:0] pick = sel[1] ? (sel[0] ? d : c) : (sel[0] ? b : a);
    always @(posedge clk) begin
        if (rst) y <= 8'd0;
        else y <= pick;
    end
endmodule
"""


def _receipts(work, tools):
    """Stand-in tool exit records. They are not evidence that any tool ran."""
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    with (work / "tool_exit_records.log").open("a", encoding="utf-8") as stream:
        for tool in tools:
            log = work / f"simulated_{tool}.log"
            log.write_text(f"simulated walkthrough: {tool} was not run\n", encoding="utf-8")
            stream.write(json.dumps({"schema_version": 1, "tool": tool, "executable": "simulated-demo/" + tool,
                                     "cwd": str(work.resolve()), "pid": 1, "status": "exited", "returncode": 0,
                                     "driver_returncode": 0, "elapsed_seconds": 0,
                                     "output_log_path": str(log.resolve()),
                                     "output_log_sha256": hashlib.sha256(log.read_bytes()).hexdigest()}) + "\n")


def _compile(files, cfg, work, **kwargs):
    _receipts(work, ("xvlog",))
    return True, "", FailureKind.DESIGN


def _simulate(files, tb, top, cfg, work, **kwargs):
    Path(work).mkdir(parents=True, exist_ok=True)
    (Path(work) / "sim_log.txt").write_text("TEST PASSED (simulated walkthrough)\n", encoding="utf-8")
    _receipts(work, ("xvlog", "xelab", "xsim"))
    return True, "", FailureKind.DESIGN


def _synthesize(files, top, cfg, work, **kwargs):
    (Path(work) / "utilization.rpt").write_text("simulated walkthrough: no synthesis was run\n", encoding="utf-8")
    _receipts(work, ("vivado",))
    return True, "", FailureKind.DESIGN


def _metrics(work):
    baseline = "iter_000" in str(work)
    return VivadoMetrics(sim_passed=True, lut_used=12 if baseline else 9, lut_total=20800,
                         ff_used=8, ff_total=41600, wns_ns=1.0, whs_ns=0.1, timing_met=True)


def _blocked(*args, **kwargs):
    raise RuntimeError("the simulated walkthrough never starts a process or opens a connection")


def install_models(orchestrator):
    """Replace each model role the optimize flow calls with a fixed answer."""
    answers = {("planner", "propose_contract"): "simulated contract",
               ("planner", "plan"): "## Instruction for generator\nWrite the select as one expression.",
               ("evaluator", "review_contract"): "ACCEPT",
               ("generator", "generate"): CANDIDATE,
               ("evaluator", "evaluate"): Evaluation("simulated walkthrough: fixed ACCEPT", "ACCEPT", 1, 0)}
    for (role, name), value in answers.items():
        def answer(*args, _value=value, **kwargs):
            orchestrator.budget.charge_llm()
            return _value
        setattr(getattr(orchestrator, role), name, answer)


@contextmanager
def stand_ins():
    """Swap the Vivado functions in, and block model calls, processes and sockets."""
    swaps = [(fsm.vivado, "xvlog_check", _compile), (fsm.vivado, "xsim_run", _simulate),
             (fsm.vivado, "run_synthesis", _synthesize), (fsm.vivado, "full_metrics", _metrics),
             (fsm.vivado, "vivado_seconds", lambda: 0), (roles, "ask", _blocked),
             (subprocess, "Popen", _blocked), (socket.socket, "connect", _blocked)]
    saved = [(owner, name, getattr(owner, name)) for owner, name, _ in swaps]
    try:
        for owner, name, value in swaps:
            setattr(owner, name, value)
        yield
    finally:
        for owner, name, value in saved:
            setattr(owner, name, value)


def run_demo(output_dir=None):
    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="autortl-demo-"))
    out = out.resolve()
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"{out} must be new or empty")
    cfg = RunConfig(mode="optimize", top_module="mux4", design_path=DESIGN / "mux4.v",
                    testbench_path=DESIGN / "mux4_tb.v", objective="minimize_luts",
                    max_iterations=1, best_of_n=1, vivado_bin="simulated-demo/vivado",
                    xvlog_bin="simulated-demo/xvlog", xelab_bin="simulated-demo/xelab",
                    xsim_bin="simulated-demo/xsim")
    with stand_ins():
        orchestrator = fsm.Orchestrator(cfg, out)
        install_models(orchestrator)
        summary = orchestrator.run()
    return out, summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output-dir", type=Path, help="new or empty folder (default: a fresh temp folder)")
    args = parser.parse_args(argv)
    print(BANNER, flush=True)
    out, summary = run_demo(args.output_dir)
    base, best = summary.get("baseline_metrics") or {}, summary.get("best_metrics") or {}
    print(f"status: {summary.get('status')}  best iteration: {summary.get('best_iteration')}  "
          f"simulated LUTs: {base.get('lut_used')} -> {best.get('lut_used')}")
    for label, path in (("run folder", out), ("journal", out / "journal"), ("events", out / "events.jsonl"),
                        ("progress", out / "progress.md"), ("summary", out / "run_summary.json"),
                        ("winner", out / "mux4_best.v")):
        print(f"{label:11} {path}")
    print(BANNER)
    return 0 if summary.get("status") == "done" else 1


if __name__ == "__main__":
    sys.exit(main())
