import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path("C:/Users/prince.baah/Downloads/autortl-work");sys.path.insert(0,str(ROOT))
from autortl.spec import DesignSpec
from autortl.tbgen import generate
from autortl.golden import GoldenModel
from autortl.config import RunConfig
from autortl.vivado import xsim_run
from curriculum.tier2.skid_buffer_build.qualification.cases import case_sources
p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);a=p.parse_args()
out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
spec=DesignSpec.load(ROOT/"curriculum/tier2/skid_buffer_build/design_spec.json").modules[0]
gold=out/"payload_identity.py";gold.write_text('def init(): return {}\ndef step(s,i): return s,{"out_data":i["in_data"] & 255}\n',encoding="utf-8")
tb=generate(spec,GoldenModel(gold),out)
cfg=RunConfig(mode="optimize",**{n+"_bin":"C:/AMDDesignTools/2025.2/Vivado/bin/"+n+".bat" for n in ("vivado","xvlog","xelab","xsim")});cfg.save(out/"config.json")
results=[]
for name in ("reference","capacity_one"):
 d=out/name;d.mkdir();v=d/"dut.v";v.write_text(case_sources()[name],encoding="utf-8")
 passed,error,kind=xsim_run([v],tb,"skid_buffer_core_tb",cfg,d,timeout=60)
 record={"case":name,"passed":passed,"error":error,"kind":kind.value,"source_sha256":hashlib.sha256(v.read_bytes()).hexdigest(),"tb_sha256":hashlib.sha256(tb.read_bytes()).hexdigest(),"scope":"Coverage investigation: capacity_one violates the two-entry contract even if payload scoreboard passes."}
 results.append(record);print(json.dumps(record),flush=True)
(out/"results.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
raise SystemExit(0 if all(r["passed"] for r in results) else 1)
