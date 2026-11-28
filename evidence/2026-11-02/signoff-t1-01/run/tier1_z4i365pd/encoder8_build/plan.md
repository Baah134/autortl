# PLAN — iteration 1

## Current state assessment

The incumbent uses 6 LUTs and 4 FFs, with routed WNS 0.528 ns and WHS 0.009 ns, so it meets timing and this iteration must improve the `minimize_luts` objective to replace it. There are no reported register-to-register timing paths; the chip-top timing results include I/O pad delay. No prior proposals or evaluations are available.

## Hypothesis

Replacing the serial `if/else` priority chain with factored upper/lower group predicates may reduce the encoder’s LUT count while preserving the existing timing-feasible registered interface.

## Instruction for generator

In `priority_encoder8_core`, replace the descending `if/else` chain with explicit upper- and lower-nibble nonzero predicates and factored Boolean equations for the three index bits; derive `valid` from the request nonzero predicate. Keep `index` and `valid` registered on `posedge clk`, with synchronous active-high reset to zero, and retain the top-level `// @latency 1` annotation. Preserve highest-set-bit priority, zero-request outputs, and output holds between rising edges; assess the candidate against the incumbent’s 6 LUTs and timing gates.