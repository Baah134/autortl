---
name: timing-closure
description: "Contract-preserving timing-closure guidance for AutoRTL."
---
# Timing Closure Playbook

Preserve the fixed contract: cycle latency, throughput, reset, parameter behavior
and registered outputs. An `@latency` change does not authorize adding a cycle.

## Diagnose before changing
Use routed setup WNS AND hold WHS, constrained endpoint coverage, path start/end,
logic levels, fanout and net delay. Missing metrics are unknown, not passing.
Depth and fanout are hints, not universal thresholds or guaranteed remedies.

## Bounded escalation
1. Harness-controlled retiming/physical optimization options may help; they have
   implementation risk and require the complete verification and timing gates.
2. Refactor combinational logic or replicate an equivalent existing driver;
   retime existing registers only if every observable cycle remains identical.
3. Replan within the contract or report that the target remains unmet.
Do not insert extra pipeline stages into fixed-latency designs. Balance data and
control only within existing stage boundaries. Do not rewrite @latency.

## Hold failures
A hold-only failure calls for harness-owned physical hold repair and review of
actual clock/I/O constraints. Never add RTL delay chains or extra cycles, relax
the target clock, or invent false paths. Recheck both setup and hold after any fix.
No option guarantees timing closure or a particular slack improvement.
