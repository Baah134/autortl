# Generated FIFO05: accepted timing recovery

## Measured result

Source: 6f3fa7c, with runtime identical to 85e4fb8 and 1,074 passing tests.
All 55 runtime files match the published commit and remained unchanged.

| Stage | LUTs | FFs | Setup slack (ns) | Hold slack (ns) | Outcome |
|---|---:|---:|---:|---:|---|
| Baseline |13|6|-0.931|0.091|Failed timing |
| Iteration1 |21|26|-0.289|0.127|Rejected |
| Tool-only Doctor |21|27|-0.016|0.005|Not adopted |
| Iteration2 |24|14|0.013|0.027|Accepted timing recovery |
| Iteration3 before repair |—|—|-0.093|—|Failed setup |
| Final RTL Doctor repair |22|13|0.108|0.076|Accepted final winner |

The final repair registered an equivalent valid-state flag without adding an
observable cycle. It reduced LUT use by 8.33% from the first feasible candidate,
while using more area than the invalid 13 LUT baseline. Final review: 5/5 PASS.

Vivado 2025.2; xc7a35tcpg236-1; 100 MHz; ideal zero minimum/maximum I/O delays.
Physical metrics cover the fixed WIDTH8/DEPTH3 top. The selected child matrix
does not prove all WIDTH1..16/DEPTH1..8 combinations or board timing closure.

## Verification and execution

The first Python oracle had a syntax error and was repaired. The generated
payload grader passed 103 transactions and detected stuck-zero outputs, but
missed the readiness mutation. The independent six-case temporal matrix caught
that exact mutation. Their evidence is complementary; qualification is fault
sensitivity, not correctness proof. The original 13-fault admission is separate.

The exact saved top and declared children passed independent final simulation.
Actual CLI DONE reuse made no extra model or tool charges. Temporary changes to
the child, resolved specification and a protected Doctor report were rejected;
all 327 protected hashes, the run file set and budget matched after restoration.
This is completed-run reuse evidence, not an in-flight hard-kill recovery claim.

Optimization cost: 13 model calls, 856.39 charged tool seconds, 1041.5565 elapsed
seconds. Predeclared budget: 3 iterations, 1 candidate, 16 calls, 25 tool minutes,
35 wall minutes and 1 infrastructure retry. The final independent simulation is
separate validation outside that optimization budget. Model identity remains
unobserved; no controlled model-strength or efficiency claim follows.

## Archive

Original text artifacts are copied unchanged. Compiled trees and journal
artifact copies are omitted. Original absolute paths are provenance; this is
not a directly portable resumable run. The manifest covers all retained files,
nested manifests and the exact controlled-check helper.
