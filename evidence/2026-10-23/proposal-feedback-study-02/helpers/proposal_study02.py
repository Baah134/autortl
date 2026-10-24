"""Predeclared local feedback ablation; one bounded run per invocation."""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
import traceback
from pathlib import Path

ROOT = Path('C:/Users/prince.baah/Downloads/autortl-work')
WORK = Path('C:/Users/prince.baah/Documents/Codex/2026-10-15/hey')
sys.path.insert(0, str(ROOT))
from autortl.config import RunConfig
from autortl.fsm import Orchestrator
from autortl.state import atomic_write_text
from autortl.vivado import xsim_run
from autortl.triage import FailureKind
from autortl.cache import code_hash

sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
STUDY = ROOT/'logs/proposal-feedback-study-02'
ORDER = [(1,False),(1,True),(2,True),(2,False),(3,False),(3,True)]


def identities():
    result = {}
    for name in ('autortl','llm','tests','curriculum','scripts','data','.claude'):
        for p in (ROOT/name).rglob('*'):
            if p.is_file() and p.suffix in ('.py','.v','.sv','.json','.yaml','.md') and '__pycache__' not in p.parts:
                result[p.relative_to(ROOT).as_posix()] = sha(p)
    result['run.py'] = sha(ROOT/'run.py')
    return result


def prepare():
    STUDY.mkdir(parents=True,exist_ok=False)
    original=ROOT/'logs/build-golden-divider-01'
    archive=ROOT/'evidence/2026-10-23/generated-divider-attempt-01/build-golden-divider-01'
    paths=[Path('iter_000/iterative_divider.v'),Path('modules/iterative_divider_core/iterative_divider_core.v')]
    for rel in paths:
        assert sha(original/rel)==sha(archive/rel), f'Original source drift: {rel}'
    seed=STUDY/'seed.v'
    # Edit only the parameterized core. Freeze the wrapper inside the TB,
    # preserving all six independently admitted behavioral case bodies.
    seed.write_bytes((original/paths[1]).read_bytes())
    tb=STUDY/'tb.v'
    body=(ROOT/'curriculum/tier3/iterative_divider_build/iterative_divider_tb.v').read_text(encoding='utf-8')
    assert body.count('module iterative_divider_tb;')==1
    renamed=body.replace('module iterative_divider_tb;','module iterative_divider_core_tb;')
    assert renamed.replace('module iterative_divider_core_tb;','module iterative_divider_tb;')==body
    wrapper=(original/paths[0]).read_text(encoding='utf-8')
    tb.write_text(wrapper+'\n\n'+renamed,encoding='utf-8',newline='\n')
    plan={'schema_version':1,'order':ORDER,'helper_sha256':sha(Path(__file__)),
          'seed_sha256':sha(seed),'testbench_sha256':sha(tb),
          'sources':[{'path':str(original/p),'sha256':sha(original/p)} for p in paths],
          'runtime_source':identities(),'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
          'task':'Optimize original generated parameterized core only; frozen original wrapper appended to independently admitted TB with only its container module renamed; all six behavioral cases preserved',
          'model':'codex.default; actual model identity unknown unless emitted',
          'budgets':{'iterations':3,'best_of_n':1,'model_calls':16,'tool_minutes':25,'wall_minutes':35,'infra_retries':1},
          'decision':'Require fewer repeated proposals, no lower verified completion and no material (>25%) aggregate tool/wall/token cost increase; exploratory n=3, no model strength or product superiority claim'}
    atomic_write_text(STUDY/'plan.json',json.dumps(plan,indent=2))
    print(json.dumps({'prepared':True,'source_files':len(plan['runtime_source']),'seed':sha(seed),'tb':sha(tb)}),flush=True)


