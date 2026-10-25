import hashlib,json,shutil
from pathlib import Path
ROOT=Path('C:/Users/prince.baah/Downloads/autortl-work');WORK=Path('C:/Users/prince.baah/Documents/Codex/2026-10-15/hey/work')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((WORK/'top-timescale-source-freeze-01.json').read_text())
assert all(sha(ROOT/p)==h for p,h in old.items())
for name in ('generated-elastic-dot4-attempt-01','elastic-dot4-admission-attempt-02'):
    archive=ROOT/'evidence/2026-10-25'/name
    assert all(sha(archive/p)==h for p,h in json.loads((archive/'archive-manifest.json').read_text()).items())
p=ROOT/'data/taxonomy.yaml';text=p.read_text(encoding='utf-8');marker='\nmethodology:\n'
assert text.count(marker)==1 and 'invalid_golden_api_prompt:' not in text
p.write_text(text.replace(marker,'''
  invalid_golden_api_prompt:
    meaning: "The golden prompt showed an invalid Python return annotation and the model copied it into an oracle"
    repair: "Provide an executable unannotated API scaffold and regression-test it against the unchanged restricted interpreter"
  undocumented_golden_language_subset:
    meaning: "Oracle repair used f-strings accepted by general Python but rejected by the restricted execution policy"
    repair: "Expose current supported builtins and methods in the prompt, use literal port names, and preserve rejection of unsupported syntax"
  uncheckpointed_active_exit_walltime:
    meaning: "A clean failed run returned after a completed model call without persisting its final active wall time"
    repair: "Checkpoint active dispatch exits with the existing atomic save; preserve charge counts and keep completed reuse/input guards outside the checkpoint"
'''+marker),encoding='utf-8')
groups={
 'golden-prompt-stage':['autortl/prompts.py','autortl/roles.py','tests/test_golden_prompt.py'],
 'budget-final-stage':['autortl/budget.py','autortl/fsm.py','tests/test_budget_final_checkpoint.py'],
 'elastic-dot4-tests-stage':['tests/test_elastic_dot4_fixture.py']+['curriculum/tier3/elastic_dot4_build/'+n for n in
    ('design_spec.json','meta.yaml','elastic_dot4_tb.v','qualification/reference.v','qualification/cases.py','README.md')],
}
names=[n for items in groups.values() for n in items];assert len(names)==len(set(names))==13
receipt={}
for stage,items in groups.items():
    for name in items:
        src=WORK/stage/name;p=ROOT/name;assert src.is_file()
        receipt[name]={'before':sha(p) if p.exists() else None,'after':sha(src),'stage':stage}
        p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,p)
assert sha(ROOT/'autortl/golden_worker.py')==old['autortl/golden_worker.py']
assert sha(ROOT/'llm/client.py')==old['llm/client.py']
for name,key in [('design_spec.json','spec_sha256'),('elastic_dot4_tb.v','tb_sha256')]:
    before=json.loads((ROOT/'logs/build-elastic-dot4-01-prelaunch.json').read_text())[key]
    assert sha(ROOT/'curriculum/tier3/elastic_dot4_build'/name)==before
(WORK/'elastic-fixes-integration.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps({'applied':len(names)+1,'oracle_policy_unchanged':True,'design_spec_and_TB_byteidentical':True,'gates':'full regression, fresh build02, final tier0'}))
