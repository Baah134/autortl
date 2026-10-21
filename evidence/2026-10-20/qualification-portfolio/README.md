# Bounded fault qualification and typed build infrastructure outcomes

A real readiness mutation passed a generated payload grader while an independent
capacity grader detected it. The harness retains that miss and probes at most
three fixed faults: original operator/increment mutation, interface-faithful
stuck-zero outputs, and stuck-one outputs. The testbench never changes. Control
must pass; qualification requires raw assertion detail and TEST FAILED for one
fault. All misses remain explicit coverage limits. This is minimum non-vacuity
evidence, not proof that every fault is detectable or that a generated oracle is
correct. The independent queue TB remains mandatory for exact capacity/timing.

INFRA/UNKNOWN stops immediately without trying a different fault or repairing
RTL. Public build_blocked summaries preserve kind, diagnostic, stage and TB.
Missing/watchdog/contradictory logs never count as a detected fault. Constant-zero
functions can reach the all-ones probe; symbolic/signed/packed interfaces remain
unchanged. Reports retain source/TB/raw-log hashes and ordered outcomes.

Focused suites:41portfolio/interface tests,27flow/build/recovery tests, then54
combined tests including non-ASCII candidate evidence/trusted-TB adaptation.
Fullsuite05: **794 passed in4377.09s**. Windows recorded battery-triggered system
sleep during this run, so its duration is not a performance measurement. A fresh
awake full suite is recorded separately. No failed tests were regraded.

The second streaming trial exercised the exact missed-primary/observed-zero
sequence in real simulation; its independent TB detected the readiness fault.
Battery sleep later exhausted its frozen tool/wall budgets before physical
measurement. That interruption is separate infrastructure evidence. The third
fresh run uses the same source on AC power with a temporary system-awake request.
No old budgets were reset and no run was resumed across changed runtime source.

Awake repeat on identical source: **794 passed in237.82s** (full-suite-794-awake.txt).
