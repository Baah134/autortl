# Tier3 uart_fifo_build from prose: built and optimized

Exploratory, not a curriculum verdict: `tools/explore.py --tier 3 --entries
uart_fifo_build --jobs 1 --model gpt-6-luna` on the main checkout at eaf08ddd,
the first run after the entry got a fixed top interface and an independent
testbench qualified in xsim (10/10 mutants; tier3-uart-fifo-tb). Previous
attempts: `explore-tier3-uart-fifo`.

| Iteration | Verdict | LUT | FF | WNS ns |
|---:|---|---:|---:|---:|
| 0 | built from prose (3 planner spec repairs) | 170 | 117 | -1.188 |
| 1 | ACCEPT timing_progress | 120 | 89 | -0.827 |
| 2 | ACCEPT timing_recovery | 119 | 89 | +0.011 |
| 3 | ACCEPT objective | 112 | 85 | +0.058 |
| 4 | ACCEPT objective | **36** | **27** | **+0.179** |
| 5, 6 | REJECT (39 LUT, not smaller) | 39 | 26 | +0.072 |

The run stopped on its 40-minute tool budget (`budget_exhausted`, 29 model
calls) after 6 of 8 iterations, with the verified iteration-4 design retained.

## What the roles showed

- **Prose to a timing-met, much smaller design.** The planner decomposed the
  request into `byte_fifo` and `uart_tx` behind the fixed `uart_fifo` top; the
  generated baseline missed 100 MHz and the roles walked it to closure with
  the timing-progress and recovery rules, then shrank it.
- **The big step is a real FPGA optimization.** Iteration 4 replaced the
  FIFO's 32-bit `integer` read and write pointers with registers sized to the
  depth; Vivado then mapped the storage into distributed RAM (6 LUT as memory)
  instead of flip-flops and wide multiplexers: 112 → 36 LUT, 85 → 27 FF.
- Every accepted step passed the independent testbench (four concurrent cases,
  including a direct `uart_tx` at bit periods 2, 3 and 7).

Role report: `role-report-uart_fifo_build.md` (its summary row shows no LUT
figures because the run ended on budget; the per-iteration table is exact).
