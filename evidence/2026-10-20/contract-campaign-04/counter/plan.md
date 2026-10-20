# PLAN — iteration 1

## Current state assessment

The baseline passes the supplied simulation and has routed timing slack of WNS 0.494 ns and WHS 0.113 ns. It uses 55 LUTs, 37 FFs, no DSP48s, and no BRAM. The objective is a strict LUT reduction; the unused `prev_count` is already absent from the measured FF count, and the registered threshold flags are part of the fixed cycle behavior.

## Hypothesis

Replacing the explicit maximum-count wrap mux with the counter’s natural modulo increment may reduce LUT use while preserving the existing overflow behavior.

## Instruction for generator

In the enabled counting branch, remove the `count == {WIDTH{1'b1}}` conditional that selects between zero and `count_next`, and assign `count <= count + 1'b1` so the `WIDTH`-bit counter wraps naturally. Keep the all-ones comparison for setting `overflow`, and preserve its current reset, load, and disabled-cycle behavior. Leave the registered threshold flags and all ports and parameters unchanged.