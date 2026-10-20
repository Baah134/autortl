---
name: vivado-messages
description: "Contract-preserving vivado-messages guidance for AutoRTL."
---
# Vivado Message Diagnosis

Preserve the fixed contract: cycle latency, reset, parameter behavior, registered
outputs, exact interfaces and arithmetic widths. Repairs cannot amend @latency.
Use the actual message ID, full context and tool version; descriptions/IDs can
vary. The curated data/taxonomy.yaml is the machine-facing classification.

## Repair process
Read compile/elaboration logs for wrapper failures, then match module/port names,
widths and parameters to the contract. For latch diagnostics, complete
combinational assignments with defaults. For multiple drivers, establish one
owner while preserving reset/enable priority. Do not blindly tie unconnected
ports low; inspect intended connectivity and behavior.
Missing clocks require inspection of the actual clock ports and harness-owned
constraints, not renaming an interface to make a diagnostic disappear.
Unknown IDs remain evidence for review rather than invented authoritative meanings.

## Boundary rules
Never demote/suppress messages, weaken constraints or alter testbench expectations.
Infrastructure (license, missing tool, locks, timeout/provider failure) is distinct
from RTL failure. Preserve RTL and completed evidence when infrastructure blocks.
