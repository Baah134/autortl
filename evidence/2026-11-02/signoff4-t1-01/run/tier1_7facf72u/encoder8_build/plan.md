# PLAN — iteration 1

## Current state assessment

The incumbent uses 6 LUTs and 4 FFs and meets timing at WNS 0.528 ns and WHS 0.009 ns. It passes the supplied simulation and synthesis gates; there are no prior trial results. The objective is to reduce LUTs while preserving the known one-cycle registered behavior and synchronous active-high reset.

## Hypothesis

Replacing the serial priority chain with shared high-group-valid logic and explicit encoded-bit equations may reduce LUT use, though the 6-LUT baseline leaves limited room and the routed result must decide.

## Instruction for generator

In `priority_encoder8_core`, replace the descending `if/else` priority chain with explicit Boolean equations for the three encoded index bits, sharing prefix or group-valid terms where useful. Keep `valid_q` registered from `|request`, register all four outputs on the rising edge, and preserve synchronous reset to zero; keep the top-level `// @latency 1` annotation. Do not add pipeline stages or alter the interface, and rely on routed LUT/FF counts and all fixed verification gates to determine whether this change improves the incumbent.