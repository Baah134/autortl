"""Prepare independent checker admission cases; never invoke tools."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MUTATIONS={'current_coefficient': [("13'sd3*sx", "13'sd2*sx")],
 'history_coefficient': [("13'sd5*sh1", "13'sd4*sh1")],
 'swapped_taps': [("13'sd5*sh1", "13'sd5*sh2"), ("13'sd7*sh2", "13'sd7*sh1")],
 'unsigned_input': [('{{5{x[7]}},x}', "{5'b0,x}")],
 'unsigned_history': [('{{5{h1[7]}},h1}', "{5'b0,h1}"),
                      ('{{5{h2[7]}},h2}', "{5'b0,h2}"),
                      ('{{5{h3[7]}},h3}', "{5'b0,h3}")],
 'truncate12': [('result<=combined;', 'result<={combined[11],combined[11:0]};')],
 'history_on_invalid': [('else if(in_valid && in_ready) begin // history_gate',
                         'else if(in_ready) begin // history_gate')],
 'history_on_blocked': [('else if(in_valid && in_ready) begin // history_gate',
                         'else if(in_valid) begin // history_gate')],
 'history_delay': [('reg signed [7:0] h1,h2,h3;', 'reg signed [7:0] h1,h2,h3; reg signed [7:0] delayed_x;'),
                   ('h1<=0;h2<=0;h3<=0; // history_reset', 'h1<=0;h2<=0;h3<=0; delayed_x<=0; // history_reset'),
                   ('h3<=h2;h2<=h1;h1<=x; // history_shift',
                    'h3<=h2;h2<=h1;h1<=delayed_x;delayed_x<=x; // history_shift')],
 'reverse_history_shift': [('h3<=h2;h2<=h1;h1<=x;', 'h3<=x;h2<=h3;h1<=h2;')],
 'stale_history_reset': [('h1<=0;h2<=0;h3<=0; // history_reset',
                          'if(h1) h1<=h1; else h1<=0; if(h2) h2<=h2; else h2<=0; if(h3) h3<=h3; else h3<=0; // '
                          'history_reset')],
 'async_history_reset': [('always @(posedge clk) begin // history_clock',
                          'always @(posedge clk or posedge rst) begin // history_clock')],
 'early_output': [('assign out_valid=v3;', 'assign out_valid=v3 || v2;')],
 'late_output': [('reg v1,v2,v3;',
                  'reg v1,v2,v3; reg delayed_valid; always @(posedge clk) begin if(rst) delayed_valid<=0; else '
                  'delayed_valid<=v3; end'),
                 ('assign out_valid=v3;', 'assign out_valid=delayed_valid;')],
 'accept_full': [('assign in_ready=r1;', "assign in_ready=1'b1;")],
 'overwrite_stage1': [('if(in_ready) begin // stage1_gate', 'if(in_ready || in_valid) begin // stage1_gate')],
 'overwrite_stage2': [('if(r2) begin // stage2_gate', 'if(r2 || v1) begin // stage2_gate')],
 'clear_stalled_valid': [('end // pipeline_normal', 'if(!r3) v3<=0; end // pipeline_normal')],
 'corrupt_held_output': [('end // pipeline_normal', "if(!r3) result<=result ^ 13'd1; end // pipeline_normal")],
 'lose_full_replacement': [('v1<=in_valid; // input_valid', 'v1<=in_valid && !v3; // input_valid')],
 'throughput_bubble': [('wire r1=!v1 || r2;', 'wire r1=!v1 || (r2 && !v3);')],
 'retained_stage1_reset': [('v1<=0; // reset_v1', 'if(v1) v1<=v1; else v1<=0; // reset_v1')],
 'retained_stage2_reset': [('v2<=0; // reset_v2', 'if(v2) v2<=v2; else v2<=0; // reset_v2')],
 'retained_stage3_reset': [('v3<=0; // reset_v3', 'if(v3) v3<=v3; else v3<=0; // reset_v3')],
 'async_valid_reset': [('always @(posedge clk) begin // pipeline_clock',
                        'always @(posedge clk or posedge rst) begin // pipeline_clock')],
 'incorrect_downstream_ready': [('wire r3=!v3 || out_ready;', 'wire r3=!v3 || in_valid;')],
 'combinational_reset_gate': [('assign out_valid=v3;', 'assign out_valid=v3 && !rst;')]}

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
    tb=(ROOT/"signed_fir4_tb.v").read_bytes()
    manifest={"schema_version":1,"status":"prepared_not_simulated",
              "top":"signed_fir4_tb","cases":[]}
    for name,source in case_sources().items():
        directory=output/name
        directory.mkdir()
        files={"children.v":source.encode("utf-8"),
               "signed_fir4.v":wrapper.encode("utf-8"),"signed_fir4_tb.v":tb}
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
