# PLAN — iteration 1

## Current state assessment

The current top is an 8-bit, every-cycle registered 4:1 mux with synchronous active-high reset. The verified baseline passes simulation and has 8 LUTs, 8 FFs, WNS 0.579 ns, and WHS 0.052 ns, so timing recovery is not the goal; `minimize_luts` requires a strict reduction below 8 LUTs while retaining all promotion gates. Top numeric latency is unknown, so no numeric `@latency` annotation is required.

## Hypothesis

Mapping each bit’s 4:1 selection onto the 7-series dedicated MUXF7/MUXF8 cascade may reduce LUT usage while preserving the registered output and reset behavior.

## Instruction for generator

Replace the `case (sel)` data-selection pattern with two MUXF7 stages per output bit, selected by `sel[0]`, feeding one MUXF8 stage selected by `sel[1]`. Keep `y` as the existing posedge-registered output and preserve its synchronous active-high reset to zero. Preserve all ports and cycle behavior; do not add a numeric latency annotation.