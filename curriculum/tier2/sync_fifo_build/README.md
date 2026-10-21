# Parameterized synchronous FIFO experiment

A ready/valid build task with child `sync_fifo_core #(WIDTH=8, DEPTH=3)` and
fixed-eight-bit top `sync_fifo`. The current mechanical wrapper explicitly binds
child defaults; it does not expose public top parameters. PPA measurements apply
only to the default **8 x 3** design, not to the testbench's matrix instances.

## Fixed behavior

- Positive integer experiment domain: WIDTH 1..16 and DEPTH 1..8.
- Synchronous active-high reset discards queued words at the rising edge and
  overrides transfers. Reset does not clear state between edges.
- Output valid means nonempty; input ready is `(occupancy < DEPTH) || out_ready`.
  Ready has a combinational path from downstream ready. Full simultaneous
  retirement/capture is supported and leaves occupancy unchanged.
- Preserve order, multiplicity, all payload bits, and stable valid/data while
  stalled. Invalid output data is unspecified.
- No empty bypass. A newly captured word becomes visible after capture and can
  transfer at the following edge: minimum accepted-transfer age one.
- Explicit wrap must handle non-power-of-two depths and DEPTH=1.

Resolved `Port.width` remains integer eight for default payloads. The existing
`interface_signature` schema records public WIDTH/DEPTH defaults and symbolic
`[WIDTH-1:0]` boundaries, without including the qualification implementation.
No strings replace numeric port widths. The Python scoreboard oracle maps one
accepted payload to its eventual identical output; it must not implement a
cycle-level occupancy/backpressure queue. Examples include rst=0 and accepted
transaction controls. RTL still implements the full temporal contract.

## Independent verification and admission

The trusted top TB contains six independent shift-queue checkers:

| Instance | WIDTH | DEPTH | DUT |
|---|---:|---:|---|
| Default | 8 | 3 | Mechanical top wrapper |
| Minimum | 1 | 1 | Explicit parameterized child |
| Legacy capacity | 8 | 2 | Explicit parameterized child |
| Power of two | 8 | 4 | Explicit parameterized child |
| Wide/non-power-of-two | 13 | 5 | Explicit parameterized child |
| Maximum corner | 16 | 8 | Explicit parameterized child |

The same child source is compiled once and instantiated at those settings.
Each checker independently verifies exact readiness/capacity, pre-capture
validity, full-width queue order, stalls, fill/drain, full simultaneous traffic,
repeated wraps, reset while occupied and deterministic random traffic. Producers
hold pending valid/data until acceptance. Per-case coverage and accounting must
pass; only the enclosing top emits a final verdict after every checker finishes.
A global watchdog prevents an unfinished case from passing. No DUT internals
are used as reference state.

`qualification/reference.v` is a ring-buffer control. `qualification/cases.py`
prepares that control plus thirteen distinct behavioral faults with unique
mutation targets. They cover hardcoded defaults, power-of-two-only wrap,
early/late full, full simultaneous admission, simultaneous count/retirement,
wide payload truncation, ordering, stall stability, empty bypass and async reset.
The bypass deliberately retains a false `@latency 1`: an annotation is not
behavioral proof. `materialize_cases(output)` exports the same case/file-hash
contract as the earlier skid-buffer fixture and launches no tools.

Before model generation, require the control to emit `TEST PASSED` and every
fault to produce a concrete behavioral assertion failure. Compile/elaboration
errors, watchdogs, missing verdicts and infrastructure failures are not mutant
kills. Preserve every failed admission attempt. Use generated + independent
verification together (`--generate-golden` and this trusted `--tb`). The
qualification reference is never configured as a generation seed.

## Evidence limits

Unit/schema/static checks do not establish simulator success. The six selected
configurations do not prove all WIDTH/DEPTH combinations or formal equivalence.
Adding this fixture establishes no routed metrics, optimization gain or held
tier; those require retained live evidence under a frozen harness revision.
