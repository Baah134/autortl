# FIFO03: timing failures and feedback omissions

Source49599b5;55runtimefile identities matched at launch;939fulltests passed.
Combined generated payload + independent temporal verification. Both graders
qualified; readiness mutation remains a payload miss and independent assertion.
Oracle initial state violated its restricted-literal protocol and was repaired
by the existing bounded retry. Generated child and integrated candidates passed
functional tests. No timing-closed winner or accepted resource gain is claimed.

Baseline:13LUT/6FF,setup-0.931ns/hold0.091ns. Iteration1 inline one-hot occupancy
still failed at-0.905ns. Doctor changed read selection, passed simulation, and
improved setup to-0.525ns, still infeasible; not adopted. Iteration2 one-hot
read/write pointers failed at-0.600ns. Its Doctor returned exactly unchanged
RTL, repeated tools, and exhausted the remaining deadline. Final status
budget_exhausted,best_iteration0; no saved final winner.10calls,
1200.654chargedtoolseconds,1349.068elapsedseconds. Same20tool/30wallminute
budgets and2iterations/1candidate; no counters were reset.

feedback-gap-proof.json records four observed omissions before corrections:
- Actual path is after report header preview; planner explicitly reports missing
  critical-path evidence although the complete routed report exists.
- The non-adopted-.525trial is absent from evaluation and next planning facts.
- Resolved build intent says invalid payload is unspecified, but optimization
  context omits that specification and planner invents empty-data preservation.
- Final surgery is exact unchanged source with unchanged physical flow.

Corrections are recorded in taxonomy/HARNESS_REVIEW before implementation:
bounded report-linked paths and resolved specs, not-adopted trial feedback,
and conservative exact-source-and-flow no-op deduplication. All defined behavior,
fixed testbench, exit, setup/hold and metric acceptance gates remain mandatory.

Vivado2025.2,xc7a35tcpg236-1,10ns,idealzero min/maxIO delays. Paths retain
provenance; compiled trees/journal artifact copies omitted. Not directly resumable.
