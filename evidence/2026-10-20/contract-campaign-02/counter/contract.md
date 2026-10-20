# CONTRACT
## Resource targets
- [ ] **Advisory goal:** Record the routed Slice LUT count from `utilization_routed.rpt` and whether it is below the baseline of 55 on `xc7a35tcpg236-1`; a reduction is not required.

## Timing targets
- [ ] The routed timing report for the 10.0 ns clock shows setup slack (WNS) ≥ 0 ns and hold slack (WHS) ≥ 0 ns.

## Correctness
- [ ] Preserve the top module’s ports, parameter defaults, and synchronous reset behavior; run the fixed testbench with `xvlog`, `xelab`, and `xsim -runall`, and require its verdict `TEST PASSED`.
- [ ] Use the fixed provided testbench, tools, device, and constraints without modification; the compile steps complete successfully.

## Code quality
- [ ] Synthesis of top module `counter` for `xc7a35tcpg236-1` reaches the retained script’s `SYNTH_COMPLETE` marker, with no `ERROR`-severity messages for `Designutils 20-1307`, `Synth 8-327`, or `Synth 8-3352`.

## Definition of done

All hard-gate checklist items pass with evidence from the fixed simulation and retained Vivado reports; report the routed LUT count as the advisory optimization result.