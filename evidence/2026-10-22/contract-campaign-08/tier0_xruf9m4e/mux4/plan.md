# PLAN — iteration 1

## Current state assessment

The baseline passes simulation and meets setup and hold timing: 8 LUTs, 8 FFs, WNS 0.579 ns, and WHS 0.052 ns. The 8-bit registered output requires 8 FFs, and each bit’s 4:1 mux depends on six inputs (four data bits and two select bits), already fitting the one-LUT-per-bit floor. The objective is strictly fewer LUTs, so matching the baseline would not qualify as an improvement. Top numeric latency is unknown; preserve the observed registered behavior without adding an annotation requirement.

## Hypothesis

Expressing the 4:1 selection directly as a six-input Boolean mux may preserve the 8-LUT mapping, but cannot reduce LUTs below eight; accept only if routed evidence shows a strict reduction and all gates pass.

## Instruction for generator

Replace the `case (sel)` assignment to `y` with an equivalent direct 4:1 mux expression for each output bit, keeping `rst` as the synchronous active-high reset and preserving the existing output register. Keep the exact ports and one-cycle registered behavior; do not add a latency annotation. If synthesis still uses 8 LUTs, retain the baseline because it does not improve the `minimize_luts` objective.