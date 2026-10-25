import hashlib,json,shutil
from pathlib import Path
ROOT=Path('C:/Users/prince.baah/Downloads/autortl-work')
WORK=Path('C:/Users/prince.baah/Documents/Codex/2026-10-15/hey')
out=ROOT/'evidence/2026-10-25/contract-campaign-12'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
history=ROOT/'curriculum/results.jsonl'
records=[json.loads(x) for x in history.read_text(encoding='utf-8').splitlines() if x.strip()]
matches=[x for x in records if x.get('tier')==0 and any('contract-campaign-12' in e.get('evidence_dir','') for e in x.get('results',[]))]
assert len(matches)==1
record=matches[0];assert record['passed']==record['total']==2 and record['qualified'] and record['full_tier']
assert record['runtime_identity']['status']=='known'
assert record['consecutive_qualifying_runs']==1 and not record['held']
assert record['cohort']!='4c34a6b14b8633c3007d246063cad7ad4453f219eb3e69b0a65a60e47019989d'
frozen=json.loads((WORK/'work/elastic-fixes-source-freeze-01.json').read_text())
assert all(sha(ROOT/p)==h for p,h in frozen.items())
launch_plan=json.loads((ROOT/'logs/contract-campaign-12-prelaunch.json').read_text())
launch_result=json.loads((ROOT/'logs/contract-campaign-12-launch-result.json').read_text())
assert launch_plan['runtime_source']==frozen and launch_result['exit_code']==0 and launch_result['source_unchanged']
assert launch_plan['git_commit']=='be60de7ef4a29f026bb863e55b282d3459778106'
source={}
for entry in record['results']:
    run=Path(entry['evidence_dir']);runtime=json.loads((run/'runtime.json').read_text())['implementation']
    assert all(sha(ROOT/p)==h for p,h in runtime.items())
    summary=json.loads((run/'run_summary.json').read_text());top=summary['top_module']
    measured=Path(summary['best_artifact_dir'])/(top+'.v');winner=run/(top+'_best.v')
    assert measured.read_bytes().replace(b'\r\n',b'\n')==winner.read_bytes().replace(b'\r\n',b'\n')
    source[entry['entry']]={'runtime_files':len(runtime),'all_runtime_hashes_match':True,
        'measured_sha256':sha(measured),'saved_sha256':sha(winner),'complete_text_equal_after_only_crlf_to_lf':True,
        'best_metrics':summary['best_metrics'],'baseline_metrics':summary['baseline_metrics'],
        'budget':json.loads((run/'budget.json').read_text())}
out.mkdir(parents=True,exist_ok=False)
allowed={'.v','.py','.json','.jsonl','.log','.txt','.rpt','.md','.yaml','.xdc','.tcl'}
runroot=ROOT/'logs/contract-campaign-12'
for p in sorted(runroot.rglob('*')):
    rel=p.relative_to(runroot)
    if not p.is_file() or p.suffix not in allowed or any(x in rel.parts for x in ('artifacts','xsim.dir','.Xil')):continue
    target=out/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
shutil.copyfile(history,out/'history-at-campaign12.jsonl')
shutil.copyfile(WORK/'outputs/AutoRTL-contract-campaign-12.txt',out/'AutoRTL-contract-campaign-12.txt')
(out/'source-verification.json').write_text(json.dumps({'launch_commit':'be60de7ef4a29f026bb863e55b282d3459778106','tested_files':len(frozen),'all_tested_identities_unchanged':True,'campaign':record,'entries':source},indent=2)+'\n')
text='# Fresh full tier0 campaign12\n\n**2/2passed, new-cohort streak1, heldfalse.**\n\n'
text+='| Entry | BaselineLUT | BestLUT | FF | Setupns | Holdns | Calls |\n|---|---:|---:|---:|---:|---:|---:|\n'
for name,x in source.items():
    m=x['best_metrics'];text+=f"| {name} | {x['baseline_metrics']['lut_used']} | {m['lut_used']} | {m['ff_used']} | {m['wns_ns']} | {m['whs_ns']} | {x['budget']['llm_calls']} |\n"
text+='''
Fresh full merge gate onbe60de7ef4a29f026bb863e55b282d3459778106 with1415tests. Both runtime manifests
match the committed source; all220 tested identities remained unchanged.
The oracle prompt and active-wall checkpoint fixes changed runtime identity, so prior cohort streaks
are not carried over. Modelidentity remains unobserved CLIdefault; no weaker-model
or general optimization reliability claim follows.

Vivado2025.2,xc7a35tcpg236-1,100MHz,idealzero min/max I/O. Perentry:
1iteration/1candidate,16calls,20tool/30wallminutes,1infraretry. Mandatory
simulation/tool-exit/routedmetric/timing gates passed. Actual failed/no-gain
proposals remain raw; verified baseline retention is permitted by tier0criteria.
This gate is separate from the26LUT divider measurement on originalcfef8af.
'''
(out/'README.md').write_text(text,encoding='utf-8')
for path in (ROOT/'logs/contract-campaign-12-prelaunch.json',ROOT/'logs/contract-campaign-12-launch-result.json',
             WORK/'work/run_campaign12.py',Path(__file__)):
    shutil.copyfile(path,out/path.name)
manifest={p.relative_to(out).as_posix():sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
(out/'archive-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
assert all(sha(out/p)==h for p,h in manifest.items())
print(json.dumps({'files':len(manifest),'bytes':sum((out/p).stat().st_size for p in manifest),'cohort':record['cohort'],'streak':record['consecutive_qualifying_runs'],'held':record['held'],'entries':{k:{'luts':v['best_metrics']['lut_used'],'calls':v['budget']['llm_calls']} for k,v in source.items()}}))
