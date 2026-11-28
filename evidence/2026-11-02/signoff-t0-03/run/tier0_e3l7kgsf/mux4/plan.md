# PLAN — iteration 1
## Current state assessment
The 8-bit registered 4:1 mux meets timing in the retained baseline: WNS is 0.579 ns and WHS is 0.052 ns, with 8 LUTs and 8 FFs. Each output bit already maps efficiently to a LUT6 for the four data inputs and two select bits; the synchronous reset can use the flip-flop’s dedicated reset input. The top’s numeric latency is unknown, so no numeric latency annotation is required; preserve its existing registered behavior.

## Hypothesis
The current mapping is likely already at the 8-LUT floor, but expressing the selection as an indexed mux may let Vivado retain one LUT6 per output bit and expose no resource increase.

## Instruction for generator
Replace the `case (sel)` data-selection branch with an indexed 8-bit slice of the packed `{d, c, b, a}` bus, using `sel` to select the slice; keep the existing clocked process and synchronous active-high reset unchanged. Preserve the exact one-cycle registered output behavior for all four select values. This is a low-confidence resource hypothesis: compare routed LUT and FF counts against 8 and 8, and retain only if all gates pass and LUT count decreases (or LUTs tie and FF count decreases).