# Tier5 exploration 01: the first run of every tier5 entry

Exploratory, not a curriculum verdict: `tools/explore.py --tier 5 --jobs 1
--model gpt-6-luna` ran each entry through `run.py build` from its typed
specification, without writing the curriculum history. Code: the main checkout
from f349d054 (tier5 merged) with the whole-design edit scope (71557e0e) merged
before the first entry started; later commits that afternoon (port attributes,
progress reasons, example-error wording) landed on disk while it ran. Every
acceptance used the entry's independent testbench, qualified in xsim against
ten planted faults (`tier5-qualification-01`).

| Entry | Built | Baseline | Best | Calls | Wall |
|---|---|---|---|---:|---:|
| uart_rx_fifo_build (UART 8N1 RX, 16x oversampling, FIFO, error counters; 100 MHz) | yes | 65 LUT, 55 FF, WNS -1.166 ns (missed timing) | **55 LUT, 59 FF, WNS +0.443 ns** | 16 | 29.8 min |
| fir16_sym_build (16-tap symmetric FIR, valid/ready; 150 MHz) | yes | 394 LUT, 7 DSP, WNS -10.770 ns | 165 LUT, 11 DSP, WNS -3.024 ns (not closed) | 15 | 45.1 min |
| axil_regs_build (AXI4-Lite slave, 8 registers; 100 MHz) | children yes, integration no: baseline_failed | — | — | 10 | 10.1 min |

## What the roles showed

- **Tier5 builds and optimizes.** The UART receiver with FIFO is three
  generated modules; its baseline missed 100 MHz, the roles recovered timing
  (+0.042 ns) and then made it smaller twice (70 → 66 → 55 LUT), each change
  inside the child modules: a registered FIFO head, bit/phase counters instead
  of a divide and modulo, and a shift register instead of indexed writes.
- **The 150 MHz FIR is the hardest target so far.** Two timing-progress steps
  cut the deficit from -10.770 to -3.024 ns (and LUTs from 394 to 165 by moving
  products into DSP slices), but timing is not closed within the budget.
- **AXI exposed a repair-feedback gap.** All three AXI children passed their
  own generated oracles, but the integrated design failed the independent
  testbench on five protocol rules. One rule (read data) repeated 32 times and
  filled the 15-line failure window, so the fixer never saw the four handshake
  rules and three repairs failed (taxonomy
  `repeated_failure_hides_other_rules`; failures are now reported once per
  kind with a count). The independent testbench did its job: no wrong design
  was accepted.

Per-entry role reports: `role-report-<entry>.md` (tools/role_report.py).
Simulator snapshots (xsim.dir) and Vivado scratch (.Xil) are not copied.
