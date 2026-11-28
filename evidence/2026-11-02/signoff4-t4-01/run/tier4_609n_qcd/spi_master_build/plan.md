# PLAN — iteration 3
## Current state assessment
Iteration 1 is the verified best: 20 LUTs and 31 FFs, with setup and hold timing passing. Iteration 2’s parameter-sized `half_count` change was rejected because it did not improve the objective. The current seed still uses a 5-bit `edge_count`, although only values 0 through 15 are needed to schedule the 16 SCLK transitions; the top must retain `// @latency 33`.

## Hypothesis
Reducing `edge_count` to 4 bits should remove one flip-flop and may reduce counter logic while preserving transfer timing and behavior.

## Instruction for generator
Change the `edge_count` declaration and its reset and start values from 5 bits to 4 bits, and update the terminal comparison to match. Preserve the existing increment and edge scheduling; wrapping from 15 to 0 on the final transition is harmless because `busy` clears on that same edge and the next accepted command resets the counter. Preserve all supported `HALF_PERIOD` behavior, registered outputs, reset and handshake behavior, and the top’s `// @latency 33` annotation.