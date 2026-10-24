---
name: cdc
description: "Contract-preserving cdc guidance for AutoRTL."
---
# Clock Domain Crossing (CDC)

Preserve the fixed contract: clocks, cycle latency, resets, parameter behavior,
registered outputs and transfer protocol. CDC repair cannot add observable
cycles without an explicitly revised external specification.

## Structural checks
A two-flop synchronizer is for sufficiently stable single-bit levels, not arbitrary
pulses or independently synchronized bus bits. Pulse/toggle and request/ack
protocols require rate and reset assumptions. An async FIFO transfers buses
through storage with Gray-coded pointers synchronized into each domain.
See snippets/sync_2ff.v and snippets/async_fifo_skeleton.v.

The FIFO skeleton supports AW >= 2, DW >= 1 and depth 2**AW. It requires
coordinated reset of both domains while traffic is stopped; independent reset
recovery is not supported. Data output is registered on accepted reads, holds
otherwise, and is unspecified until the first accepted read after reset.
Full/empty flags are conservative because remote pointers pass through two
synchronizer stages. Full compares the CURRENT write Gray pointer to the
inverted-MSB synchronized read pointer, avoiding a combinational next-pointer loop.

## Limits and constraints
Simulation checks logical data/flag behavior; it does not prove metastability
safety or physical CDC correctness. Review synchronizer placement, Gray-bus skew,
reset release and actual crossing constraints for the target. Harness-owned
constraints must identify real CDC paths; never invent false paths to hide timing.
A recognized CDC module is a structural lint check, not a physical signoff.
