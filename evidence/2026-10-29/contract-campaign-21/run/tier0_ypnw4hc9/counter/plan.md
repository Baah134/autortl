# PLAN — iteration 1
## Current state assessment
The incumbent passes simulation and has routed setup WNS of 0.494 ns and hold WHS of 0.113 ns, so it is timing-feasible; the objective therefore requires a strict LUT reduction from 55 under the same device, clock and constraints. The seed’s dead `prev_count` register is already absent from the measured 37 FFs, so removing it again is unlikely to reduce area. Top numeric latency is unknown; preserve the existing cycle behavior without adding an annotation requirement.

## Hypothesis
Using the counter’s natural modulo wrap for its increment can remove the terminal-count-controlled data mux and reduce LUT use while preserving the overflow flag behavior.

## Instruction for generator
In the `enable` branch, replace the conditional `count == {WIDTH{1'b1}}` choice between zero and `count_next` with a direct `count <= count + 1'b1`; unsigned `WIDTH`-bit arithmetic wraps to zero at all ones. Keep the all-ones comparison to set `overflow` on an enabled wrap and clear it on an enabled non-wrap, preserving load clear, disabled hold, and reset priority. Leave the registered threshold flags and their comparisons unchanged, and preserve behavior for supported `WIDTH` and threshold parameter values.