"""Prepare qualification-only RTL cases; never invoke models or simulators."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MUTATIONS = {
    "capacity_one": ("(used != 2) || out_ready", "(used == 0) || out_ready"),
    "overrun_ready": ("(used != 2) || out_ready", "1'b1"),
    "payload_corruption": ("assign out_data = storage[read_pointer];", "assign out_data = storage[read_pointer] ^ 8'h01;"),
    "unstable_stall": ("assign out_data = storage[read_pointer];", "assign out_data = out_ready ? storage[read_pointer] : in_data;"),
    "drop_valid_stall": ("assign out_valid = (used != 0);", "assign out_valid = (used != 0) && out_ready;"),
    "async_reset": ("always @(posedge clk) begin", "always @(posedge clk or posedge rst) begin"),
    "simultaneous_pop_lost": ("if (pop) read_pointer <= !read_pointer;", "if (pop && !push) read_pointer <= !read_pointer;"),
}


def case_sources():
    reference = (ROOT / "qualification/reference.v").read_text(encoding="utf-8")
    result = {"reference": reference}
    for name, (old, new) in MUTATIONS.items():
        if reference.count(old) != 1:
            raise ValueError("mutation target no longer unique: " + name)
        result[name] = reference.replace(old, new, 1)
    # Intentionally false annotation: matching a comment is not cycle proof.
    result["combinational_passthrough"] = """`timescale 1ns/1ps
// @latency 1
module skid_buffer_core(input clk,input rst,input [7:0] in_data,
    input in_valid,output in_ready,output [7:0] out_data,
    output out_valid,input out_ready);
    assign out_valid = in_valid && !rst;
    assign in_ready = out_ready && !rst;
    assign out_data = in_data;
endmodule
"""
    return result


def materialize_cases(output):
    """Create a fresh case directory, exact TB copies and a full-byte manifest.

    Expected verdicts are a qualification plan, not measured results. A mutant
    only counts as killed after a behavioral assertion failure in a real sim.
    """
    from autortl.linter import top_verilog
    from autortl.spec import DesignSpec
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    spec = DesignSpec.load(ROOT / "design_spec.json")
    wrapper = top_verilog(spec)
    manifest = {"schema_version": 1, "status": "prepared_not_simulated", "cases": []}
    for name, source in case_sources().items():
        directory = output / name
        directory.mkdir()
        files = {"skid_buffer_core.v": source.encode("utf-8"),
                 "skid_buffer.v": wrapper.encode("utf-8"),
                 "skid_buffer_tb.v": (ROOT / "skid_buffer_tb.v").read_bytes()}
        for filename, data in files.items():
            (directory / filename).write_bytes(data)
        manifest["cases"].append({"name": name, "expected_verdict": "TEST PASSED" if name == "reference" else "TEST FAILED",
            "required_failure_kind": None if name == "reference" else "behavioral_assertion",
            "files": [{"path": str((directory / filename).resolve()), "sha256": hashlib.sha256(data).hexdigest()}
                      for filename, data in files.items()]})
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
