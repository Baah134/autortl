# Out-of-context flow: first live run (tier5 AXI4-Lite reference)

The live check for the out-of-context implementation flow (branch `ooc-flow`,
merged at eaf08ddd; taxonomy `chip_top_flow_for_soc_block`). The tier5
`axil_regs` top has 165 I/O ports against the xc7a35tcpg236-1 package's 106
user I/O, so the chip-top flow cannot place it (`Place 30-415`).

```
python run.py optimize --design curriculum/tier5/axil_regs_build/qualification/reference.v
  --tb curriculum/tier5/axil_regs_build/axil_regs_tb.v --top axil_regs
  --implementation out_of_context --iterations 1 --model gpt-6-luna
  --target-part xc7a35tcpg236-1 (Vivado 2025.2 bat paths) --output-dir logs/ooc-live-01
```

| Iteration | LUT | FF | WNS ns | WHS ns | Verdict |
|---:|---:|---:|---:|---:|---|
| 0 (qualified reference) | 137 | 254 | +5.779 | +0.109 | baseline |
| 1 | **96** | 254 | +6.288 | — | ACCEPT (objective), independent testbench passed |

Checks the flow needed live, all confirmed in `run/iter_000`:
`synth_design -mode out_of_context` with no project, SYNTH_COMPLETE printed,
Bonded IOB 0 of 106, numeric routed WNS/WHS (422 endpoints), and the power,
design-analysis, register-to-register, methodology and QoR reports all written
with no ERROR or CRITICAL WARNING lines. In this mode WNS/WHS cover the routed
internal clocked paths; ports carry no pad delays (see docs/DESIGN.md,
"Implementation flow").
