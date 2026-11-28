# PLAN — iteration 3
## Current state assessment
The verified incumbent closes setup and hold timing at 29 LUTs and 17 FFs. With `minimize_luts`, the candidate must pass every gate and use fewer than 29 LUTs to improve the objective; the one-hot occupancy and registered head outputs from the prior iterations are already in the seed.

## Hypothesis
Deriving `out_valid` directly from the empty-state bit will remove occupancy reduction logic and may reduce LUT usage while preserving FIFO behavior.

## Instruction for generator
In `packet_fifo_core`, replace `assign out_valid = |occupancy_state[DEPTH:1];` with `assign out_valid = !occupancy_state[0];`, relying on the initialized one-hot state and its shift-only updates. Keep the full-state ready logic, registered head outputs, pointers, reset behavior, and all handshake logic unchanged; preserve support for every specified `DEPTH` and `WIDTH`. This is a LUT-reduction hypothesis: retain the candidate only if routed metrics show fewer LUTs than the incumbent and all verification and timing gates pass.