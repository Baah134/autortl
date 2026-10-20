# CONTRACT
## Resource targets
- [ ] **Advisory optimization goal:** Seek a measured reduction in routed LUTs from the 55-LUT baseline on `xc7a35tcpg236-1`; report the actual routed LUT count. No minimum reduction is required.

## Timing targets
- [ ] Routed timing reports for `xc7a35tcpg236-1` at 10.000 ns show setup slack ≥ 0 ns and hold slack ≥ 0 ns.

## Correctness
- [ ] Pass the fixed testbench (`TEST PASSED`); preserve ports and parameter defaults as verified by the static/interface checks.
- [ ] Static/interface checks and compile succeed.
- [ ] Provide routed utilization and timing reports for `xc7a35tcpg236-1` at 10.000 ns, with setup and hold slack ≥ 0 ns; report the routed LUT count against the 55-LUT baseline.

## Code quality
- [ ] The candidate remains synthesizable RTL for the `counter` top module, with no inferred latches.

## Definition of done
The run is complete when the fixed provided testbench passes, static/interface checks and compilation succeed, routed utilization and timing reports are present for `xc7a35tcpg236-1` at 10.000 ns with setup and hold slack nonnegative, and the routed LUT count is reported against the 55-LUT baseline. Use the fixed harness, tools, device, and constraints without modification.