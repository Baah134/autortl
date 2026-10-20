import sys,json,hashlib,argparse
from pathlib import Path
ROOT=Path("C:/Users/prince.baah/Downloads/autortl-work")
sys.path.insert(0,str(ROOT))
from tests.tbgen_live_cases import cases
from autortl.tbgen import generate_scoreboard_tb
from autortl.config import RunConfig
from autortl.vivado import xsim_run
p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);a=p.parse_args()
out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
_,spec,good,_,_=next(row for row in cases() if row[0]=="scoreboard_good")
spec.latency=1
stim=[{"a":i,"b":i+1} for i in range(8)]
exp=[{"y":row["a"]+row["b"],"z":row["a"]^row["b"]} for row in stim]
tb=generate_scoreboard_tb(spec,stim,exp)
bad="""module stream_pair(input clk,rst,input [7:0] a,b,input in_valid,out_ready,
output in_ready,out_valid,output [7:0] y,z);
assign in_ready=out_ready && !rst;
assign out_valid=in_valid && !rst;
assign y=a+b; assign z=a^b; endmodule
"""
cfg=RunConfig(mode="optimize",**{name+"_bin":"C:/AMDDesignTools/2025.2/Vivado/bin/"+name+".bat" for name in ("vivado","xvlog","xelab","xsim")})
results=[]
for name,source in [("registered-control",good),("forbidden-fallthrough",bad)]:
    d=out/name;d.mkdir();v=d/"dut.v";t=d/"tb.v"
    v.write_text("`timescale 1ns/1ps\n"+source,encoding="utf-8");t.write_text(tb,encoding="utf-8")
    passed,error,kind=xsim_run([v],t,"stream_pair_tb",cfg,d,timeout=60)
    record={"case":name,"passed":passed,"error":error,"kind":kind.value,"source_sha256":hashlib.sha256(v.read_bytes()).hexdigest(),"tb_sha256":hashlib.sha256(t.read_bytes()).hexdigest()}
    results.append(record);print(json.dumps(record),flush=True)
(out/"results.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
