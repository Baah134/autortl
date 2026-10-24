# PLAN — iteration 3
## Current state assessment
Iteration 1 is the verified best at 33 LUTs with timing feasible (WNS 0.313 ns, WHS 0.095 ns); iteration 2 repeated the same RTL and was rejected for no strict LUT improvement. Try a distinct counter implementation while keeping the divider arithmetic and transaction behavior intact.

## Hypothesis
Loading the iteration counter with `WIDTH` and counting down to `1` may reduce LUT use by simplifying the completion comparison, with fewer than 33 routed LUTs as the measurable target.

## Instruction for generator
Change the up-counter pattern that initializes `iteration` to zero, increments it during `busy`, and completes at `WIDTH-1` into a down-counter loaded with `WIDTH` on request capture, decremented on each nonfinal busy cycle, and completing when it equals `1`. Preserve the existing `COUNT_WIDTH`, including behavior at `WIDTH=1`, and keep the arithmetic, state machine, reset, handshakes, registered outputs, and observable latency unchanged. Retain `// @latency 9`; promotion still requires every fixed verification and metric gate, nonnegative setup and hold slack, and strictly fewer than 33 routed LUTs.