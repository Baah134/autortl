---
name: xilinx-inference
description: "Contract-preserving xilinx-inference guidance for AutoRTL."
---
# Xilinx Inference Patterns

Preserve the fixed contract: cycle latency, reset, parameter behavior, registered
outputs, widths and signedness. Resource inference is a measured result, not a
guarantee. Confirm mapped primitives and post-route utilization in actual reports.

## DSP arithmetic
Write multiplication/addition plainly with explicit signedness and full required
product width. Existing input/output registers may map into DSP registers when
compatible. Do not add stages, truncate products or change reset/enable semantics
to force inference. Retiming existing registers must preserve all observable behavior.

## Memories
Registered reads may infer block RAM when device/port/reset requirements fit.
An asynchronous-read contract cannot be converted to registered reads to obtain
BRAM. Preserve read-during-write behavior and all supported depth/width values.
Attributes such as ram_style are requests; verify the actual implementation.

## SRL and carry logic
Shift registers can map into SRLs when reset/tap/enable requirements allow it.
Never remove a required reset to obtain an SRL. Plain arithmetic can use carry
chains; compare alternatives with the same constraints and verification gates.
