# Generated packet FIFO attempt 01

Fresh build from1357a08; no supervised reference seed. Frozen typed spec,
generated golden transaction grader and independent temporal checker.
Budgets:3iterations/1candidate,16calls,25tool/35wallminutes,oneinfraretry.
Vivado2025.2,xc7a35tcpg236-1,100MHz,idealzero min/max I/O delays.

## Actual result

- Baseline15LUT/6FF: setup-0.946ns,hold+0.167ns; functionally correct,
  timing infeasible.
- Iter1 shiftqueue23LUT/29FF failedsetup-0.172ns. Bounded tool-knob trial
  closed timing at **23LUT/31FF,setup+0.078ns,hold+0.106ns**; review6/6ACCEPT.
- Iter2 repeated source and failed standard timing; RTLDoctor trial also
  failed setup. Rejected. Churn watchdog triggered a replan.
- Iter3 repeated source again. RTLDoctor produced feasible27LUT/30FF,
  +0.333/+0.115ns, correctly rejected for increased LUTs versus feasible23LUT.
  Replan did not enforce architectural diversity in this trial.
- Finalbestiter1,done,timing_closed=true,improvement_kind=timing_recovery.
  **13calls,769.639chargedtoolseconds,937.551elapsedseconds.**

This is timing recovery with higher area than the invalid15LUTbaseline;
no area savings are claimed. Physical metrics apply only to default8x3 top.

## Verification and retained limits

The first Python oracle had a SyntaxError and was rejected; attempt2 qualified.
Generated grader passed its control, missed readinessflip and detected global
stuckzero. Independent temporal grader detected that readiness fault.
Separate post-run measurement froze the completed generated grader and checked
prequalified source hashes: passingcontrol plus **all six named last-marker
faults detected by actual assertions**, with no missing/infra/watchdog evidence.
These six probes establish default-instance marker sensitivity, not exhaustive
coverage. The original qualification record is retained unchanged.

Exact savedwinner and declaredchild passed independent sixconfiguration TB.
Actual DONE replay exited0; temporary child/spec/Doctorreport changes each
rejected1,restored331hashes/fileset/budget with no newmodel/toolcharges.
This is completed-run verification, not proof of in-flight hard-kill recovery.
Measured/saved source differs only CRLF/LF; explicit identity link is retained.
Read-only source/report review found no blocker. Selectedmatrix is not
allparameter,formal,boardtiming or weakmodel robustness proof; no heldtier.

## Feature decision

Keep complementary graders, report-grounded plans, bounded Doctor and strict
promotion. Keep cache/source identities separate from tool-flow measurements.
Named marker probes found no missing sideband comparison, so no new scoreboard
engine or role is justified. Record weak architecture diversity after replan
for a controlled portfolio/feedback experiment rather than adding agents now.
Fullsuite1105passed; freshfulltier0 remains the main integration gate.
