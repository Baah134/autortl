"""Integrate only reviewed staged code after preserving the old full audit."""
import hashlib,json,shutil
from pathlib import Path
R=Path('C:/Users/prince.baah/Downloads/autortl-work');W=Path(__file__).resolve().parent
S=W/'fir4-signed-corners-stage';A=R/'evidence/2026-10-26/signed-fir4-generated-audit-01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
old=read(W/'signed-fir4-source-freeze-01.json');assert len(old)==227 and all(sha(R/p)==h for p,h in old.items())
assert all(sha(A/p)==h for p,h in read(A/'archive-manifest.json').items())
audit=read(A/'audit/result.json');assert audit['control_passed'] and audit['executed_cases']==28 and audit['detected']==18 and audit['missed']==9 and audit['ungraded']==0
assert 'truncate12' in audit['missed_names'] and all(audit['integrity'].values())
focus=read(S/'focused-tests-result.json');assert focus['exit_code']==0 and focus['passed']==107 and focus['old_source227']==old
assert sha(S/'focused-tests.txt')==focus['focused_log_sha256']
assert sha(S/'old-regression.txt')==focus['old_regression_log_sha256']
changes={**{p:v['staged_sha256'] for p,v in focus['changes'].items()},**focus['new_files']}
assert set(changes)=={'autortl/tbgen.py','tests/test_tbgen_signed_corners.py'}
assert all(sha(S/p)==h for p,h in changes.items())
old_text=(R/'autortl/tbgen.py').read_text(encoding='utf-8')
insertion='''        if any(p.signed for p in inputs):
            # Preserve this temporal burst, including repeated tuples: signed
            # stateful arithmetic needs consecutive extrema, not just a set.
            for high in (False, True) * 3:
                stimulus.append({p.name: ((1 << (p.width-1))-1 if high else 1 << (p.width-1))
                                 if p.signed else 0 for p in inputs})
'''
anchor='        if len(stimulus) + n_random + reset_steps > 10000:\n'
assert old_text.count(anchor)==1
assert (S/'autortl/tbgen.py').read_text(encoding='utf-8')==old_text.replace(anchor,insertion+anchor)
# Taxonomy lands BEFORE the runtime change, without altering strict verdicts.
p=R/'data/taxonomy.yaml';text=p.read_text(encoding='utf-8');assert '  signed_extrema_trace_gap:' not in text
entry='''  signed_extrema_trace_gap:
    meaning: "Generated signed accepted-transaction inputs omitted a boundary sequence and missed a compiling 12-bit truncation fault in a 13-bit FIR result"
    repair: "Add a bounded signed minimum/maximum payload burst before the unchanged random tail; preserve oracle semantics, driver ownership, strict verdicts and reset-inclusive step limits"

'''
assert text.count('\nmethodology:\n')==1;p.write_text(text.replace('\nmethodology:\n','\n'+entry+'methodology:\n'),encoding='utf-8')
for p in changes:shutil.copyfile(S/p,R/p);assert sha(R/p)==changes[p]
# Documentation-only correction to the qualified fixture; admitted spec/TB unchanged.
p=R/'curriculum/tier3/signed_fir4_build/README.md';text=p.read_text(encoding='utf-8')
text=text.replace('# Signed FIR4 stream: isolated admission proposal','# Signed FIR4 stream')
text=text.replace('`pure-validation.json` records structural checks only.', '[Archived pure-validation.json](../../../evidence/2026-10-25/signed-fir4-admission-attempt-01/fixture/pure-validation.json) records structural checks only.')
p.write_text(text,encoding='utf-8')
p=R/'docs/GOLDEN_VERIFICATION.md';text=p.read_text(encoding='utf-8');anchor='## Independent authority and limits\n'
section='''## Signed boundary sequences

Scoreboard modules with signed data inputs receive six alternating minimum and
maximum signed payloads after the original corners and eligible example payloads,
before the unchanged seeded random input sequence. These are accepted transactions,
not a clock schedule. Unsigned data inputs are zero during this burst; the driver
continues to own reset, valid and ready. Values stay masked to their declared widths.

Consecutive extrema exercise arithmetic state that isolated corner values can miss.
For the four-tap FIR, they reach both exact signed13 bounds, 2166 and -2169.
The oracle computes expectations through the full sequence, including its history.
Intentional repeated payloads remain in the sequence. The 10000-step limit includes
the reset prefix, examples, signed burst and random inputs. Fixed-latency and
unsigned-only stimulus sequences retain their previous behavior.

This bounded burst is not exhaustive state, sign-combination or reset coverage.
Keep qualified independent checks for contract-specific timing and reset behavior.

'''
assert text.count(anchor)==1;p.write_text(text.replace(anchor,section+anchor),encoding='utf-8')
p=R/'docs/DESIGN.md';text=p.read_text(encoding='utf-8');anchor='   Three existing corners and the seeded random tail are preserved.'
assert anchor in text;text=text.replace(anchor,anchor+' Signed-data scoreboard modules also receive six alternating\n   minimum/maximum accepted payloads between examples and the random tail, with\n   unsigned payloads zero and no change to driver scheduling or oracle semantics.',1);p.write_text(text,encoding='utf-8')
allowed={'autortl/tbgen.py','data/taxonomy.yaml','curriculum/tier3/signed_fir4_build/README.md'}
assert all(p in allowed or sha(R/p)==h for p,h in old.items())
receipt={'old_source227':old,'old_audit_archive_files':287,'old_audit':'18/27 detected;9missed;0ungraded',
         'review':'Coordinator verified exact six-line insertion, real restricted-oracle extrema and preserved modes/prefix/random tail/count guards',
         'staged_focus_passed':107,'stage_changes':changes,'canonical_changed_existing':{p:{'old_sha256':old[p],'new_sha256':sha(R/p)} for p in sorted(allowed)},
         'new_tests':focus['new_files'],'admitted_spec_TB_reference_faults_unchanged':True,'taxonomy_before_runtime':True,
         'scope':'Signed accepted payload coverage only; no driver/oracle/API/role/budget changes'}
(W/'fir4-signed-corners-integration.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps({'changed_existing':sorted(allowed),'new_tests':list(focus['new_files']),'staged_focus':107,'old_audit_preserved':True}))
