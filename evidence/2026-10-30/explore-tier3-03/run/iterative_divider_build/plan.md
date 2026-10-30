# PLAN — iteration 3
## Current state assessment
Iteration 2 is the verified incumbent at 27 LUTs, 37 FFs, WNS 0.315 ns, and WHS 0.168 ns; it passes the behavioral and tool gates and meets timing. With both incumbent and candidate timing-feasible, iteration 3 must strictly reduce LUT use to improve the objective. The current core uses an up-counter that increments from zero and compares against `WIDTH - 1`.

## Hypothesis
Counting down from `WIDTH - 1` to zero may simplify the terminal-count logic and reduce LUT use while preserving the exact `WIDTH`-iteration schedule.

## Instruction for generator
In `iterative_divider_core`, change `iteration_count` from an up-counter to a down-counter: load `WIDTH - 1` on accepted capture, decrement on each busy compute edge, and finish when the pre-edge count is zero. Keep the existing arithmetic step, result registers, handshake and reset behavior unchanged; preserve the supported `WIDTH` range, including `WIDTH=1`. Retain the candidate only if all gates pass and routed LUT use is strictly below the 27-LUT incumbent.