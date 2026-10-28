"""Archive actual run outcomes without resetting or regrading the experiment."""
import hashlib,json,runpy,shutil
from pathlib import Path
ROOT=Path('C:/Users/prince.baah/Downloads/autortl-work')
BASE=Path('C:/Users/prince.baah/Documents/Codex/2026-10-15/hey');WORK=BASE/'work'
RUN=ROOT/'logs/build-signed-fir4-02';PROOF=ROOT/'logs/build-signed-fir4-02-verification'
OUT=ROOT/'evidence/2026-10-26/generated-signed-fir4-attempt-02'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
assert not OUT.exists(),'Never overwrite an archived attempt'
identities=runpy.run_path(str(WORK/'validate_seed_binding_live.py'))['identities']
plan=read(ROOT/'logs/build-signed-fir4-02-prelaunch.json')
assert len(plan['runtime_source'])==230 and identities()==plan['runtime_source']
assert set(plan['runtime_diff_from_build01'])=={'autortl/tbgen.py','data/taxonomy.yaml'}
assert plan['reference_is_not_a_generation_input'] is True
assert plan['budgets']=={'iterations':3,'best_of_n':1,'model_calls':16,'tool_minutes':25,'wall_minutes':35,'infra_retries':1}
assert sha(WORK/'run_signed_fir4_build02.py')==plan['helper_sha256']
freeze=WORK/'fir4-coverage-source-freeze-01.json';full=WORK/'fir4-coverage-full-result-01.json'
assert sha(freeze)==plan['source_freeze_sha256'] and read(freeze)==plan['runtime_source']
assert sha(full)==plan['full_test_receipt_sha256']
full_result=read(full)
assert full_result['exit_code']==0 and full_result['source_unchanged'] and full_result['source_files']==230
assert full_result['source_freeze_sha256']==sha(freeze)
# Related archives stay separate. Their hashes link old outcomes without regrading.
related={}
for name in ('generated-signed-fir4-attempt-01','fir4-coverage-tests-01','fir4-driver-comparison-01'):
    archive=ROOT/'evidence/2026-10-26'/name
    manifest=read(archive/'archive-manifest.json')
    assert all(sha(archive/p)==h for p,h in manifest.items())
    related[name]={'path':archive.relative_to(ROOT).as_posix(),'manifest_sha256':sha(archive/'archive-manifest.json'),'verified_files':len(manifest)}
original=read(ROOT/'evidence/2026-10-26/generated-signed-fir4-attempt-01/result.json')
assert original['status']=='done' and original['independent_cycles']==800
assert original['best_metrics']['lut_used']==52 and original['model_calls_recorded']==12
admission=Path(plan['admission_archive']);admitted=read(admission/'admission/result.json')
assert sha(admission/'archive-manifest.json')==plan['admission_manifest_sha256']
assert all(sha(admission/p)==h for p,h in read(admission/'archive-manifest.json').items())
assert admitted['qualified'] and admitted['admitted']==admitted['executed']==admitted['planned']==28
admission_plan=read(admission/'admission/prelaunch-plan.json')
assert plan['spec_sha256']==admission_plan['stage_files']['design_spec.json']
assert plan['tb_sha256']==admission_plan['stage_files']['signed_fir4_tb.v']
launch=read(ROOT/'logs/build-signed-fir4-02-launch-result.json')
assert launch['source_unchanged'] and launch['stats_prefix_unchanged']
assert all(sha(ROOT/p)==h for p,h in plan['runtime_source'].items())
fixture=Path(plan['spec_path']).parent
assert all(sha(fixture/p)==h for p,h in plan['fixture_hashes'].items())
summary=read(RUN/'run_summary.json');budget=read(RUN/'budget.json')
runtime=read(RUN/'runtime.json')['implementation']
assert runtime==plan['runtime_implementation'] and all(plan['runtime_source'].get(p)==h and sha(ROOT/p)==h for p,h in runtime.items())
stats=(ROOT/'llm/router_stats.jsonl').read_bytes();offset=plan['router_stats_offset']
assert hashlib.sha256(stats[:offset]).hexdigest()==plan['router_stats_prefix_sha256']
records=[json.loads(x) for x in stats[offset:].decode('utf-8').splitlines() if x.strip()]
assert len(records)==budget['llm_calls']
assert sha(Path(plan['spec_path']))==plan['spec_sha256'] and sha(Path(plan['tb_path']))==plan['tb_sha256']
proof=None
if summary['status']=='done':
    assert launch['exit_code']==0
    state=read(RUN/'state.json');assert state['phase']=='DONE'
    assert all(sha(Path(p))==h for p,h in state['final_artifacts'].items())
    proof=read(PROOF/'result.json')
    assert all(proof.get(k) is True for k in ('passed','independent_exact_top_and_frozen_child',
        'all_restored_unchanged','budget_stats_and_file_set_unchanged','no_new_model_or_optimization_tool_charges','runtime_source_unchanged'))
    assert proof['checked_cycles']==800 and proof['budget']==budget
    assert proof['proof_helper_sha256']==sha(WORK/'verify_signed_fir4_build02.py')
    assert proof['prelaunch_sha256']==sha(ROOT/'logs/build-signed-fir4-02-prelaunch.json')
    assert all(sha(Path(p))==h for p,h in proof['identities'].items())
    codes=proof['cli_exit_codes'];assert codes['nominal']==0 and len(codes)==7 and all(v!=0 for k,v in codes.items() if k!='nominal')
    winner=RUN/'signed_fir4_best.v';measured=Path(summary['best_artifact_dir'])/'signed_fir4.v'
    assert sha(winner)==state['best_sha256']
    assert winner.read_bytes().replace(b'\r\n',b'\n')==measured.read_bytes().replace(b'\r\n',b'\n')
