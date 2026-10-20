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
_,spec,_,_,_=next(row for row in cases() if row[0]=="scoreboard_good")
spec.latency=100
stim=[{"a":i,"b":i+1} for i in range(3)]
exp=[{"y":r["a"]+r["b"],"z":r["a"]^r["b"]} for r in stim]
tb=generate_scoreboard_tb(spec,stim,exp)
source="""`timescale 1ns/1ps
module stream_pair(input clk,rst,input [7:0] a,b,input in_valid,out_ready,
output in_ready,output reg out_valid,output reg [7:0] y,z);
reg busy; integer remaining;
assign in_ready=!busy && !out_valid;
always @(posedge clk) begin
 if(rst) begin busy<=0; remaining<=0; out_valid<=0;y<=0;z<=0;end
 else begin
  if(out_valid && out_ready) out_valid<=0;
  if(busy) begin
   if(remaining==1) begin busy<=0;out_valid<=1;end
   else remaining<=remaining-1;
  end
  if(in_valid && in_ready) begin busy<=1;remaining<=100;y<=a+b;z<=a^b;end
 end
end endmodule
"""
cfg=RunConfig(mode="optimize",**{name+"_bin":"C:/AMDDesignTools/2025.2/Vivado/bin/"+name+".bat" for name in ("vivado","xvlog","xelab","xsim")})
cfg.save(out/"config.json")
old=3*12+32+100;new=3*(12+100)+32
assert f"_autortl_cycle<{new}" in tb
short=tb.replace(f"_autortl_cycle<{new}",f"_autortl_cycle<{old}")
results=[]
for name,text,expected in [("short-budget-reproduction",short,False),("per-transaction-budget",tb,True)]:
 d=out/name;d.mkdir();v=d/"dut.v";t=d/"tb.v";v.write_text(source,encoding="utf-8");t.write_text(text,encoding="utf-8")
 passed,error,kind=xsim_run([v],t,"stream_pair_tb",cfg,d,timeout=60)
 raw=(d/"sim_log.txt").read_text(encoding="utf-8")
 ok=(passed is True) if expected else (passed is False and "FAIL scoreboard did not drain" in raw)
 record={"case":name,"ok":ok,"expected_pass":expected,"passed":passed,"error":error,"kind":kind.value,"source_sha256":hashlib.sha256(v.read_bytes()).hexdigest(),"tb_sha256":hashlib.sha256(t.read_bytes()).hexdigest()}
 results.append(record);print(json.dumps(record),flush=True)
(out/"results.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
raise SystemExit(0 if all(r["ok"] for r in results) else 1)
