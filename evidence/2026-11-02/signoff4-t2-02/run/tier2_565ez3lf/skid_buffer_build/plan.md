# PLAN — iteration 2

## Current state assessment

Iteration 1 was accepted as a timing recovery: the incumbent meets setup and hold at WNS 0.146 ns and WHS 0.013 ns, using 11 LUTs and 19 FFs. Since it is timing-feasible, this iteration must strictly reduce LUTs to improve the `minimize_luts` objective; the prior indexed-storage output path has already been replaced with explicit head and tail registers.

## Hypothesis

Replacing the binary occupancy counter and separate valid register with head-valid and tail-valid state flags may reduce control LUTs while preserving the FIFO’s cycle behavior and timing feasibility.

## Instruction for generator

In `skid_buffer_core`, recode occupancy control as `head_valid` and `tail_valid` flags: drive `out_valid` from `head_valid`, `in_ready` as `!tail_valid || out_ready`, and derive push and pop from those signals. Update the flags for empty, one-entry, and full states, including simultaneous push/pop at each occupancy, while retaining the existing head/tail payload movement and synchronous reset behavior. Keep the top’s `// @latency 1` annotation and interface; compare routed LUTs, WNS, and WHS against the incumbent, since this proposal improves the objective only if it uses fewer LUTs and passes every gate.