else:assert launch['exit_code'] is not None and launch['exit_code']!=0
assert not OUT.exists()
OUT.mkdir(parents=True)
allowed={'.v','.sv','.py','.json','.jsonl','.log','.txt','.rpt','.md','.yaml','.tcl','.xdc','.jou'}
for tree,prefix in [(RUN,'run'),(fixture,'fixture')]+([(PROOF,'verification')] if proof else []):
    for p in tree.rglob('*'):
        rel=p.relative_to(tree)
        if not p.is_file() or p.suffix not in allowed or any(x.lower() in ('artifacts','xsim.dir','.xil','__pycache__') for x in rel.parts):continue
        dest=OUT/prefix/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
for p in (ROOT/'logs/build-signed-fir4-02-prelaunch.json',ROOT/'logs/build-signed-fir4-02-launch-result.json',
          WORK/'run_signed_fir4_build02.py',WORK/'archive_signed_fir4_build02.py',freeze,full,
          BASE/'outputs/AutoRTL-build-signed-fir4-02.txt'):
    shutil.copyfile(p,OUT/p.name)
if proof:
    for p in (WORK/'verify_signed_fir4_build02.py',BASE/'outputs/AutoRTL-signed-fir4-verification-02.txt'):shutil.copyfile(p,OUT/p.name)
for p,h in plan['runtime_source'].items():
    dest=OUT/'source-snapshot'/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/p,dest);assert sha(dest)==h
(OUT/'router-records.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
result={'status':summary['status'],'launch':launch,'budget':budget,'actual_model_identity':'unobserved CLI default',
    'model_calls_recorded':len(records),'source_files':len(plan['runtime_source']),'source_unchanged':True,'runtime_diff_from_build01':plan['runtime_diff_from_build01'],'related_evidence':related,
    'same_original_spec_and_TB':True,'independent_cycles':800 if proof else None,
    'baseline_metrics':summary.get('baseline_metrics'),'best_metrics':summary.get('best_metrics'),
    'verification':{k:v for k,v in proof.items() if k!='identities'} if proof else None}
(OUT/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
text='# Generated signed FIR4 build02\n\n'
text+=f"Actual status: **{summary['status']}**; {len(records)} model calls, {budget['vivado_seconds']:.3f} charged tool seconds, {budget['elapsed']:.3f} saved active seconds. CLI wall {launch['cli_wall_seconds']:.3f} seconds.\n\n"
if proof:
    text+='Exact saved top plus frozen generated child independently passed 800 cycles. Actual DONE reuse and six restored tamper probes preserved budget, router records and protected file identities. These are completed-run checks, not arbitrary in-flight crash or formal proof.\n\n'
    text+='| Metric | Baseline | Winner |\n|---|---:|---:|\n'
    for key in ('lut_used','ff_used','dsp_used','bram_used','wns_ns','whs_ns','total_power_w'):
        text+=f"| {key} | {summary['baseline_metrics'].get(key)} | {summary['best_metrics'].get(key)} |\n"
    text+='\nSlice FFs exclude DSP internal registers. Report resource/timing/power tradeoffs together; no unmeasured universal gain is claimed.\n\n'
else:text+='No completed verified design or PPA gain is claimed. Original failure evidence and costs are retained.\n\n'
text+='New signed FIR4 experiment on the tested coverage runtime: signed extrema payload traces, legal bubbles with changing invalid data, and sync-only off-edge reset pulses. Runtime changes from original01 are limited to tbgen.py and taxonomy data. The full regression receipt binds230 source identities. No oracle API, roles, retries or budget expansion.\n\n'
text+='The same byte-identical admitted spec/TB and original N1/3iteration/16call/25tool/35wall/1infra limits apply; qualification reference was never a generation seed. Original01 remains separately preserved at52LUT/12modelcalls with independent800-cycle proof and is never reset or regraded. Results are separate model trials, not a causal efficiency comparison.\n\n'
text+='The controlled old-oracle driver comparison detected22/27 faults. That result belongs to the frozen controlled comparison, not this fresh generated oracle/testbench; no fresh-grader score is inferred here. Independent integration checks remain required for exact readiness/availability and occupied-reset behavior.\n\n'
text+='Vivado2025.2, xc7a35tcpg236-1,100MHz, ideal zero minimum/maximum I/O delays. No board deployment, formal equivalence, arbitrary hard-kill atomicity or model-strength comparison is established.\n'
(OUT/'README.md').write_text(text,encoding='utf-8')
manifest={p.relative_to(OUT).as_posix():sha(p) for p in OUT.rglob('*') if p.is_file()}
(OUT/'archive-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
assert all(sha(OUT/p)==h for p,h in manifest.items())
assert identities()==plan['runtime_source']
assert (ROOT/'llm/router_stats.jsonl').read_bytes()==stats
print(json.dumps({'files':len(manifest),'status':summary['status'],'calls':len(records),'independent_cycles':result['independent_cycles']}))
