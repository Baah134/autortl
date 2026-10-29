# PLAN — iteration 5
## Current state assessment
The verified incumbent is timing-feasible at 7 LUTs, 9 FFs, WNS 0.553 ns, and WHS 0.135 ns. Iterations 1–4 all failed to improve the LUT objective; counter narrowing, comparator rewrites, segmented carry logic, and complemented counting have already been tried. Top numeric latency is unknown, so no numeric annotation is required.

## Hypothesis
Using 7-series CARRY4 primitives for the 8-bit counter increment and duty comparison may reduce LUT use while preserving the current cycle behavior, though the LUT result must be measured.

## Instruction for generator
Replace the behavioral counter increment and `counter < {24'd0, duty}` comparison with explicit CARRY4 carry-chain logic, keeping the counter’s existing 32-bit declaration and terminal-at-255 wrap behavior. Keep the synchronous reset and registered `pwm_out`; compute its comparison from the current counter and duty on the same clock edge as before. Preserve the exact 0–255 phase sequence and test duty values 0 and 255, including reset behavior; retain the candidate only if all gates pass and routed LUT use is strictly below 7.