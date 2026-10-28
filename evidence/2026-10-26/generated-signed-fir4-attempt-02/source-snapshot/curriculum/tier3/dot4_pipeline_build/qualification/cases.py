"""Prepare controls and intended behavioral mutants. Does not execute tools."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Each old fragment must occur exactly once; replacements preserve compilable
# interfaces by construction. Only a real simulator run can establish admission.
MUTATIONS = {
    "drop_product": ("children", [("else pair01_sum <= {1'b0,product0} + {1'b0,product1};", "else pair01_sum <= {1'b0,product0};")]),
    "truncate_pair_carry": ("children", [("else pair01_sum <= {1'b0,product0} + {1'b0,product1};", "else pair01_sum <= ({1'b0,product0} + {1'b0,product1}) & 17'h0ffff;")]),
    "truncate_final_carry": ("children", [("else dot_result <= {1'b0,left_sum} + {1'b0,right_sum};", "else dot_result <= ({1'b0,left_sum} + {1'b0,right_sum}) & 18'h1ffff;")]),
    "signed_operands": ("children", [("wire [15:0] product0 = a0 * b0;", "wire [15:0] product0 = $signed(a0) * $signed(b0);")]),
    "duplicate_first_input_pair": ("wrapper", [(".a2(a2)", ".a2(a0)"), (".b2(b2)", ".b2(b0)"), (".a3(a3)", ".a3(a1)"), (".b3(b3)", ".b3(b1)")]),
    "duplicate_partial_sum": ("children", [("else dot_result <= {1'b0,left_sum} + {1'b0,right_sum};", "else dot_result <= {1'b0,left_sum} + {1'b0,left_sum};")]),
    "combinational_merge": ("children", [("always @(posedge clk) begin // merge_clock", "always @* begin // merge_clock")]),
    "extra_merge_stage": ("children", [
        ("always @(posedge clk) begin // merge_clock", "reg [17:0] delayed_sum;\n    always @(posedge clk) begin // merge_clock"),
        ("if(rst) dot_result <= 0;\n        else dot_result <= {1'b0,left_sum} + {1'b0,right_sum};",
         "if(rst) begin dot_result <= 0; delayed_sum <= 0; end\n        else begin delayed_sum <= {1'b0,left_sum} + {1'b0,right_sum}; dot_result <= delayed_sum; end")]),
    "branch_cycle_misalignment": ("children", [
        ("wire [15:0] product2 = a2 * b2;", "reg [16:0] delayed_pair;\n    wire [15:0] product2 = a2 * b2;"),
        ("if(rst) pair23_sum <= 0;\n        else pair23_sum <= {1'b0,product2} + {1'b0,product3};",
         "if(rst) begin pair23_sum <= 0; delayed_pair <= 0; end\n        else begin delayed_pair <= {1'b0,product2} + {1'b0,product3}; pair23_sum <= delayed_pair; end")]),
    "asynchronous_pair_reset": ("children", [("always @(posedge clk) begin // pair01_clock", "always @(posedge clk or posedge rst) begin // pair01_clock")]),
    "merge_reset_ignored": ("children", [("if(rst) dot_result <= 0;", "if(rst) dot_result <= dot_result;")]),
    "interedge_input_leak": ("wrapper", [
        ("    dot4_merge u_dot4_merge (", "    wire [17:0] registered_result;\n    assign dot_result = registered_result ^ {17'b0,a0[0]};\n    dot4_merge u_dot4_merge ("),
        (".dot_result(dot_result)", ".dot_result(registered_result)")]),
}

def case_sources():
    from autortl.linter import top_verilog
    from autortl.spec import DesignSpec
    reference = (ROOT / "qualification/reference.v").read_text(encoding="utf-8")
    wrapper = top_verilog(DesignSpec.load(ROOT / "design_spec.json"))
    control = {"children": reference, "wrapper": wrapper}
    result = {"reference": control}
    for name, (target, edits) in MUTATIONS.items():
        variant = dict(control)
        for old, new in edits:
            if variant[target].count(old) != 1:
                raise ValueError("nonunique mutation target: " + name)
            variant[target] = variant[target].replace(old, new, 1)
        result[name] = variant
    identities = {(entry["children"], entry["wrapper"]) for entry in result.values()}
    if len(identities) != len(result):
        raise ValueError("duplicate qualification variants")
    return result

def materialize_cases(output):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    manifest = {"schema_version": 1, "status": "prepared_not_simulated",
                "top": "dot4_pipeline_tb", "cases": []}
    tb = (ROOT / "dot4_pipeline_tb.v").read_bytes()
    for name, sources in case_sources().items():
        directory = output / name
        directory.mkdir()
        files = {"children.v": sources["children"].encode("utf-8"),
                 "dot4_pipeline.v": sources["wrapper"].encode("utf-8"),
                 "dot4_pipeline_tb.v": tb}
        for filename, data in files.items():
            (directory / filename).write_bytes(data)
        manifest["cases"].append({
            "name": name, "expected_verdict": "TEST PASSED" if name == "reference" else "TEST FAILED",
            "required_failure_kind": None if name == "reference" else "behavioral_assertion",
            "mutation_targets": [{"file": MUTATIONS[name][0], "original": old, "replacement": new,
                                  "original_occurrences": 1} for old, new in MUTATIONS.get(name, ("", []))[1]],
            "files": [{"path": str(directory / filename), "sha256": hashlib.sha256(data).hexdigest()}
                      for filename, data in files.items()]})
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    return manifest
