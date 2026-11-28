# PLAN — iteration 3
## Current state assessment
The verified incumbent is timing-feasible at 95 LUTs and 254 FFs, with WNS 5.441 ns and WHS 0.134 ns. Iterations 1 and 2 passed behavioral and timing checks but left LUT and FF counts unchanged, so neither improved `minimize_luts`; the read-selection rewrite and narrower stored write address should not be repeated. The top’s numeric latency is unknown, so no numeric top annotation is required.

## Hypothesis
Sharing decoded register and byte-lane write enables across CTRL, SCRATCH, and CONFIG may reduce duplicated write-control LUTs without adding state or changing any observable cycles.

## Instruction for generator
In `axil_regbank`, replace the separate `case (wr_idx)` branches and nested strobe checks for indices 0–2 with shared per-register select terms and per-byte write enables derived from `wr_en`, `wr_idx`, and `wr_strb`. Use those enables to update only the selected register bytes from the matching `wr_data` lanes, preserving each disabled byte. Keep reset values, IRQ and write-count logic, read behavior, handshakes, and all cycle behavior unchanged; this is an area hypothesis, so retain it only if the full gates pass and routed LUTs strictly decrease, or LUTs tie with fewer FFs.