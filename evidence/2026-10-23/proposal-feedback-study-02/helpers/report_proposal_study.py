"""Summarize the predeclared six-trial study without silently omitting failures."""
import hashlib
import json
from pathlib import Path

ROOT=Path('C:/Users/prince.baah/Downloads/autortl-work')
STUDY=ROOT/'logs/proposal-feedback-study-02'
plan=json.loads((STUDY/'plan.json').read_text())
rows=[]
for pair,enabled in plan['order']:
    path=STUDY/f'pair{pair}-{"feedback" if enabled else "baseline"}'/'study-result.json'
    if not path.is_file():
        raise RuntimeError(f'Planned trial missing; comparison incomplete: {path}')
    row=json.loads(path.read_text());assert row['pair']==pair and row['feedback'] is enabled
    row['result_path']=str(path);row['result_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    stages=[json.loads(p.read_text())['stage'] for p in path.parent.glob('journal/*/completed.json')]
    plan_seed=None;stale=0;scored=0
    for evidence in sorted(path.parent.glob('iter_*/proposal_input.json')):
        iteration=int(evidence.parent.name.split('_')[1])
        current=json.loads(evidence.read_text())['seed_sha256']
        if any(s.startswith(f'iteration_{iteration}:model:planner.plan:') for s in stages): plan_seed=current
        if any(s.startswith(f'iteration_{iteration}:model:generator.generate:') for s in stages):
            if scored>=row['generated']: break
            stale+=plan_seed is not None and plan_seed!=current
            scored+=1
        restart=evidence.parent/'proposal_restart.json'
        if restart.is_file(): plan_seed=json.loads(restart.read_text())['seed_sha256']
    row['exploratory_stale_plan_seed_executions']=stale
    rows.append(row)


def summarize(enabled):
    selected=[r for r in rows if r['feedback'] is enabled]
    result={'trials':len(selected),'verified_completions':sum(r['status']=='done' and r['independent_passed'] and r['runtime_source_unchanged'] for r in selected),
        'generated':sum(r['generated'] for r in selected),'repeated_exact':sum(r['repeated_exact'] for r in selected),
        'repeated_code':sum(r['repeated_code'] for r in selected),'distinct_measured_code_sum':sum(r['distinct_measured_codes'] for r in selected),
        'accepted_improvements':sum(r['accepted_improvements'] for r in selected),
        'exploratory_stale_plan_seed_executions':sum(r['exploratory_stale_plan_seed_executions'] for r in selected),
        'best_luts':[r['best_metrics']['lut_used'] if r.get('best_metrics') else None for r in selected],
        'generated_without_completed_outcome':sum(r['generated_without_completed_outcome'] for r in selected)}
    for key,selector in [('model_calls',lambda r:(r.get('budget') or {}).get('llm_calls')),
        ('tool_seconds',lambda r:(r.get('budget') or {}).get('vivado_seconds')),
        ('wall_seconds',lambda r:r.get('elapsed_seconds')),
        ('input_tokens',lambda r:r['reported_usage'].get('input_tokens')),
        ('output_tokens',lambda r:r['reported_usage'].get('output_tokens')),
        ('cached_input_tokens',lambda r:r['reported_usage'].get('cached_input_tokens'))]:
        values=[selector(r) for r in selected]
        result[key]=sum(values) if all(type(v) in (int,float) for v in values) else None
    result['tokens']=result['input_tokens']+result['output_tokens'] if result['input_tokens'] is not None and result['output_tokens'] is not None else None
    return result


baseline,feedback=summarize(False),summarize(True)
ratios={key:feedback[key]/baseline[key] if baseline[key] is not None and feedback[key] is not None and baseline[key]>0 else None for key in ('model_calls','tool_seconds','wall_seconds','tokens')}
criteria={
    'all_six_trials_retained':len(rows)==6,
    'uninterrupted_comparison_available':all(r['status']=='done' for r in rows),
    'repetition_decreased':feedback['repeated_code']<baseline['repeated_code'],
    'completion_not_lower':feedback['verified_completions']>=baseline['verified_completions'],
    'no_unscored_generated_outcomes':baseline['generated_without_completed_outcome']==feedback['generated_without_completed_outcome']==0,
    'cost_known_and_within_predeclared_25pct':all(ratios[k] is not None and ratios[k]<=1.25 for k in ('tool_seconds','wall_seconds','tokens'))}
keep=all(criteria.values())
report={'schema_version':1,'scope':'Exploratory context-only feedback ablation; n=3pairs, actual CLI model identity unknown. Not a controlled model-strength or product comparison.',
    'plan_sha256':hashlib.sha256((STUDY/'plan.json').read_bytes()).hexdigest(),
    'baseline':baseline,'feedback':feedback,'feedback_over_baseline_ratios':ratios,'predeclared_criteria':criteria,
    'keep_context_by_default':keep,'decision':'Eligible for narrow pilot retention; no general benefit claim' if keep else 'No established repetition benefit; disable default advisory context and retain opt-in experiment/audit records. Interrupted trials and unknown usage prevent a complete efficacy comparison. Investigate stale plan/source binding separately.',
    'trials':rows,
    'limits':['Unknown underlying model identity','Three pairs and one curated design','All supplied independent checks retained; selected widths are not formal all-domain proof',
              'Reported tokens are counts, not monetary costs; cached tokens are a subset of input counts',
              'Baseline WIDTH1 source warning may remain despite actual Vivado PASS; no cross-tool portability claim',
              'Invalid study01 setup retained separately with lower-bound budget, excluded from paired efficacy counts',
              'Original pair2 baseline quota interruption is retained; supplemental same-runtime recovery is not substituted into the paired rows',
              'Host load and power state were uncontrolled; isolated synthetic staging tests overlapped part of pair3 baseline. Wall/tool costs are descriptive, not causal efficiency estimates']}
(STUDY/'comparison.json').write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
lines=['# Previous-proposal context: exploratory paired study','',report['scope'],'',
    '| Pair | Context | Status | Winner LUT / FF | Calls | Repeat proposals | Tool seconds | Wall seconds | Independent |',
    '|---|---|---|---|---|---|---|---|---|']
for row in sorted(rows,key=lambda r:(r['pair'],r['feedback'])):
    metrics=row.get('best_metrics') or {}
    lines.append(f"| {row['pair']} | {'on' if row['feedback'] else 'off'} | {row['status']} | {metrics.get('lut_used', 'unknown')} / {metrics.get('ff_used', 'unknown')} | {(row.get('budget') or {}).get('llm_calls')} | {row['repeated_code']} | {(row.get('budget') or {}).get('vivado_seconds',0):.3f} | {row['elapsed_seconds']:.3f} | {row['independent_passed']} |")
lines += ['',report['decision'],'','## Predeclared criteria','']+[f'- {key}: {value}' for key,value in criteria.items()]
lines += ['','## Limits','']+['- '+item for item in report['limits']]
(STUDY/'COMPARISON.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('trials','limits')}),flush=True)
