# Tier4 exploration 02: the same entries with editable children

Exploratory, not a curriculum verdict: `tools/explore.py --tier 4 --jobs 1
--model gpt-6-luna`, without writing the curriculum history. Code: the main
checkout from 71557e0e, where a build whose independent testbench instantiates
the top hands the optimizer every generated child and the top as one editable
unit (taxonomy `frozen_children_block_build_optimization`); fixes for port
attributes and progress reasons landed on disk while the first entry ran.
Compare with `explore-tier4-01`, where the children were frozen and no entry
improved.

| Entry | Baseline (Basys 3, 100 MHz) | Best | Accepted | Calls | Wall |
|---|---|---|---|---:|---:|
| spi_master_build | 25 LUT, 37 FF, WNS +0.317 ns | **19 LUT, 33 FF, WNS +0.354 ns** | 2 of 3 | 10 | 22.5 min |
| crc16_stream_build | 16 LUT, 34 FF, WNS +0.445 ns | 16 LUT (one candidate 16 LUT / 19 FF) | 0 of 3 | 11 | 18.2 min |
| rr_regfile_build | 42 LUT, 90 FF, WNS +0.554 ns | unchanged | 0 of 2 | 10 | 21.0 min |

## What the roles showed

- **Editable children unlock real gains.** Every proposal now targets the
  child logic. The SPI master shrank twice inside its core (received bits
  shifted straight into the response register; a counter sized from the
  parameter), 25 → 19 LUT with timing met.
- **Two vetoes became harness fixes.**
  - A third SPI candidate reached 17 LUT, verified and timing-met, but the
    evaluator failed it for a missing `// @latency` on the child, a rule the
    contract never states (taxonomy
    `evaluator_requires_child_latency_annotation`; the contract now says child
    annotations are never a criterion).
  - A CRC candidate kept 16 LUT and cut flip-flops 34 → 19, which plain
    `minimize_luts` discarded (taxonomy `equal_lut_ff_saving_discarded`; LUT
    ties now break on flip-flops).
- **The arbiter's two ideas were larger** (50 and 63 LUT) and were correctly
  rejected; 42 LUT for the register file is mostly the reset-required storage.

Per-entry role reports: `role-report-<entry>.md` (tools/role_report.py).
Simulator snapshots (xsim.dir) and Vivado scratch (.Xil) are not copied.
