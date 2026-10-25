---
name: testbench-craft
description: "Contract-preserving testbench-craft guidance for AutoRTL."
---
# Independent Testbench Craft

Use an independent behavioral reference; never derive expected values from DUT
outputs or internal state. Preserve the fixed contract's cycle latency,
registered outputs, reset/enable priority and parameter behavior.
Drive away from sampling edges and check after nonblocking updates. Use !== so
unknowns fail whenever the contract defines a value. Check reset assertion and
release at their specified edges; there is no unconditional warmup that can hide
specified reset or first-result failures. Unspecified startup values may be
excluded explicitly, without discarding required observations.

For fixed latency, compare at the exact required cycle. For valid/ready, record
accepted input/output beats and check ordering, values, stalls, throughput and
any bounded latency requirement. A scoreboard does not waive timing behavior.
Exercise boundary values, high bits, wrap, back-to-back traffic, reset and stalls.
Print TEST PASSED only after all required checks; otherwise TEST FAILED with
mismatch evidence. Add a watchdog and qualify the oracle with behavioral mutants
that compile and fail assertions. Compile failures are not mutant detections.
