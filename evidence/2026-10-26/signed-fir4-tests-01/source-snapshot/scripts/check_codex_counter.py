"""Generate a small counter with Codex, then independently verify it with Vivado.

This is a bounded supervised generation trial, not the full optimization FSM.
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from autortl.budget import Budget
from autortl.config import RunConfig
from autortl.metrics_gate import validate
from autortl.spec import ModuleSpec, Port
from autortl.static_checks import check
from autortl.triage import FailureKind
from autortl import vivado
from llm import client

PROMPT = """Write synthesizable Verilog for exactly one module named counter8.
Ports: input clk, input rst, input enable, output reg [7:0] count.
At each rising clock edge: synchronous active-high rst sets count to zero;
otherwise if enable is one increment count modulo 256; otherwise hold count.
Reset has priority over enable. No initial blocks, extra ports, parameters,
testbench, files, or tools. Return the complete module in a verilog code fence.
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bin-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source", type=Path, help="Reverify saved RTL without another model call")
    parser.add_argument("--implementation-timeout", type=int, default=600)
    args = parser.parse_args()
    if args.implementation_timeout <= 0:
        parser.error("--implementation-timeout must be positive")
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    previous_stats = client._STATS_PATH
    client._STATS_PATH = out / "model_events.jsonl"
    result = {"passed": False, "stages": [],
              "kind": "supervised_reverification" if args.source else "supervised_generation"}

    def record(stage, passed, detail=""):
        event = {"stage": stage, "passed": passed, "detail": detail, "time": time.time()}
        result["stages"].append(event)
        with (out / "stages.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
        print(json.dumps(event), flush=True)

    def tool_call(function, *positional, **keywords):
        if budget.wall_minutes >= budget.max_wall_minutes or budget.vivado_seconds >= budget.max_vivado_minutes * 60:
            raise RuntimeError("Tool or wall-time budget exhausted")
        remaining = min((budget.max_wall_minutes - budget.wall_minutes) * 60,
                        budget.max_vivado_minutes * 60 - budget.vivado_seconds)
        if remaining <= 0:
            raise RuntimeError("Tool or wall-time budget exhausted")
        keywords["timeout"] = min(keywords.get("timeout", remaining), remaining)
        started = time.monotonic()
        try:
            return function(*positional, **keywords)
        finally:
            budget.charge_vivado(time.monotonic() - started)

    try:
        budget = Budget(1, 20, 25, out / "budget.json")
        cfg = RunConfig(mode="optimize", **{
            name + "_bin": str(args.bin_dir.resolve() / (name + ".bat"))
            for name in ("vivado", "xvlog", "xelab", "xsim")})
        result.update(part=cfg.target_part, period_ns=cfg.target_period_ns)
        (out / "prompt.txt").write_text(PROMPT, encoding="utf-8")
        if args.source:
            response = args.source.resolve().read_text(encoding="utf-8")
            result["imported_source"] = str(args.source.resolve())
        else:
            response = client.ask("generator", PROMPT, budget=budget)
        (out / "response.txt").write_text(response, encoding="utf-8")
        source = client.extract_verilog(response)
        # Consistent simulation units supplied by the harness, not model tools.
        if "`timescale" not in source:
            source = "`timescale 1ns/1ps\n" + source
        dut = out / "counter8.v"
        dut.write_text(source, encoding="utf-8")
        tb = out / "counter8_tb.v"
        tb.write_bytes((ROOT / "tests/fixtures/counter8_tb.v").read_bytes())
        result["source_sha256"] = hashlib.sha256(dut.read_bytes()).hexdigest()
        result["testbench_sha256"] = hashlib.sha256(tb.read_bytes()).hexdigest()
        record("source_import" if args.source else "generation", True)
        spec = ModuleSpec("counter8", "8-bit enabled synchronous counter", [
            Port("clk", "input", 1), Port("rst", "input", 1),
            Port("enable", "input", 1), Port("count", "output", 8)])
        static = check(source, spec)
        record("static", static.passed, static.errors)
        if not static.passed:
            return 1
        sim = out / "simulation"
        sim.mkdir()
        passed, err, kind = tool_call(vivado.xsim_run, [dut], tb, "counter8_tb", cfg, sim, timeout=60)
        record("simulation", passed, {"error": err, "failure_kind": kind.value})
        if not passed:
            return 1
        mutant = out / "mutation"
        mutant.mkdir()
        bad = mutant / "counter8.v"
        bad.write_text("`timescale 1ns/1ps\nmodule counter8(input clk,rst,enable, output [7:0] count); assign count=8'b0; endmodule")
        passed, err, kind = tool_call(vivado.xsim_run, [bad], tb, "counter8_tb", cfg, mutant, timeout=60)
        qualified = not passed and kind == FailureKind.DESIGN and err.startswith("Testbench failures:")
        record("mutation_detection", qualified, err)
        if not qualified:
            return 1
        async_dir = out / "async_reset_mutation"
        async_dir.mkdir()
        async_bad = async_dir / "counter8.v"
        async_bad.write_text("`timescale 1ns/1ps\nmodule counter8(input clk,rst,enable, output reg [7:0] count); always @(posedge clk or posedge rst) if(rst) count<=0; else if(enable) count<=count+1; endmodule")
        passed, err, kind = tool_call(vivado.xsim_run, [async_bad], tb, "counter8_tb", cfg, async_dir, timeout=60)
        qualified = not passed and kind == FailureKind.DESIGN and err.startswith("Testbench failures:")
        record("async_reset_detection", qualified, err)
        if not qualified:
            return 1
        impl = out / "implementation"
        impl.mkdir()
        passed, err, kind = tool_call(vivado.run_synthesis, [dut], "counter8", cfg, impl,
                                     timeout=args.implementation_timeout)
        record("implementation", passed, {"error": err, "failure_kind": kind.value})
        if not passed:
            return 1
        metrics = vivado.full_metrics(impl)
        metrics.sim_passed, metrics.sim_error = True, ""
        validate(metrics, synthesis_ran=True)
        result["metrics"] = metrics.to_dict()
        record("metrics", True)
        record("timing", metrics.timing_met)
        if not metrics.timing_met:
            return 1
        result["passed"] = True
        return 0
    except Exception as exc:
        record("exception", False, {"type": type(exc).__name__, "error": str(exc)[:1000]})
        return 1
    finally:
        client._STATS_PATH = previous_stats
        (out / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
