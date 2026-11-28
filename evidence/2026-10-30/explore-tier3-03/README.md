# Tier3 exploration 03: editable children on the divider

Exploratory, not a curriculum verdict: `tools/explore.py --tier 3 --entries
iterative_divider_build uart_fifo_build --jobs 1 --model gpt-6-luna`, without
writing the curriculum history. Code: the main checkout from 71557e0e (the
whole-design edit scope merged), with the port-attribute and progress-reason
fixes of 4ed1f572 landing on disk while the first entry ran. Budgets as in
exploration 02.

| Entry | Built from prose | Baseline (Basys 3, 100 MHz) | Best | Calls | Wall |
|---|---|---|---|---:|---:|
| iterative_divider_build | yes | 33 LUT, 45 FF, WNS +0.315 ns | **27 LUT, 37 FF, WNS +0.315 ns** | 11 | 19.1 min |
| uart_fifo_build | spec yes, oracle no: module_failed | — | — | 7 | 3.2 min |

## What the roles showed

- **Editable children turn into real gains.** In exploration 02 the divider's
  core was frozen and all three proposals were no-ops. Here the build handed
  the optimizer the core and the top as one unit (verified by the independent
  testbench), and two of three proposals were accepted: merging the compare
  and subtract (33 → 29 LUT), then removing redundant output registers
  (27 LUT, 45 → 37 FF). Timing stayed met throughout.
- **The payload-tagging fix worked.** uart_fifo_build's spec passed lint after
  two repairs (exploration 02 failed lint four times).
- **Two new oracle-stage failures**, each now a taxonomy entry with a fix:
  the planner paired `fixed_latency` with valid/ready ports, found only when the
  oracle ran (`fixed_latency_handshake_found_at_oracle`; the spec-repair loop now
  runs the testbench generator's shape rules), and the oracle sandbox refused
  `state["count"] -= 1` (`golden_augmented_subscript_rejected`; simple
  subscripts are now accepted under the same guards).

Per-entry role reports: `role-report-<entry>.md` (tools/role_report.py).
Simulator snapshots (xsim.dir) and Vivado scratch (.Xil) are not copied.
