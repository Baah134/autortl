# Supervised physical hold-fix command check

Runtime source: 61854c0. Vivado 2025.2, xc7a35tcpg236-1, 10 ns and ideal zero I/O
assumptions. Exact scripts, source, testbench and raw reports/logs are retained.
No model call. The independent mux TB passes. The flow executes
`phys_opt_design -hold_fix` after placement and before routing.

Synthesis report: WNS 3.546 ns, WHS -1.057 ns. Routed: WNS 0.579 ns,
WHS 0.059 ns, 18 LUTs/8 FFs. The standard prior mux flow used 8 LUTs/8 FFs
with routed WHS 0.052 ns.
The physical hold option incurs area here; it is a targeted repair candidate,
not a universal optimization. This is command and flow validation, not a full
Doctor invocation or a controlled causal estimate of this option alone.

The archived helper is the exact local command driver; it takes the checkout
path as argument, uses installed Windows tool paths and creates a new local
logs/physical-hold-fix-01 directory. It refuses to overwrite an existing run.
