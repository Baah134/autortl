# PLAN — iteration 1
## Current state assessment
The incumbent is timing-feasible at 8 LUTs, 8 FFs, WNS 0.579 ns, and WHS 0.052 ns. The objective is strictly fewer LUTs; with one output register per data bit and a 4:1 mux per bit, the current 8 LUTs may already be near the mapping floor. The top latency is unknown, so preserve the existing registered output behavior without adding a numeric annotation.

## Hypothesis
Writing the mux as a balanced two-level tree may let Vivado map its select structure more efficiently and reduce LUT usage, though the current case may already achieve that mapping.

## Instruction for generator
Replace the `case (sel)` data selection with an explicit balanced 2:1 mux tree, first selecting between `a`/`b` and `c`/`d` using `sel[0]`, then selecting between those results using `sel[1]`. Keep the existing synchronous active-high reset to zero and the single clocked assignment to `y`; preserve all ports and cycle behavior. The proposed benefit is fewer than 8 routed LUTs; retain the candidate only if it passes every deterministic gate, has WNS and WHS at least zero, and strictly improves LUT count.