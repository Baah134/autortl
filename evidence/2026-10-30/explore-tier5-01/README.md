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
- **AXI exposed a flow gap, not a design bug.** All three AXI children passed
  their own generated oracles and the integrated baseline **passed the
  independent testbench** (journal stage `baseline:tool:xsim_run:0`). The
  routed flow then failed because the 165-port top does not fit the package's
  106 user I/O pins (`Place 30-415`). Triage called that a design error, so a
  correct design went to the fixer three times and the "repairs" broke it;
  the five failing testbench rules seen later belong to those repairs
  (taxonomy `io_overutilization_sent_to_fixer`; an AXI4-Lite slave is an SoC
  block and needs an out-of-context flow, `chip_top_flow_for_soc_block`).
  The same review found that one repeated rule could fill the fixer's 15-line
  failure window (`repeated_failure_hides_other_rules`; failures are now
  reported once per kind with a count). No wrong design was accepted.
  *Corrected on 2026-11-01: an earlier version of this note said the baseline
  failed the testbench.*

Per-entry role reports: `role-report-<entry>.md` (tools/role_report.py).
Simulator snapshots (xsim.dir) and Vivado scratch (.Xil) are not copied.
