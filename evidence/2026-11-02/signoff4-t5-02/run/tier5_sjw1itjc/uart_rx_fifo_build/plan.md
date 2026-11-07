# PLAN — iteration 3
## Current state assessment
The verified incumbent has 59 LUTs, 63 FFs, WNS 0.042 ns, and WHS 0.024 ns, so timing is feasible. With `minimize_luts`, this iteration must reduce LUTs to improve the incumbent; preserve the FIFO head-data register that addressed the earlier output timing path. The top’s numeric latency is unknown, so no numeric annotation is required.

## Hypothesis
Sharing a single factored UART majority-vote expression across the start, data, and stop decisions may reduce duplicated LUT logic without changing state or cycle behavior.

## Instruction for generator
In `uart_rx_core`, replace the three repeated pairwise-AND/OR majority expressions with one shared `majority_vote` wire, expressed as `(vote_a & vote_b) | ((vote_a | vote_b) & line_sample)`. Use that same value for start-bit validation, data-bit capture, and stop-bit validation. Preserve the existing vote sample edges, state transitions, data-bit ordering, registered outputs, reset behavior, and supported `OVERSAMPLE_DIV` timing.