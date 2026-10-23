# Divider admission attempt02 — passed

Correct control passed all six selected widths: default8 wrapper and explicit
children1,2,4,13,16. All20 named source mutants triggered actual behavioral
assertions; compile errors, infrastructure failures and watchdogs are not kills.
Full regression: **1,180 passed in429.28seconds**. Integrated focus:107passed7.81s.
All192 frozen identities matched through recovery and archiving.

Attempt01 was rejected because reset with ready high allowed normal retirement
to hide ignored reset. Its original failed evidence is retained separately at
../../2026-10-22/divider-admission-attempt-01/. The correction keeps that case
and adds a held-result reset with ready low, a mandatory reset_stalled_result
coverage counter, and omission regressions. The previously missed fault now
fails actual assertions. Reference, specification and every mutant source are
unchanged. This is fresh qualification, never retroactive promotion.

The independently authored checker covers exact WIDTH-step availability,
WIDTH+1 minimum transfer age, busy/retirement boundaries, atomic quotient and
remainder, stalls, divide-by-zero semantics, input capture, reset phases,
exhaustive small widths and bounded deterministic larger-width cases.

Vivado2025.2 xvlog/xelab/xsim, raw sources/verdicts retained. This establishes
selected-width fixture admission, not generated-design success, routed PPA,
full-domain/formal proof or physical iterative structure. Supervised reference
remains qualification-only, never a model seed. Scalar latency9 is default8 only.
