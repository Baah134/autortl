"""Archive actual run outcomes without resetting or regrading the experiment."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path('C:/Users/prince.baah/Downloads/autortl-work')
BASE=Path('C:/Users/prince.baah/Documents/Codex/2026-10-15/hey');WORK=BASE/'work'
RUN=ROOT/'logs/build-elastic-dot4-02';PROOF=ROOT/'logs/build-elastic-dot4-02-verification'
OUT=ROOT/'evidence/2026-10-25/generated-elastic-dot4-attempt-02'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
plan=read(ROOT/'logs/build-elastic-dot4-02-prelaunch.json')
launch=read(ROOT/'logs/build-elastic-dot4-02-launch-result.json')
assert launch['source_unchanged'] and launch['stats_prefix_unchanged']
assert all(sha(ROOT/p)==h for p,h in plan['runtime_source'].items())
fixture=Path(plan['spec_path']).parent
assert all(sha(fixture/p)==h for p,h in plan['fixture_hashes'].items())
summary=read(RUN/'run_summary.json');budget=read(RUN/'budget.json')
runtime=read(RUN/'runtime.json')['implementation']
assert runtime and all(plan['runtime_source'].get(p)==h and sha(ROOT/p)==h for p,h in runtime.items())
stats=(ROOT/'llm/router_stats.jsonl').read_bytes();offset=plan['router_stats_offset']
assert hashlib.sha256(stats[:offset]).hexdigest()==plan['router_stats_prefix_sha256']
records=[json.loads(x) for x in stats[offset:].decode('utf-8').splitlines() if x.strip()]
assert len(records)==budget['llm_calls']
proof=None
if summary['status']=='done':
    assert launch['exit_code']==0
    state=read(RUN/'state.json');assert state['phase']=='DONE'
    assert all(sha(Path(p))==h for p,h in state['final_artifacts'].items())
    proof=read(PROOF/'result.json')
    assert all(proof.get(k) is True for k in ('passed','independent_exact_top_and_frozen_child',
        'all_restored_unchanged','budget_stats_and_file_set_unchanged','no_new_model_or_optimization_tool_charges','runtime_source_unchanged'))
    assert proof['checked_cycles']==852 and proof['budget']==budget
    assert all(sha(Path(p))==h for p,h in proof['identities'].items())
    codes=proof['cli_exit_codes'];assert codes['nominal']==0 and len(codes)==7 and all(v!=0 for k,v in codes.items() if k!='nominal')
    winner=RUN/'elastic_dot4_best.v';measured=Path(summary['best_artifact_dir'])/'elastic_dot4.v'
    assert sha(winner)==state['best_sha256']
    assert winner.read_bytes().replace(b'\r\n',b'\n')==measured.read_bytes().replace(b'\r\n',b'\n')
else:assert launch['exit_code']!=0
assert not OUT.exists()
OUT.mkdir(parents=True)
allowed={'.v','.sv','.py','.json','.jsonl','.log','.txt','.rpt','.md','.yaml','.tcl','.xdc','.jou'}
for tree,prefix in [(RUN,'run'),(fixture,'fixture')]+([(PROOF,'verification')] if proof else []):
    for p in tree.rglob('*'):
        rel=p.relative_to(tree)
        if not p.is_file() or p.suffix not in allowed or any(x.lower() in ('artifacts','xsim.dir','.xil','__pycache__') for x in rel.parts):continue
        dest=OUT/prefix/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
for p in (ROOT/'logs/build-elastic-dot4-02-prelaunch.json',ROOT/'logs/build-elastic-dot4-02-launch-result.json',
          WORK/'run_elastic_build02.py',WORK/'archive_elastic_build02.py',BASE/'outputs/AutoRTL-build-elastic-dot4-02.txt'):
    shutil.copyfile(p,OUT/p.name)
if proof:
    for p in (WORK/'verify_elastic_build02.py',BASE/'outputs/AutoRTL-elastic-dot4-verification-02.txt'):shutil.copyfile(p,OUT/p.name)
for p,h in plan['runtime_source'].items():
    dest=OUT/'source-snapshot'/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/p,dest);assert sha(dest)==h
(OUT/'router-records.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
result={'status':summary['status'],'launch':launch,'budget':budget,'actual_model_identity':'unobserved CLI default',
    'model_calls_recorded':len(records),'source_files':len(plan['runtime_source']),'source_unchanged':True,
    'same_original_spec_and_TB':True,'independent_cycles':852 if proof else None,
    'baseline_metrics':summary.get('baseline_metrics'),'best_metrics':summary.get('best_metrics'),
    'verification':{k:v for k,v in proof.items() if k!='identities'} if proof else None}
(OUT/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
text='# Generated elastic dot-product build02\n\n'
text+=f"Actual status: **{summary['status']}**; {len(records)} model calls, {budget['vivado_seconds']:.3f} charged tool seconds, {budget['elapsed']:.3f} saved active seconds. CLI wall {launch['cli_wall_seconds']:.3f} seconds.\n\n"
if proof:
    text+='Exact saved top plus frozen generated child independently passed 852 cycles. Actual DONE reuse and six restored tamper probes preserved budget, router records and protected file identities. These are completed-run checks, not arbitrary in-flight crash or formal proof.\n\n'
    text+='| Metric | Baseline | Winner |\n|---|---:|---:|\n'
    for key in ('lut_used','ff_used','dsp_used','bram_used','wns_ns','whs_ns','total_power_w'):
        text+=f"| {key} | {summary['baseline_metrics'].get(key)} | {summary['best_metrics'].get(key)} |\n"
    text+='\nSlice FFs exclude DSP internal registers. Report resource/timing/power tradeoffs together; no unmeasured universal gain is claimed.\n\n'
else:text+='No completed verified design or PPA gain is claimed. Original failure evidence and costs are retained.\n\n'
text+='New experiment on corrected prompt/accounting runtime, byte-identical original spec/TB and original N1/3iteration/16call/25tool/35wall/1infra limits. Qualification reference was not a generation input. Original build01 and failed checker framing remain separately archived.\n\nVivado2025.2, xc7a35tcpg236-1,100MHz, ideal zero minimum/maximum I/O delays. No board deployment or model-strength comparison is established.\n'
(OUT/'README.md').write_text(text,encoding='utf-8')
manifest={p.relative_to(OUT).as_posix():sha(p) for p in OUT.rglob('*') if p.is_file()}
(OUT/'archive-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
assert all(sha(OUT/p)==h for p,h in manifest.items())
print(json.dumps({'files':len(manifest),'status':summary['status'],'calls':len(records),'independent_cycles':result['independent_cycles']}))
