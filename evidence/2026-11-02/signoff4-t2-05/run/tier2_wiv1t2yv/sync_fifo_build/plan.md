# PLAN — iteration 2
## Current state assessment
Iteration 1’s shift-register queue improved setup WNS from −0.931 ns to −0.273 ns and hold slack to +0.124 ns, so it qualifies as timing progress but remains timing-infeasible. The advisory identifies `out_valid`’s occupancy-to-port logic path as the current critical path; the FIFO still needs to preserve its defined handshake and payload behavior.

## Hypothesis
Registering `out_valid` as a state bit updated alongside occupancy should remove the occupancy decode from the output path and improve routed setup slack, potentially closing timing without adding a cycle.

## Instruction for generator
In `sync_fifo_core`, replace the combinational `assign out_valid = (occupancy != 0)` with a resettable `valid_reg` that directly drives `out_valid`, updating it on push/pop so it always represents whether the post-edge occupancy is nonzero. Preserve synchronous active-high reset, full simultaneous pop/push behavior, empty no-bypass behavior, and valid stability during stalls; leave the top interface and `// @latency 1` unchanged. Keep the shift-register queue and its oldest-word output path for this iteration.