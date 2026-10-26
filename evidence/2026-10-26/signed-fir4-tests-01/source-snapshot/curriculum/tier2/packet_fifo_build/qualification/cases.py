"""Prepare packet FIFO admission inputs; never launch models or simulators."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = [(8, 3), (1, 1), (8, 2), (8, 4), (13, 5), (16, 8)]
DOMAIN = {"width_min": 1, "width_max": 16, "depth_min": 1, "depth_max": 8}

# Every edit requires exactly one original occurrence. These are intentionally
# behavioral defects with unchanged public interfaces and claimed latency.
MUTATIONS = {
    "hardcoded_depth_three": [
        ("assign in_ready = (used < DEPTH) || out_ready;",
         "assign in_ready = (used < 3) || out_ready;")],
    "payload_capture_truncated_eight": [
        # Keep the tuple's WIDTH-selected marker legal at every configuration;
        # force effective payload storage to eight bits rather than introducing
        # out-of-range tag selects that could fail compilation instead.
        ("memory[write_pointer] <= {in_last,in_data};",
         "memory[write_pointer] <= {in_last,in_data};\n                memory[write_pointer][WIDTH-1:0] <= in_data & 8'hff;")],
    "power_of_two_wrap": [
        ("if(write_pointer == DEPTH-1) write_pointer <= 0;",
         "if(write_pointer == (1 << $clog2(DEPTH))-1) write_pointer <= 0;"),
        ("if(read_pointer == DEPTH-1) read_pointer <= 0;",
         "if(read_pointer == (1 << $clog2(DEPTH))-1) read_pointer <= 0;")],
    "early_full": [
        ("assign in_ready = (used < DEPTH) || out_ready;",
         "assign in_ready = (used < DEPTH-1) || out_ready;")],
    "late_full": [
        ("assign in_ready = (used < DEPTH) || out_ready;",
         "assign in_ready = (used <= DEPTH) || out_ready;")],
    "full_simultaneous_blocked": [
        ("assign in_ready = (used < DEPTH) || out_ready;",
         "assign in_ready = (used < DEPTH);")],
    "simultaneous_occupancy_lost": [
        ("2'b11: used <= used;", "2'b11: used <= used - 1'b1;")],
    "simultaneous_retirement_lost": [
        ("if(pop) begin", "if(pop && !push) begin")],
    "output_truncated_eight": [
        ("assign out_data = memory[read_pointer][WIDTH-1:0];",
         "assign out_data = memory[read_pointer][WIDTH-1:0] & 8'hff;")],
    "unstable_stalled_payload": [
        ("assign out_data = memory[read_pointer][WIDTH-1:0];",
         "assign out_data = out_ready ? memory[read_pointer][WIDTH-1:0] : in_data;")],
    "incorrect_data_order": [
        ("assign out_data = memory[read_pointer][WIDTH-1:0];",
         "assign out_data = memory[write_pointer][WIDTH-1:0];")],
    "asynchronous_reset": [
        ("always @(posedge clk) begin", "always @(posedge clk or posedge rst) begin")],
    "last_stuck_zero": [
        ("assign out_last = memory[read_pointer][WIDTH];", "assign out_last = 1'b0;")],
    "last_stuck_one": [
        ("assign out_last = memory[read_pointer][WIDTH];", "assign out_last = 1'b1;")],
    "current_input_last_bypass": [
        ("assign out_last = memory[read_pointer][WIDTH];", "assign out_last = in_last;")],
    "unaccepted_tag_write": [
        ("if(push) begin", "if(in_valid && !in_ready) memory[write_pointer][WIDTH] <= in_last;\n            if(push) begin")],
    "displaced_tag_read": [
        ("assign out_last = memory[read_pointer][WIDTH];",
         "assign out_last = memory[write_pointer][WIDTH];")],
    "tag_only_stall_drift": [
        ("if(push) begin", "if(out_valid && !out_ready) memory[read_pointer][WIDTH] <= ~memory[read_pointer][WIDTH];\n            if(push) begin")],
}

MUTATION_NOTES = {
    "payload_capture_truncated_eight": (
        "Adapted from the hardcoded eight-bit memory fault: truncate captured payload "
        "to eight effective bits while retaining symbolic packed memory width and "
        "the marker bit. This does not change the declared physical memory width."
    ),
}

BYPASS = """`timescale 1ns/1ps
// @latency 1
// Intentionally false annotation: temporal assertions must establish behavior.
module packet_fifo_core #(parameter WIDTH=8, parameter DEPTH=3)(
    input clk, input rst, input [WIDTH-1:0] in_data, input in_last,
    input in_valid, output in_ready, output [WIDTH-1:0] out_data,
    output out_last, output out_valid, input out_ready);
    assign in_ready = out_ready && !rst;
    assign out_valid = in_valid && !rst;
    assign out_data = in_data;
    assign out_last = in_last;
endmodule
"""


def mutation_targets(reference):
    """Return complete exact edits, including the whole-source bypass edit."""
    return {**MUTATIONS, "combinational_bypass": [(reference, BYPASS)]}


def case_sources(reference=None):
    """Create unique sources, rejecting drift or ambiguity in any target."""
    if reference is None:
        reference = (ROOT / "qualification/reference.v").read_text(encoding="utf-8")
    result = {"reference": reference}
    for name, targets in mutation_targets(reference).items():
        source = reference
        for old, new in targets:
            if not old or old == new or reference.count(old) != 1 or source.count(old) != 1:
                raise ValueError("qualification target no longer unique: " + name)
            source = source.replace(old, new, 1)
        result[name] = source
    if len(set(result.values())) != len(result):
        raise ValueError("qualification source variants are not distinct")
    return result


def materialize_cases(output):
    """Write fresh complete inputs and exact byte hashes, not measured verdicts.

    Selected matrix configurations do not prove the complete declared domain.
    Every faulty case requires a real behavioral assertion, never a compile
    error, infrastructure failure or watchdog expiration.
    """
    from autortl.linter import top_verilog
    from autortl.spec import DesignSpec

    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    wrapper = top_verilog(DesignSpec.load(ROOT / "design_spec.json"))
    sources = case_sources()
    targets = mutation_targets(sources["reference"])
    manifest = {
        "schema_version": 1,
        "status": "prepared_not_simulated",
        "top": "packet_fifo_tb",
        "domain": DOMAIN,
        "matrix": [{"width": width, "depth": depth, "default_wrapper": index == 0}
                   for index, (width, depth) in enumerate(MATRIX)],
        "cases": [],
    }
    for name, source in sources.items():
        directory = output / name
        directory.mkdir()
        files = {
            "packet_fifo_core.v": source.encode("utf-8"),
            "packet_fifo.v": wrapper.encode("utf-8"),
            "packet_fifo_tb.v": (ROOT / "packet_fifo_tb.v").read_bytes(),
        }
        for filename, data in files.items():
            (directory / filename).write_bytes(data)
        manifest["cases"].append({
            "name": name,
            "expected_verdict": "TEST PASSED" if name == "reference" else "TEST FAILED",
            "required_failure_kind": None if name == "reference" else "behavioral_assertion",
            "mutation_note": MUTATION_NOTES.get(name),
            "mutation_targets": [{"original": old, "replacement": new, "original_occurrences": 1}
                                 for old, new in targets.get(name, [])],
            "files": [{"path": str((directory / filename).resolve()),
                       "sha256": hashlib.sha256(data).hexdigest()}
                      for filename, data in files.items()],
        })
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
