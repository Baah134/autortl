import hashlib,json,shutil
from pathlib import Path
ROOT=Path('C:/Users/prince.baah/Downloads/autortl-work')
WORK=Path('C:/Users/prince.baah/Documents/Codex/2026-10-15/hey')
RUN=ROOT/'logs/seed-binding-live-01';PROOF=ROOT/'logs/seed-binding-live-01-done-check'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
plan=read(RUN/'prelaunch-plan.json');result=read(RUN/'quota-recovery/result.json')
assert result['passed'] and result['original_blocked_result_unchanged'] and result['no_budget_reset']
assert result['binding_audit']['corrected_path_exercised'] and result['binding_audit']['binding_invariant_passed']
assert not result['binding_audit']['unbound_generated_inputs']
assert all(sha(ROOT/p)==h for p,h in plan['runtime_source'].items())
assert sha(Path(plan['seed_path']))==plan['seed_sha256'] and sha(Path(plan['testbench_path']))==plan['testbench_sha256']
assert sha(WORK/'work/validate_seed_binding_live.py')==plan['helper_sha256']
assert result['budget_after']['elapsed']>=result['budget_before']['elapsed']
assert read(RUN/'config.json')==read(RUN/'quota-recovery/before-config.json')
blocked=ROOT/'evidence/2026-10-24/seed-binding-quota-block-01'
assert (blocked/'run/validation-result.json').read_bytes()==(RUN/'validation-result.json').read_bytes()
assert all(sha(blocked/p)==h for p,h in read(blocked/'archive-manifest.json').items())
proof=read(PROOF/'result.json')
assert all(proof[k] for k in ('ok','all_restored_unchanged','file_set_unchanged','budget_and_router_stats_unchanged','no_new_model_or_tool_charges'))
assert proof['cli_exit_codes']['nominal']==0
assert all(proof['cli_exit_codes'][k]!=0 for k in ('feedback_input','feedback_outcome','prior_standard_source','prior_standard_script','plan_seed_binding'))
assert all(sha(Path(p))==h for p,h in proof['identities'].items())
out=ROOT/'evidence/2026-10-24/seed-binding-live-recovery-01'
out.mkdir(parents=True,exist_ok=False)
allowed={'.v','.sv','.py','.json','.jsonl','.log','.txt','.rpt','.md','.yaml','.xdc','.tcl'}
for source,prefix in ((RUN,'run'),(PROOF,'done-check')):
    for p in source.rglob('*'):
        rel=p.relative_to(source)
        if not p.is_file() or p.suffix not in allowed or any(x.lower() in ('artifacts','xsim.dir','.xil') for x in rel.parts):continue
        dest=out/prefix/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
for p in (WORK/'work/resume_seed_binding.py',WORK/'work/finalize_seed_binding_recovery.py',WORK/'work/validate_seed_binding_live.py',
          WORK/'work/check_seed_binding_done.py',WORK/'work/check_seed_audit_synthetic.py',
          WORK/'work/seed-audit-synthetic-result.json',Path(__file__),
          WORK/'outputs/AutoRTL-seed-binding-quota-recovery-01.txt',
          WORK/'outputs/AutoRTL-seed-binding-recovery-finalize-01.txt',
          WORK/'outputs/AutoRTL-seed-binding-done-check.txt'):
    shutil.copyfile(p,out/p.name)
(out/'README.md').write_text('''# Seed-bound planning: actual quota recovery validation

Runtime965251f; full regression1,340passed before launch. The original live run
hit quota before generation; its blocked result and pre-recovery evidence remain
separate. This archive records actual same-runtime CLI resume with cumulative
budgets, accepted-source refresh audit, independent exact winner and five
restored DONE tamper probes. No old result was replaced or budget reset.

The first recovery observer failed while printing Unicode after optimization
completed; its source/error/output remain retained. Original optimization CLI
exit and observer wall duration are unknown. Separate actual completed CLI reuse
returned0 without new charges; the independent simulation and DONE proof are
recorded separately. No optimization stage was repeated to finish reporting.

See run/quota-recovery/result.json and binding-audit.json for measured outcomes.
This is mechanism/recovery validation, not a controlled repetition or efficiency
comparison. Actual underlying model is unknown; original failed-call usage is
unknown. Independent simulation cost is separate from optimization cost. Selected
six widths are not formal proof for all values/parameters. Vivado2025.2,
xc7a35tcpg236-1,100MHz,ideal zero I/O; no board timing claim.
''',encoding='utf-8')
manifest={p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file()}
(out/'archive-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
assert all(sha(out/p)==h for p,h in manifest.items())
print(json.dumps({'files':len(manifest),'runtime_files_verified':len(plan['runtime_source']),
    'accepted_source_refreshes':result['binding_audit']['changed_seed_refreshes_exercised'],
    'protected_done_identities':proof['protected_identities'],'best_metrics':result['best_metrics']}))
