"""Actual DONE reuse and restored feedback/source/script identity probes."""
import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);parser.add_argument('--output',required=True);parser.add_argument('--python',required=True)
args=parser.parse_args();root=Path.cwd();run=Path(args.run).resolve();out=Path(args.output).resolve()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
state=json.loads((run/'state.json').read_text());assert state['phase']=='DONE'
summary=json.loads((run/'run_summary.json').read_text());assert summary['status']=='done'
paths={Path(p) for p in state['final_artifacts']}
paths.update(run/name for name in ('state.json','runtime.json','config.json','budget.json','run_summary.json','inputs.json',summary['top_module']+'_best.v','events.jsonl','designs.jsonl','progress.md','plan.md') if (run/name).is_file())
paths.update(Path(v['path']) for v in json.loads((run/'inputs.json').read_text()).values())
paths.update(run.glob('journal/*/completed.json'))
paths.update(run.glob('journal/*/started.json'))
stats=root/'llm/router_stats.jsonl';paths.add(stats)
before={str(p):sha(p) for p in paths}
files={str(p.relative_to(run)) for p in run.rglob('*') if p.is_file()}
out.mkdir(parents=True,exist_ok=False)


def invoke(name):
    process=subprocess.Popen([args.python,'-u','run.py','resume','--run',str(run)],cwd=root,
        env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
    try: output=process.communicate(timeout=60)[0]
    except subprocess.TimeoutExpired:
        subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True)
        output=process.communicate()[0]
        (out/(name+'.txt')).write_text(output,encoding='utf-8')
        raise RuntimeError('Owned DONE proof timed out')
    (out/(name+'.txt')).write_text(output,encoding='utf-8')
    return process.returncode


results={'nominal':invoke('nominal')};assert results['nominal']==0
assert all(sha(Path(p))==h for p,h in before.items())
outcomes=sorted(run.glob('iter_*/proposal_outcome.json'));assert outcomes
selected_outcome=outcomes[-1]
last=json.loads(selected_outcome.read_text())
candidate=next(c for p in reversed(outcomes) for c in json.loads(p.read_text())['candidates']
               if c.get('source') and c.get('flow_script'))
probes=[('feedback_input',run/'iter_002/proposal_input.json'),('feedback_outcome',selected_outcome),
        ('prior_standard_source',Path(candidate['source']['path'])),('prior_standard_script',Path(candidate['flow_script']['path']))]
bindings=sorted(run.glob('iter_*/proposal_plan_binding.json'))
assert bindings, 'Fresh seed-bound run must retain plan bindings'
probes.append(('plan_seed_binding',bindings[-1]))
for name,path in probes:
    assert str(path.resolve()) in state['final_artifacts']
    data=path.read_bytes()
    try:
        path.write_bytes(data+b'\n ')
        results[name]=invoke(name)
        assert results[name]!=0
        assert 'missing or modified' in (out/(name+'.txt')).read_text()
    finally: path.write_bytes(data)
    assert all(sha(Path(p))==h for p,h in before.items())
assert files=={str(p.relative_to(run)) for p in run.rglob('*') if p.is_file()}
result={'ok':True,'run':str(run),'scope':'Actual DONE reuse and restored input/outcome/standard source/script/plan binding tamper; not in-flight hard-kill recovery',
    'protected_identities':len(before),'all_restored_unchanged':True,'file_set_unchanged':True,'budget_and_router_stats_unchanged':True,
    'no_new_model_or_tool_charges':True,'cli_exit_codes':results,'identities':before}
(out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
manifest={p.name:sha(p) for p in out.iterdir() if p.is_file()}
(out/'archive-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='identities'}),flush=True)
