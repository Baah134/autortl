---
name: fpga-methodology
description: "Contract-preserving fpga-methodology guidance for AutoRTL."
---
# FPGA Planning Checklist

Preserve the fixed contract: exact interface, clocks, cycle latency, registered
outputs, reset/enable priority, parameter behavior and arithmetic signedness.
Read supplied baseline source, testbench, constraints, device/tool identity and
measured reports. Do not invent missing facts or change @latency to authorize work.

1. Identify the objective and every hard gate: simulation, setup, hold, utilization
   integrity and any resource/power constraints.
2. Propose one concrete transformation with a falsifiable expected benefit and
   list the behavior it must preserve. Retiming uses existing registers only.
3. Check corner inputs, high bits, parameter bounds, overflow, stalls and reset.
4. Use independent reference checks and qualified mutants; preserve failed cases.
5. Compare post-route results under matching constraints. Record unknowns and
   tool/model costs. Infrastructure stops are not failed designs.
6. Retain only candidates that pass all gates and improve the stated objective.
A successful example does not establish general improvement or physical CDC safety.
