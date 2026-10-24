"""Controlled old/new mechanical wrapper experiment; same generated children/TB."""
import hashlib,importlib.util,json,shutil,sys,time
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8',errors='replace')
ROOT=Path('C:/Users/prince.baah/Downloads/autortl-work')
WORK=Path('C:/Users/prince.baah/Documents/Codex/2026-10-15/hey')
RUN=ROOT/'logs/build-dot4-01';OUT=ROOT/'logs/dot4-timescale-order-01'
sys.path.insert(0,str(ROOT))
from autortl.spec import DesignSpec
from autortl.linter import top_verilog
from autortl.config import RunConfig
from autortl.vivado import xsim_run
from autortl.triage import FailureKind
from autortl.contract_context import tool_exit_evidence
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=json.loads((ROOT/'logs/build-dot4-01-prelaunch.json').read_text());assert all(sha(ROOT/p)==h for p,h in plan['runtime_source'].items())
spec=DesignSpec.load(RUN/'inputs/spec_path.json')
old=top_verilog(spec)
patch=WORK/'work/top-timescale-stage/autortl/linter.py'
loader=importlib.util.spec_from_file_location('autortl._timescale_stage',patch)
module=importlib.util.module_from_spec(loader);loader.loader.exec_module(module)
new=module.top_verilog(spec)
assert new=='`timescale 1ns/1ps\n'+old and '@latency' not in new
children=[RUN/'modules'/n/(n+'.v') for n in ('dot4_pair01','dot4_pair23','dot4_merge')]
tb_source=RUN/'inputs/testbench_path.v';stats=ROOT/'llm/router_stats.jsonl';stats_hash=sha(stats)
original={str(p):sha(p) for p in [*children,tb_source]}
cfg=RunConfig.load(RUN/'config.json');OUT.mkdir(parents=True,exist_ok=False);rows=[]
for name,source in [('before',old),('after',new)]:
    directory=OUT/name;directory.mkdir()
    top=directory/'dot4_pipeline.v';top.write_text(source,encoding='utf-8',newline='\n')
    copies=[]
    for p in children:
        dest=directory/p.name;shutil.copyfile(p,dest);assert sha(dest)==sha(p);copies.append(dest)
    tb=directory/'tb.v';shutil.copyfile(tb_source,tb)
    tick=time.monotonic();okay,error,kind=xsim_run([top,*copies],tb,'dot4_pipeline_tb',cfg,directory,timeout=90)
    exits=tool_exit_evidence(directory)
    if name=='before':expected=(not okay and kind==FailureKind.DESIGN and 'XSIM 43-4099' in error)
    else:
        raw=(directory/'sim_log.txt').read_text(errors='replace')
        expected=(okay and kind==FailureKind.DESIGN and 'TEST PASSED' in raw and 'COVERAGE checked=685' in raw
            and exits['schema_valid'] and all(exits['latest_by_tool'].get(t,{}).get('successful') for t in ('xvlog','xelab','xsim')))
    row={'name':name,'expected_outcome_observed':bool(expected),'simulation_passed':okay,'failure_kind':kind.value,
         'error':error,'elapsed_seconds':time.monotonic()-tick,'top_sha256':sha(top),'process_exits':exits}
    rows.append(row);(directory/'result.json').write_text(json.dumps(row,indent=2),encoding='utf-8')
    print(json.dumps({k:row[k] for k in ('name','expected_outcome_observed','simulation_passed','error')}),flush=True)
assert all(x['expected_outcome_observed'] for x in rows)
assert sha(stats)==stats_hash and all(sha(Path(p))==h for p,h in original.items())
assert all(sha(ROOT/p)==h for p,h in plan['runtime_source'].items())
result={'passed':True,'same_generated_children_and_tb':original,'only_wrapper_timescale_added':True,
        'top_compiled_first_in_both':True,'model_calls':0,'router_stats_unchanged':True,
        'original_runtime_source_unchanged':True,'staged_linter_sha256':sha(patch),'cases':rows}
(OUT/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'passed':True,'before':'XSIM43-4099 reproduced','after':'685cyclePASS','model_calls':0}),flush=True)
