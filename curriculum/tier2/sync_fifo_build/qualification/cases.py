"""Materialize FIFO qualification inputs only; no simulator or model launches."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = [(8,3),(1,1),(8,2),(8,4),(13,5),(16,8)]
DOMAIN = {"width_min":1,"width_max":16,"depth_min":1,"depth_max":8}
# Each exact target must occur once. Multi-edit faults list distinct targets.
MUTATIONS = {
    "hardcoded_depth_three": [("assign in_ready = (used < DEPTH) || out_ready;", "assign in_ready = (used < 3) || out_ready;")],
    "hardcoded_memory_width_eight": [("reg [WIDTH-1:0] memory [0:DEPTH-1];", "reg [7:0] memory [0:DEPTH-1];")],
    "power_of_two_wrap": [
        ("if(write_pointer == DEPTH-1) write_pointer <= 0;", "if(write_pointer == (1 << $clog2(DEPTH))-1) write_pointer <= 0;"),
        ("if(read_pointer == DEPTH-1) read_pointer <= 0;", "if(read_pointer == (1 << $clog2(DEPTH))-1) read_pointer <= 0;")],
    "early_full": [("assign in_ready = (used < DEPTH) || out_ready;", "assign in_ready = (used < DEPTH-1) || out_ready;")],
    "late_full": [("assign in_ready = (used < DEPTH) || out_ready;", "assign in_ready = (used <= DEPTH) || out_ready;")],
    "full_simultaneous_blocked": [("assign in_ready = (used < DEPTH) || out_ready;", "assign in_ready = (used < DEPTH);")],
    "simultaneous_occupancy_lost": [("2'b11: used <= used;", "2'b11: used <= used - 1'b1;")],
    "simultaneous_retirement_lost": [("if(pop) begin", "if(pop && !push) begin")],
    "output_truncated_eight": [("assign out_data = memory[read_pointer];", "assign out_data = memory[read_pointer] & 8'hff;")],
    "unstable_stalled_payload": [("assign out_data = memory[read_pointer];", "assign out_data = out_ready ? memory[read_pointer] : in_data;")],
    "incorrect_data_order": [("assign out_data = memory[read_pointer];", "assign out_data = memory[write_pointer];")],
    "asynchronous_reset": [("always @(posedge clk) begin", "always @(posedge clk or posedge rst) begin")],
}


def case_sources():
    reference = (ROOT / "qualification/reference.v").read_text(encoding="utf-8")
    result = {"reference": reference}
    for name, targets in MUTATIONS.items():
        source = reference
        for old, new in targets:
            if reference.count(old) != 1 or source.count(old) != 1:
                raise ValueError("qualification target no longer unique: " + name)
            source = source.replace(old, new, 1)
        result[name] = source
    result["combinational_bypass"] = """`timescale 1ns/1ps
// @latency 1
// Intentionally false annotation: only actual temporal checks establish behavior.
module sync_fifo_core #(parameter WIDTH=8, parameter DEPTH=3)(
    input clk, input rst, input [WIDTH-1:0] in_data,
    input in_valid, output in_ready, output [WIDTH-1:0] out_data,
    output out_valid, input out_ready);
    assign in_ready = out_ready && !rst;
    assign out_valid = in_valid && !rst;
    assign out_data = in_data;
endmodule
"""
    if len(set(result.values())) != len(result):
        raise ValueError("qualification source variants are not distinct")
    return result


def materialize_cases(output):
    """Create fresh complete case inputs and exact raw-byte SHA-256 identities.

    The matrix checks selected configurations, not every supported combination.
    Expected verdicts are admission requirements, never measured results.
    """
    from autortl.linter import top_verilog
    from autortl.spec import DesignSpec
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    wrapper = top_verilog(DesignSpec.load(ROOT / "design_spec.json"))
    manifest = {"schema_version":1,"status":"prepared_not_simulated", "top":"sync_fifo_tb",
                "domain":DOMAIN,"matrix":[{"width":w,"depth":d,"default_wrapper":i==0} for i,(w,d) in enumerate(MATRIX)],"cases":[]}
    for name, source in case_sources().items():
        directory = output / name
        directory.mkdir()
        files = {"sync_fifo_core.v":source.encode("utf-8"),"sync_fifo.v":wrapper.encode("utf-8"),
                 "sync_fifo_tb.v":(ROOT / "sync_fifo_tb.v").read_bytes()}
        for filename, data in files.items():
            (directory / filename).write_bytes(data)
        targets = MUTATIONS.get(name, [])
        manifest["cases"].append({"name":name,"expected_verdict":"TEST PASSED" if name=="reference" else "TEST FAILED",
            "required_failure_kind":None if name=="reference" else "behavioral_assertion",
            "mutation_targets":[{"original":old,"replacement":new,"original_occurrences":1} for old,new in targets],
            "files":[{"path":str((directory / filename).resolve()),"sha256":hashlib.sha256(data).hexdigest()} for filename,data in files.items()]})
    (output / "manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    return manifest
