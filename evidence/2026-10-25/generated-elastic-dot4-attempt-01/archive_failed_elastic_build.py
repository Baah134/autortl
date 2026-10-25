import ast,hashlib,json,shutil
from pathlib import Path
ROOT=Path('C:/Users/prince.baah/Downloads/autortl-work');WORK=Path('C:/Users/prince.baah/Documents/Codex/2026-10-15/hey')
RUN=ROOT/'logs/build-elastic-dot4-01';OUT=ROOT/'evidence/2026-10-25/generated-elastic-dot4-attempt-01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text(encoding='utf-8'))
plan=read(ROOT/'logs/build-elastic-dot4-01-prelaunch.json');summary=read(RUN/'run_summary.json');budget=read(RUN/'budget.json')
assert summary['status']=='module_failed' and budget['llm_calls']==2
assert all(sha(ROOT/p)==h for p,h in plan['runtime_source'].items())
stage=WORK/'work/elastic-dot4-stage';assert all(sha(stage/p)==h for p,h in plan['fixture_hashes'].items())
records=[]
for p in RUN.glob('journal/*/completed.json'):
    d=read(p)
    if ':model:generator.golden_model:' in d['stage']:records.append(d)
records.sort(key=lambda d:d['stage']);assert len(records)==2
bad='def step(state, inputs: dict) -> (state, outputs: dict)'
assert bad in records[0]['result'] and bad in (ROOT/'autortl/prompts.py').read_text(encoding='utf-8')
try:ast.parse(records[0]['result']);raise AssertionError('Originalsource unexpectedlyparsed')
except SyntaxError:pass
assert any(type(n).__name__=='JoinedStr' for n in ast.walk(ast.parse(records[1]['result'])))
stats=[json.loads(x) for x in (ROOT/'llm/router_stats.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()][-2:]
assert [r['metadata']['session_id'] for r in stats]==['01a1748d-ea69-7251-97d7-1390e5916f15','01a1748e-05d8-7940-aba3-20be294668e9']
OUT.mkdir(parents=True,exist_ok=False)
allowed={'.v','.py','.json','.jsonl','.log','.txt','.rpt','.md','.yaml','.tcl','.xdc'}
for source,prefix in ((RUN,'run'),(stage,'fixture')):
    for p in source.rglob('*'):
        rel=p.relative_to(source)
        if not p.is_file() or p.suffix not in allowed or any(x.lower() in ('xsim.dir','.xil','artifacts','__pycache__') for x in rel.parts):continue
        dest=OUT/prefix/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
for name in plan['runtime_source']:
    dest=OUT/'source-snapshot'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
for p in (ROOT/'logs/build-elastic-dot4-01-prelaunch.json',WORK/'work/prepare_elastic_build.py',Path(__file__),WORK/'outputs/AutoRTL-build-elastic-dot4-01.txt'):
    shutil.copyfile(p,OUT/p.name)
for i,r in enumerate(records):(OUT/f'golden-response-{i}.py').write_text(r['result'],encoding='utf-8')
(OUT/'router-records.json').write_text(json.dumps(stats,indent=2),encoding='utf-8')
receipt={'status':'module_failed','model_calls':2,'tool_seconds':budget['vivado_seconds'],
    'saved_budget':budget,'saved_elapsed_is_last_checkpoint_not_full_wall':True,'actual_cli_wall_seconds':None,
    'reported_model_seconds':sum(r['seconds'] for r in stats),'reported_usage':{k:sum(r['metadata']['usage'][k] for r in stats) for k in ('input_tokens','cached_input_tokens','output_tokens')},
    'initial_prompt_invalid_signature_copied':True,'retry_uses_unsupported_fstrings':True,'no_RTL_generated':True,
    'runtime_source_unchanged':True,'original_run_never_reset':True}
(OUT/'result.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
(OUT/'README.md').write_text('''# Elastic dot-product build01: failed before RTL generation

Both generated oracle attempts were rejected. First copied the prompt's invalid
Python API signature; repair parsed but used unsupported f-strings. The existing
restricted interpreter correctly rejected them. No valid RTL/baseline/PPA result.
Two model calls are charged; all sources, inputs and accepted19-case checker
stayed frozen. Original source211 snapshot and both responses are retained.

Budget elapsed is the last saved checkpoint, not full active wall duration.
Model seconds/usage are retained separately; do not infer full wall from that
checkpoint or reset the failed run. This archive precedes prompt/budget fixes.
''',encoding='utf-8')
manifest={p.relative_to(OUT).as_posix():sha(p) for p in OUT.rglob('*') if p.is_file()}
(OUT/'archive-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
assert all(sha(OUT/p)==h for p,h in manifest.items())
print(json.dumps({'files':len(manifest),'status':summary['status'],'model_calls':2,'no_RTL':True,'source_files':len(plan['runtime_source'])}))
