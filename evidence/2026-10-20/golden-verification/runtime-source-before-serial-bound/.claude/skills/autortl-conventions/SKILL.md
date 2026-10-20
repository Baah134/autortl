---
name: autortl-conventions
description: "Contract-preserving autortl-conventions guidance for AutoRTL."
---
# AutoRTL Conventions (LAW — always in force)

## Fixed contract
The contract is law. Preserve exact module/port names, widths, signedness,
parameter behavior over every supported value, reset kind/polarity/priority,
enable/hold behavior, cycle latency, throughput and registered outputs.
Use the supplied clock names; do not invent or rename clocks.
When the contract supplies a known numeric latency, declare `// @latency N`
equal to it. For an existing source with no annotation, declared latency is
unknown: preserve its exact observable cycle behavior and do not invent a
numeric annotation. Unknown does not mean zero or combinational. Typed builds
require an explicit numeric latency.
Changing that comment does not authorize changing behavior. If an architecture
cannot meet this contract, report the limitation and request replanning; never
amend it to pass a test. Retiming existing registers is allowed only when all
observable behavior remains identical.

## Output and code boundaries
Return generated RTL in exactly one verilog fence, golden Python in one python
fence. Put quoted reference/testbench material in text fences. Follow the role's
requested format for reviews/specifications; do not emit replacement RTL there.
LLM output belongs only in .v/.py files. Harness templates own Tcl, shell and
paths. Never propose message suppression, altered clocks or relaxed constraints.

## Coding rules
One driver per signal. Assign combinational defaults before branches.
Use nonblocking sequential assignments. Reset behavior follows the contract,
including data registers when specified; never remove a required reset.
No synthesis initial blocks. Preserve high bits, overflow and signed arithmetic.
Vivado severities may be promoted to ERROR, never demoted or suppressed.
Simulation, setup, hold, metric integrity and independent reference gates all
remain mandatory. Infrastructure failures are not design failures.
