"""Qualify trusted build testbenches against supervised RTL controls and faults.

These references are independent qualification artifacts, never generated winners.
Run serially through the coordinator's Vivado queue in a fresh output directory.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from autortl.config import RunConfig
from autortl.state import atomic_write_text
from autortl.triage import FailureKind
from autortl.vivado import xsim_run

COUNTER = """`timescale 1ns/1ps
module counter8(input clk, rst, enable, output reg [7:0] count);
always @(posedge clk) begin
    if (rst) count <= 0;
    else if (enable) count <= count + 1'b1;
end
endmodule
"""
ENCODER = """`timescale 1ns/1ps
module priority_encoder8(input clk, rst, input [7:0] request,
                         output reg [2:0] index, output reg valid);
integer bit_number;
reg [2:0] selected;
always @(*) begin
    selected = 0;
    for (bit_number=0; bit_number<8; bit_number=bit_number+1)
        if (request[bit_number]) selected = bit_number;
end
always @(posedge clk) begin
    if (rst) begin index <= 0; valid <= 0; end
    else begin index <= selected; valid <= (request != 0); end
end
endmodule
"""


def cases():
    """Return controls and independently meaningful, compiling behavior mutations."""
    counter_delay = """`timescale 1ns/1ps
module counter8(input clk,rst,enable,output reg [7:0] count);
reg [7:0] state;
always @(posedge clk) begin
    if (rst) begin state<=0; count<=0; end
    else begin
        if (enable) state<=state+1'b1;
        count<=state;
    end
end
endmodule
"""
    encoder_delay = ENCODER.replace("integer bit_number;", "reg [2:0] prior_index; reg prior_valid; integer bit_number;").replace(
        "if (rst) begin index <= 0; valid <= 0; end",
        "if (rst) begin index<=0; valid<=0; prior_index<=0; prior_valid<=0; end").replace(
        "else begin index <= selected; valid <= (request != 0); end",
        "else begin prior_index<=selected; prior_valid<=(request!=0); index<=prior_index; valid<=prior_valid; end")
    rows = [
        ("counter-control", "counter8", COUNTER, True, "supervised modulo counter reference"),
        ("counter-saturation", "counter8", COUNTER.replace("count + 1'b1", "(count == 8'hff) ? count : count + 1'b1"), False, "saturates instead of wrapping"),
        ("counter-disabled-hold", "counter8", COUNTER.replace("else if (enable)", "else"), False, "increments while disabled"),
        ("counter-async-reset", "counter8", COUNTER.replace("@(posedge clk)", "@(posedge clk or posedge rst)"), False, "reset changes outputs between clock edges"),
        ("counter-extra-cycle", "counter8", counter_delay, False, "adds one observable output cycle"),
        ("encoder-control", "priority_encoder8", ENCODER, True, "supervised highest-bit priority reference"),
        ("encoder-wrong-priority", "priority_encoder8", ENCODER.replace("bit_number=0; bit_number<8; bit_number=bit_number+1", "bit_number=7; bit_number>=0; bit_number=bit_number-1"), False, "lowest set bit wins"),
        ("encoder-valid", "priority_encoder8", ENCODER.replace("valid <= (request != 0)", "valid <= 1'b1"), False, "valid asserted for zero request"),
        ("encoder-combinational", "priority_encoder8", ENCODER.replace("always @(posedge clk)", "always @(*)"), False, "outputs respond before active clock edge"),
        ("encoder-extra-cycle", "priority_encoder8", encoder_delay, False, "adds one observable output cycle"),
    ]
    return [{"case":name,"module":module,"top":module+"_tb","source":source,
             "expected_pass":expected,"mutation":reason} for name,module,source,expected,reason in rows]


def verdict(expected_pass, passed, error, kind, raw_log=None):
    text = raw_log if isinstance(raw_log, str) else ""
    watchdog = re.search(r"watchdog|timed?\s*out|timeout", text, re.IGNORECASE) is not None
    assertion = re.search(r"^\s*FAIL\b", text, re.MULTILINE) is not None
    pass_marker = re.search(r"^\s*TEST PASSED\s*$", text, re.MULTILINE) is not None
    fail_marker = re.search(r"^\s*TEST FAILED(?:\s*:[^\n]*)?\s*$", text, re.MULTILINE) is not None
    detected = (passed is False and kind == FailureKind.DESIGN and assertion and fail_marker and not pass_marker and not watchdog and
                (error.startswith("Testbench failures:") or error == "testbench reported failure"))
    control_pass = passed is True and pass_marker and not fail_marker and not assertion and not watchdog
    return {"ok": bool(control_pass) if expected_pass else detected,
            "assertion_detected": detected, "watchdog_or_timeout": watchdog}


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_cases(output):
    prepared = []
    for case in cases():
        work=output/case["case"]
        work.mkdir()
        (work/"dut.v").write_text(case["source"],encoding="utf-8")
        entry="counter8_build" if case["module"]=="counter8" else "encoder8_build"
        original=ROOT/"curriculum"/"tier1"/entry/(case["top"]+".v")
        (work/"tb.v").write_bytes(original.read_bytes())
        prepared.append({k:v for k,v in case.items() if k!="source"} | {
            "source_sha256":_sha(work/"dut.v"),"tb_sha256":_sha(work/"tb.v"),
            "trusted_tb_path":str(original.resolve())})
    atomic_write_text(output/"cases.json",json.dumps(prepared,indent=2))
    return prepared


def _save_materialized_cases(output, suite, module, materialize):
    case_root = suite + "_cases"
    plan = materialize(output / case_root)
    prepared = []
    for case in plan["cases"]:
        work = output / case_root / case["name"]
        source_files = [work / (module + "_core.v"), work / (module + ".v")]
        testbench = module + "_tb.v"
        prepared.append({"case": case["name"], "module": module, "top": module + "_tb",
                         "expected_pass": case["expected_verdict"] == "TEST PASSED",
                         "work_dir": case_root + "/" + case["name"],
                         "design_files": [p.name for p in source_files],
                         "testbench": testbench,
                         "source_sha256": {p.name: _sha(p) for p in source_files},
                         "tb_sha256": _sha(work / testbench),
                         "planned_files": case["files"],
                         "required_failure_kind": case["required_failure_kind"]})
    atomic_write_text(output / "cases.json", json.dumps(prepared, indent=2))
    return prepared


def save_skid_cases(output):
    from curriculum.tier2.skid_buffer_build.qualification.cases import materialize_cases
    return _save_materialized_cases(output, "skid", "skid_buffer", materialize_cases)


def save_fifo_cases(output):
    from curriculum.tier2.sync_fifo_build.qualification.cases import materialize_cases
    return _save_materialized_cases(output, "fifo", "sync_fifo", materialize_cases)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bin-dir",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--suite", choices=("build", "skid", "fifo"), default="build")
    args=parser.parse_args(argv)
    output=args.output.resolve()
    output.mkdir(parents=True,exist_ok=False)
    config=RunConfig(mode="optimize",**{name+"_bin":str(args.bin_dir.resolve()/(name+".bat"))
                                    for name in ("vivado","xvlog","xelab","xsim")})
    results=[]
    prepare = {"build": save_cases, "skid": save_skid_cases, "fifo": save_fifo_cases}[args.suite]
    prepared = prepare(output)
    for case in prepared:
        work=output/case.get("work_dir", case["case"])
        started=time.monotonic()
        sources = [work / name for name in case.get("design_files", ["dut.v"])]
        tb = work / case.get("testbench", "tb.v")
        passed,error,kind=xsim_run(sources,tb,case["top"],config,work,timeout=60)
        log=work/"sim_log.txt"
        raw_log=log.read_text(encoding="utf-8",errors="replace") if log.is_file() else None
        record=case|verdict(case["expected_pass"],passed,error,kind,raw_log)|{
            "passed":passed,"error":error,"failure_kind":kind.value,
            "seconds":time.monotonic()-started}
        results.append(record)
        atomic_write_text(output/"results.json",json.dumps(results,indent=2))
        print(json.dumps(record),flush=True)
    # Exact raw bytes, including actual process receipts, remain independently auditable.
    manifest={p.relative_to(output).as_posix():_sha(p) for p in sorted(output.rglob("*"))
              if p.is_file() and (p.suffix in (".v",".log",".txt",".json"))}
    atomic_write_text(output/"archive-manifest.json",json.dumps(manifest,indent=2))
    return 0 if results and all(row["ok"] for row in results) else 1


if __name__=="__main__":
    raise SystemExit(main())
