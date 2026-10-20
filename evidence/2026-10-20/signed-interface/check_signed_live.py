"""Supervised signed wrapper/TB and symbolic-parameter stub qualification."""
import hashlib,json,subprocess,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve();sys.path.insert(0,str(root))
from autortl.spec import ModuleSpec,Port,DesignSpec
from autortl.linter import stub_verilog,top_verilog,lint_spec
from autortl.tbgen import generate_fixed_latency_tb,gen_stimulus
from autortl.golden import GoldenModel
from autortl.static_checks import check
from autortl.verilog_interface import infer_module
from autortl.config import RunConfig
from autortl.vivado import xsim_run
from autortl.triage import FailureKind
out=root/'logs/signed-interface-01';out.mkdir(parents=True,exist_ok=False)
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
implementation={}
for directory in ('autortl','llm','data','.claude/skills'):
 for path in sorted((root/directory).rglob('*')):
  if path.is_file() and path.suffix in ('.py','.v','.yaml','.md'):
   implementation[path.relative_to(root).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
(out/'harness_identity.json').write_text(json.dumps({'base_commit':revision,'uncommitted_changes':True,'implementation':implementation},indent=2))
bins=Path('C:/AMDDesignTools/2025.2/Vivado/bin')
cfg=RunConfig(mode='optimize',**{n+'_bin':str(bins/(n+'.bat')) for n in ('vivado','xvlog','xelab','xsim')})
ports=[Port('a','input',8,signed=True,packed_dimensions=[[0,7]]),Port('b','input',8,signed=True,packed_dimensions=[[0,7]]),Port('less','output',1)]
child=ModuleSpec('signed_cmp','signed eight-bit comparison',ports)
design=DesignSpec('signed_top',[child],external_ports=ports)
assert not lint_spec(design),lint_spec(design)
wrapper=top_verilog(design)
control=stub_verilog(child).replace('endmodule','assign less = a < b;\nendmodule')
assert check(control,child).passed
unsigned=control.replace('wire signed','wire')
assert not check(unsigned,child).passed
oracle=out/'golden.py'
oracle.write_text('''def init():
    return {}
def step(state, inputs):
    a = inputs['a']
    b = inputs['b']
    sa = a if a < 128 else a - 256
    sb = b if b < 128 else b - 256
    return state, {'less': int(sa < sb)}
''')
gm=GoldenModel(oracle)
stimulus=[{'a':128,'b':127},{'a':255,'b':1},{'a':0,'b':255},{'a':127,'b':128}]+gen_stimulus(child,n_random=50)
expected=gm.run(stimulus)
assert expected[:4]==[{'less':1},{'less':1},{'less':0},{'less':0}]
tb_spec=ModuleSpec('signed_top',child.behavior,ports)
tb=generate_fixed_latency_tb(tb_spec,stimulus,expected)
cases=[]
for name,source,wanted in [('signed_control',control,True),('unsigned_mutant',unsigned,False)]:
 cases.append((name,{'signed_cmp.v':source,'signed_top.v':wrapper},tb,'signed_top_tb',wanted))
original='''module param_shape #(parameter W=8, EXTRA=0)(a,y);
localparam PW=W+EXTRA;
input signed [PW-1:0] a;
output signed [0:PW-1] y;
assign y=a;
endmodule'''
m=infer_module(original,'param_shape')
symbolic=stub_verilog(m)
param_tb='''`timescale 1ns/1ps
module param_shape_tb;
reg signed [12:0] a;
wire signed [0:12] y;
integer errors=0;
param_shape #(.W(12),.EXTRA(1)) dut(.a(a),.y(y));
initial begin
 a=13'h1f03; #2; if(y!==a) begin $display("FAIL nondefault parameter negative bits");errors=errors+1;end
 a=13'd1; #2; if(y!==a) begin $display("FAIL nondefault parameter positive bits");errors=errors+1;end
 a=13'h1fff; #2; if(y!==a) begin $display("FAIL nondefault parameter all ones");errors=errors+1;end
 if(errors==0)$display("TEST PASSED");else $display("TEST FAILED: %0d errors",errors);
 $finish;
end
initial begin #100;$display("TEST FAILED: watchdog");$finish;end
endmodule'''
for name,assignment,wanted in [('parameter_control','assign y=a;',True),('parameter_zero_mutant','assign y=0;',False)]:
 source=symbolic.replace('endmodule',assignment+'\nendmodule')
 assert infer_module(source,'param_shape').interface_signature==m.interface_signature
 cases.append((name,{'param_shape.v':source},param_tb,'param_shape_tb',wanted))
results=[]
for name,sources,tb_text,top,wanted in cases:
 work=out/name;work.mkdir()
 files=[]
 for filename,source in sources.items():
  path=work/filename;path.write_text('`timescale 1ns/1ps\n'+source);files.append(path)
 tb_path=work/'tb.v';tb_path.write_text(tb_text)
 passed,error,kind=xsim_run(files,tb_path,top,cfg,work,timeout=90)
 detected=not passed and kind==FailureKind.DESIGN and (error.startswith('Testbench failures:') or error=='testbench reported failure')
 result={'case':name,'expected_pass':wanted,'passed':passed,'ok':passed if wanted else detected,'error':error,'failure_kind':kind.value,
 'source_base_commit':revision,'runtime_identity':'harness_identity.json','files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files+[tb_path]}}
 results.append(result);(out/'results.json').write_text(json.dumps(results,indent=2));print(json.dumps(result),flush=True)
raise SystemExit(0 if all(r['ok'] for r in results) else 1)
