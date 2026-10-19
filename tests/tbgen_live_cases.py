"""Save deterministic generated-TB fixtures for an explicitly invoked live simulator run.

This file itself only writes inputs; it never launches a simulator or a model.
"""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from autortl.spec import ModuleSpec, Port
from autortl.tbgen import generate_fixed_latency_tb, generate_scoreboard_tb


def cases():
    stimulus = [{"a": a, "b": b} for a,b in [(0,0), (1,2), (255,1), (3,7), (8,4), (17,9), (10,22), (5,6)]]
    expected = [{"y": (r["a"]+r["b"]) & 255, "z": r["a"] ^ r["b"]} for r in stimulus]
    data = [Port("a", "input", 8), Port("b", "input", 8), Port("y", "output", 8), Port("z", "output", 8)]
    clock = [Port("clk", "input", 1), Port("rst", "input", 1)]
    result = []
    for latency in (0,1,3):
        name = f"latency{latency}"
        spec = ModuleSpec(name, "two-output arithmetic", ([] if latency == 0 else clock) + data, latency=latency)
        if latency == 0:
            source = f"module {name}(input [7:0] a,b, output [7:0] y,z); assign y=a+b; assign z=a^b; endmodule"
        else:
            source = f"""module {name}(input clk,rst, input [7:0] a,b, output [7:0] y,z);
reg [7:0] py[0:{latency-1}], pz[0:{latency-1}]; integer i;
assign y=py[{latency-1}]; assign z=pz[{latency-1}];
always @(posedge clk) begin
 if(rst) begin for(i=0;i<{latency};i=i+1) begin py[i]<=0; pz[i]<=0; end end
 else begin py[0]<=a+b; pz[0]<=a^b;
 for(i=1;i<{latency};i=i+1) begin py[i]<=py[i-1]; pz[i]<=pz[i-1]; end end
end endmodule"""
        tb = generate_fixed_latency_tb(spec, stimulus, expected)
        result.append((name, spec, source, tb, True))
        if latency == 3:
            result.append(("wrong_latency", spec, source.replace("assign y=py[2]", "assign y=py[1]"), tb, False))
    name = "stateful_counter"
    spec = ModuleSpec(name, "increment on enable", clock + [Port("en", "input", 1), Port("count", "output", 8)], latency=1)
    stim = [{"en": value} for value in (1,1,0,1,0,1)]
    count, exp = 0, []
    for row in stim:
        count += row["en"]
        exp.append({"count": count})
    source = f"module {name}(input clk,rst,en, output reg [7:0] count); always @(posedge clk) if(rst) count<=0; else if(en) count<=count+1; endmodule"
    result.append((name, spec, source, generate_fixed_latency_tb(spec, stim, exp), True))
    controls = [Port("in_valid", "input", 1, protocol="valid_ready"), Port("in_ready", "output", 1, protocol="valid_ready"),
                Port("out_valid", "output", 1, protocol="valid_ready"), Port("out_ready", "input", 1, protocol="valid_ready")]
    spec = ModuleSpec("stream_pair", "one elastic transaction", clock + data + controls, compare_mode="scoreboard")
    source = """module stream_pair(input clk,rst, input [7:0] a,b, input in_valid,out_ready,
output in_ready, output reg out_valid, output reg [7:0] y,z);
assign in_ready = !out_valid || out_ready;
always @(posedge clk) begin
 if(rst) begin out_valid<=0; y<=0; z<=0; end
 else if(in_ready) begin out_valid<=in_valid; if(in_valid) begin y<=a+b; z<=a^b; end end
end endmodule"""
    tb = generate_scoreboard_tb(spec, stimulus, expected)
    result += [("scoreboard_good", spec, source, tb, True),
               ("scoreboard_bad_second_port", spec, source.replace("z<=a^b", "z<=a+b"), tb, False),
               ("scoreboard_ignores_backpressure", spec, source.replace("else if(in_ready)", "else"), tb, False),
               ("scoreboard_never_valid", spec, source.replace("out_valid<=in_valid", "out_valid<=0"), tb, False)]
    return result


def save(directory):
    manifest = []
    for label, spec, source, tb, passed in cases():
        folder = directory / label
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "dut.v").write_text("`timescale 1ns/1ps\n" + source)
        (folder / "tb.v").write_text(tb)
        manifest.append({"case": label, "top": spec.name + "_tb", "expected_pass": passed})
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(save(parser.parse_args().output), indent=2))
