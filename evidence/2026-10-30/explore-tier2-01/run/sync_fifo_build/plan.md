# PLAN — iteration 2

## Current state assessment

Iteration 1 recovered timing feasibility and was accepted as a timing recovery: the verified incumbent uses 21 LUTs with WNS 0.063 ns and WHS 0.099 ns. Both designs must now be timing-feasible, and this LUT-minimization objective requires the next candidate to use strictly fewer than 21 LUTs while passing every fixed gate. The generation seed uses three payload registers and nested push/pop cases, alongside an instantiated `sync_fifo_core`; the prior routed reports show the earlier direct core output path missed setup timing.

## Hypothesis

A circular three-slot store with a registered head cache may reduce LUT use below 21 while keeping `out_data` off the read-address-to-output path and preserving timing feasibility.

## Instruction for generator

Replace the seed’s `head`/`middle`/`tail` shift-register update cases with a three-slot circular buffer, explicit wrap for its read and write pointers, occupancy tracking, and a registered head cache. Update the cache on an empty push and on a pop when another word becomes head; handle simultaneous pop/push at occupancy one by loading the incoming word, and retain the registered output, reset behavior, full simultaneous transfer, and exact one-cycle minimum age. Keep the required `sync_fifo_core` instantiation and the top’s `// @latency 1` annotation; preserve the interface and verify all gates, since the expected LUT reduction and routed timing are hypotheses until measured.