# CONTRACT
## Resource targets
- [ ] **Hard gate:** The routed utilization report identifies design `mux4`, device `xc7a35tcpg236-1`, and Routed state, and provides readable used counts for LUTs, flip-flops, DSP48s, and BRAMs; metric integrity passes.
- [ ] **Advisory goal:** Seek fewer LUTs than the baseline of 8; record the measured routed LUT count. No minimum reduction is required.

## Timing targets
- [ ] **Hard gate:** At the fixed 10.000 ns clock period, routed setup slack and hold slack are both nonnegative.

## Correctness
- [ ] **Hard gate:** Preserve the ports, active-high synchronous reset to zero, and one-cycle behavior mapping `sel` values 0–3 to `a`, `b`, `c`, and `d`.
- [ ] **Hard gate:** The provided testbench simulation passes using the fixed `xvlog`, `xelab`, and `xsim -runall` flow, with verdict `TEST PASSED`.

## Code quality
- [ ] **Hard gate:** The provided static/interface checks pass.
- [ ] **Hard gate:** Compilation and synthesis pass for top module `mux4` on `xc7a35tcpg236-1`, with no inferred latches.

## Definition of done

Complete when the hard gates pass using the provided harness and fixed constraints, with routed resource and timing evidence available; report the LUT optimization result against the 8-LUT baseline.