"""Materialize elastic-dot4 checker controls/faults; never launch tools."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MUTATIONS={
    "dropped_product":[("partial01<={1'b0,product0}+{1'b0,product1};","partial01<={1'b0,product0};")],
    "signed_arithmetic":[("wire [15:0] product0=a0*b0;","wire [15:0] product0=$signed(a0)*$signed(b0);")],
    "pair_carry_truncation":[("partial01<={1'b0,product0}+{1'b0,product1};","partial01<=({1'b0,product0}+{1'b0,product1}) & 17'h0ffff;")],
    "final_carry_truncation":[("if(v1) result<={1'b0,partial01}+{1'b0,partial23};","if(v1) result<=({1'b0,partial01}+{1'b0,partial23}) & 18'h1ffff;")],
    "early_output":[("assign out_valid=v2;","assign out_valid=v2 || v1;")],
    "late_output":[
        ("reg v1,v2;","reg v1,v2;\n    reg delayed_valid;\n    always @(posedge clk) begin\n        if(rst) delayed_valid<=0; else delayed_valid<=v2;\n    end"),
        ("assign out_valid=v2;","assign out_valid=delayed_valid;")],
    "accept_full":[("assign in_ready=!v1 || ready2;","assign in_ready=1'b1;")],
    "overwrite_blocked_stage1":[("if(in_ready) begin // capture_gate","if(in_ready || in_valid) begin // capture_gate")],
    "drop_blocked_stage1":[("end // capture_end","end else v1<=0; // capture_end")],
    "clear_stalled_valid":[("end // normal_end","if(!ready2) v2<=0;\n        end // normal_end")],
    "corrupt_held_output":[("end // normal_end","if(!ready2) result<=result ^ 18'd1;\n        end // normal_end")],
    "duplicate_retirement":[("v2<=v1; // advance_valid","v2<=v1 || v2; // advance_valid")],
    "lose_full_replacement":[("v1<=in_valid; // capture_valid","v1<=in_valid && !v2; // capture_valid")],
    "throughput_bubble":[("assign in_ready=!v1 || ready2;","assign in_ready=!v1 || (ready2 && !v2);")],
    "retained_stage1_reset":[("v1<=0; // reset_stage1","if(v1) v1<=v1; else v1<=0; // reset_stage1")],
    "retained_stage2_reset":[("v2<=0; // reset_stage2","if(v2) v2<=v2; else v2<=0; // reset_stage2")],
    "asynchronous_reset":[("always @(posedge clk) begin","always @(posedge clk or posedge rst) begin")],
    "incorrect_downstream_ready":[("wire ready2=!v2 || out_ready;","wire ready2=!v2 || in_valid;")],
}

def case_sources():
    reference=(ROOT/"qualification/reference.v").read_text(encoding="utf-8")
    cases={"reference":reference}
    for name,edits in MUTATIONS.items():
        source=reference
        for old,new in edits:
            if source.count(old)!=1:
                raise ValueError("nonunique mutation target: "+name)
            source=source.replace(old,new,1)
        cases[name]=source
    if len(set(cases.values()))!=len(cases):
        raise ValueError("duplicate source variants")
    return cases

def materialize_cases(output):
    from autortl.linter import top_verilog
    from autortl.spec import DesignSpec
    output=Path(output).resolve()
    output.mkdir(parents=True,exist_ok=False)
    wrapper=top_verilog(DesignSpec.load(ROOT/"design_spec.json"))
    tb=(ROOT/"elastic_dot4_tb.v").read_bytes()
    manifest={"schema_version":1,"status":"prepared_not_simulated",
              "top":"elastic_dot4_tb","cases":[]}
    for name,source in case_sources().items():
        directory=output/name
        directory.mkdir()
        files={"children.v":source.encode("utf-8"),
               "elastic_dot4.v":wrapper.encode("utf-8"),"elastic_dot4_tb.v":tb}
        for filename,data in files.items():
            (directory/filename).write_bytes(data)
        manifest["cases"].append({
            "name":name,"expected_verdict":"TEST PASSED" if name=="reference" else "TEST FAILED",
            "required_failure_kind":None if name=="reference" else "behavioral_assertion",
            "mutation_targets":[{"original":old,"replacement":new,"original_occurrences":1}
                                for old,new in MUTATIONS.get(name,[])],
            "files":[{"path":str(directory/filename),"sha256":hashlib.sha256(data).hexdigest()}
                     for filename,data in files.items()]})
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    return manifest