def run(index):
    plan=json.loads((STUDY/'plan.json').read_text())
    assert sha(Path(__file__))==plan['helper_sha256'],'Study helper drift'
    assert identities()==plan['runtime_source'],'Frozen study source drift'
    assert sha(STUDY/'seed.v')==plan['seed_sha256']
    assert sha(STUDY/'tb.v')==plan['testbench_sha256']
    pair,enabled=plan['order'][index]
    output=STUDY/f'pair{pair}-{"feedback" if enabled else "baseline"}'
    if output.exists(): raise RuntimeError('Never reset or overwrite a study run')
    binroot='C:/AMDDesignTools/2025.2/Vivado/bin/'
    cfg=RunConfig(mode='optimize',top_module='iterative_divider_core',design_path=STUDY/'seed.v',
        testbench_path=STUDY/'tb.v',max_iterations=3,best_of_n=1,max_llm_calls=16,
        max_vivado_minutes=25,max_wall_minutes=35,max_infra_retries=1,
        vivado_bin=binroot+'vivado.bat',xvlog_bin=binroot+'xvlog.bat',
        xelab_bin=binroot+'xelab.bat',xsim_bin=binroot+'xsim.bat',
        proposal_feedback=enabled,work_dir=output)
    stats=ROOT/'llm/router_stats.jsonl'
    before=len(stats.read_bytes()) if stats.exists() else 0
    start=time.monotonic()
    o=Orchestrator(cfg,output)
    exception=None
    try:
        result=o.run()
    except Exception as error:
        exception={'type':type(error).__name__,'message':str(error)}
        atomic_write_text(output/'study-exception.txt',traceback.format_exc())
        result={'status':'study_exception'}
    elapsed=time.monotonic()-start
    after=stats.read_bytes()[before:] if stats.exists() else b''
    (output/'study-router-stats.jsonl').write_bytes(after)
    independent=output/'study-independent'
    independent.mkdir()
    saved=output/'iterative_divider_core_best.v'
    passed=False
    independent_start=time.monotonic()
    if result.get('status')=='done':
        try:
            copied=independent/'winner.v';copied.write_bytes(saved.read_bytes())
            copied_tb=independent/'tb.v';copied_tb.write_bytes((STUDY/'tb.v').read_bytes())
            okay,error,kind=xsim_run([copied],copied_tb,'iterative_divider_core_tb',cfg,independent,timeout=90)
            raw=(independent/'sim_log.txt').read_text(errors='replace') if (independent/'sim_log.txt').is_file() else ''
            passed=okay is True and kind==FailureKind.DESIGN and re.search(r'(?m)^\s*TEST PASSED\s*$',raw) is not None and re.search(r'FAIL|watchdog|timeout|timed\s+out',raw,re.I) is None
            atomic_write_text(independent/'result.json',json.dumps({'ok':passed,'error':error,'failure_kind':kind.value,'winner_sha256':sha(saved),'copy_sha256':sha(copied)},indent=2))
        except Exception as error:
            exception={'type':type(error).__name__,'message':str(error),'scope':'independent'}
            atomic_write_text(independent/'study-exception.txt',traceback.format_exc())
    outcomes=[json.loads(p.read_text()) for p in sorted(output.glob('iter_*/proposal_outcome.json'))]
    candidates=[c for r in outcomes for c in r['candidates'] if c['status']!='duplicate_skipped']
    generated=[]
    for stage in output.glob('journal/*/completed.json'):
        data=json.loads(stage.read_text())
        if ':model:generator.generate:' in data['stage']:
            assert isinstance(data['result'],str)
            generated.append(data['result'])
    rawhashes=[hashlib.sha256(text.encode('utf-8')).hexdigest() for text in generated]
    hashes=[code_hash(text) for text in generated]
    verified={c['final_code_hash'] for c in candidates if c['status']=='measured'}
    rows=[json.loads(line) for line in after.splitlines()]
    names=('input_tokens','cached_input_tokens','output_tokens')
    known={name:sum(type((r.get('metadata',{}).get('usage') or {}).get(name)) is int for r in rows) for name in names}
    usage={name:sum((r.get('metadata',{}).get('usage') or {}).get(name) or 0 for r in rows) if known[name]==len(rows) else None for name in names}
    report={'pair':pair,'feedback':enabled,'status':result.get('status'),'independent_passed':passed,
        'generated':len(generated),'completed_outcome_candidates':len(candidates),
        'generated_without_completed_outcome':max(0,len(generated)-len(candidates)),
        'repeated_exact':len(rawhashes)-len(set(rawhashes)),
        'repeated_code':len(hashes)-len(set(hashes)),'distinct_measured_codes':len(verified),
        'accepted_improvements':sum(r['is_best'] for r in outcomes),
        'best_metrics':result.get('best_metrics'),'baseline_metrics':result.get('baseline_metrics'),
        'budget':json.loads((output/'budget.json').read_text()) if (output/'budget.json').exists() else None,
        'elapsed_seconds':elapsed,'independent_seconds':time.monotonic()-independent_start,
        'reported_usage':usage,'usage_known_calls':known,'provider_records':len(rows),'exception':exception,
        'models_observed':sorted({str(r.get('metadata',{}).get('model')) for r in rows}),
        'runtime_source_unchanged':identities()==plan['runtime_source']}
    atomic_write_text(output/'study-result.json',json.dumps(report,indent=2))
    assert report['runtime_source_unchanged']
    print(json.dumps(report),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');parser.add_argument('--index',type=int)
    args=parser.parse_args()
    if args.prepare: prepare()
    else: run(args.index)
