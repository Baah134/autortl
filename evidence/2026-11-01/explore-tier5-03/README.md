# Tier5 axil_regs_build on the out-of-context flow: built

Exploratory, not a curriculum verdict: `tools/explore.py --tier 5 --entries
axil_regs_build --jobs 1 --model gpt-6-luna` on the main checkout at 6a9c8ef8,
with the entry's new `implementation: out_of_context` (an AXI4-Lite slave is an
SoC block; its 165 ports cannot be placed on the package's 106 pins, which
explorations 01 and 02 hit).

| Iteration | Verdict | LUT | FF | WNS ns |
|---:|---|---:|---:|---:|
| 0 | built from the typed spec, three generated modules + top | **95** | 254 | **+5.441** |
| 1 | REJECT (larger) | 136 | 254 | +5.789 |
| 2 | REJECT (equal) | 95 | 254 | +5.441 |
| 3 | REJECT (equal) | 95 | 254 | +5.716 |

The generated design passes the independent AXI4-Lite testbench (qualified in
xsim against ten protocol faults) and meets 100 MHz out of context. It already
matches the best the optimizer reached from the hand-written reference in
`ooc-live-01` (96 LUT), and the 254 flip-flops are mostly the eight 32-bit
registers the contract requires. All three tier5 entries now build.

Role report: `role-report-axil_regs_build.md`.
