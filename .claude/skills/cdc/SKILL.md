---
name: cdc
description: "Use when the design has multiple clock domains, async interfaces, wr_clk/rd_clk port pairs, or any signal crossing between clock domains. Simulation LIES about metastability — these patterns are mandatory."
---
# Clock Domain Crossing (CDC)

## The danger
A flop capturing a signal from another clock domain can go metastable.
**Simulation will not show this** — sim passes, silicon fails. CDC correctness
comes from structure, never from simulation results.

## Single-bit crossing: two-flop synchroniser
See snippets/sync_2ff.v. Rules:
- Only synchronise SLOW-CHANGING single bits (levels, not pulses).
- Never synchronise a multi-bit bus bit-by-bit (bits arrive in different cycles).

## Pulse crossing: toggle synchroniser
Convert the pulse to a level toggle, synchronise the toggle, edge-detect on the far side.

## Bus crossing: async FIFO (gray-coded pointers)
Any multi-bit data crossing uses an async FIFO with gray-coded read/write pointers, each pointer synchronised into the other domain with two flops. See snippets/async_fifo_skeleton.v.

## Handshake crossing
For occasional transfers: req/ack with both signals two-flop synchronised in their destination domains.

## Constraints
Cross-domain paths need `set_false_path` or `set_max_delay -datapath_only` on the synchroniser input — but ONLY on true synchroniser inputs, never to silence real same-domain paths.

## Spec-level law
The contract linter rejects any connection whose two ends live in different clock_domains without a CDC module between them. If you need a crossing, it must be its own module using these patterns.
