# Controlled signed-boundary coverage correction

The original generated FIR grader passed the reference AND missed the signed12
truncation fault. Adding six alternating signed minimum/maximum accepted payloads
preserved the control pass and produced five actual out_data assertions against
the identical faulty RTL. Successful xvlog/xelab/xsim exits are retained.

The generated Python oracle, correct reference and faulty RTL were unchanged.
Original payload corner/example prefix and the exact100 seeded random inputs are
preserved.104 payloads become110; expected range expands from[-1703,1539] to
[-2169,2166]. Expectations are recomputed through the same accepted-history oracle.
No model/synthesis calls or changes to the completed original run/budget/statistics.
This is one targeted sensitivity improvement, not a new full27-fault grader score.

Before the six-line runtime insertion, the new pure regressions produced7failed/
4passed. After it,107focused tests passed7.00seconds. Both original failure and
passing scope, old code, exactpatch, integration mapping and228source snapshot
are retained. Fullregression and fresh runtime gates remain separate work.

See [original generated-grader audit](../signed-fir4-generated-audit-01/README.md)
and [original independently verified design](../generated-signed-fir4-attempt-01/README.md).
