# Tier6 rv32i_core_build: a RISC-V RV32I core built and optimized

Exploratory runs, not curriculum verdicts (`tools/explore.py --tier 6 --entries
rv32i_core_build --jobs 1 --model gpt-6-luna`), out of context at 100 MHz.

The design: a multi-cycle RV32I subset CPU (ALU and immediate ops, shifts,
LUI/AUIPC, JAL/JALR, all six branches, word LW/SW) split by the typed spec into
an instruction memory, a combinational decoder, a register file, a
combinational ALU, a data memory and a sequencer (six modules, 26 internal
connections). Every accepted step passed the independent testbench, which runs
four hand-assembled programs (ALU corner cases, Fibonacci and a sum loop, a
memory copy with aliasing, every branch taken and not taken with JAL/JALR
links) and 40 seeded random programs against its own ISA-level RV32I model,
checking every port before each clock edge; it was qualified in xsim against
ten faults.

| Run | Code | Baseline | Best (verified, timing met) | Notes |
|---|---|---|---|---|
| `explore-tier6-06` | 768c2fa2 | 2,093 LUT / 4,356 FF, +1.201 ns | **1,530 LUT / 3,325 FF, +0.916 ns** | Ended on the 40-minute tool budget after two iterations; iteration 2 below |
| `explore-tier6-08` | f47e4315 (30-minute synthesis limit, 180 tool minutes) | 2,141 LUT / 4,354 FF, +0.362 ns | 2,027 LUT / 4,350 FF, +0.569 ns | `done`: shared add/sub, one shift network, comparisons through the subtractor |

**The memory idea.** The spec makes reset clear the instruction memory, data
memory and registers, which forces them into about 4,300 flip-flops. In
`explore-tier6-06` iteration 2 the planner kept that behavior but replaced the
clearing loops with per-word valid bits (a word never written reads as zero),
which lets Vivado use distributed RAM: **868 LUT and 269 FF**, passing the
full ISA testbench, but 0.269 ns short of 100 MHz, so it was correctly not
promoted over the timing-met incumbent.

**Harness lessons** (taxonomy): `editable_unit_inventory_overflow` (the first
build crashed after meeting timing because the advisory module inventory of a
six-module unit was too long; it is now summarized) and
`fixed_synthesis_timeout_blocks_heavy_designs` (each implementation takes about
15 minutes, so the default exploration budget allowed two iterations).

Each run folder holds the run, its console and a role report.
