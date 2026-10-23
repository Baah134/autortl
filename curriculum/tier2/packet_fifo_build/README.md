# Packet-tagged synchronous FIFO experiment

A ready/valid build task with child `packet_fifo_core #(WIDTH=8,
DEPTH=3)` and fixed-eight-bit top `packet_fifo`. Each accepted word carries an
independent one-bit `last` marker. The mechanical wrapper binds child defaults;
it exposes no public top parameters. Physical measurements, when obtained,
apply only to the default **8 x 3** instance.

## Fixed behavior

- Supported positive integer experiment domain: WIDTH 1..16 and DEPTH 1..8.
- Accept and retire atomic `(data, last)` tuples. Preserve their order,
  multiplicity and all bits. A marker must remain attached to its original word.
- Output valid means nonempty; input ready is `(occupancy < DEPTH) || out_ready`.
  Full simultaneous retirement/capture is legal and leaves occupancy unchanged.
- Hold valid and both tuple fields stable during an output stall. Both output
  fields are unspecified while invalid.
- `last` is ordinary payload (`protocol: none`), not another handshake. This
  FIFO does not wait for a complete packet: beats without a marker are visible,
  and zero or consecutive markers are legal. Data cannot determine the marker.
- Synchronous active-high reset flushes the queue and dominates transfers at
  the rising edge. It does not change state between edges. An interrupted
  partial packet can be discarded; reset must not manufacture a final marker.
- No empty bypass. Earliest accepted-tuple retirement is the following edge:
  minimum accepted-transfer age one, with later retirement under backpressure.
- Explicit pointer wrap must handle non-power-of-two depths and DEPTH=1.

Resolved data `Port.width` is integer eight at defaults. The exact inferred
`interface_signature` retains symbolic `[WIDTH-1:0]` data boundaries and public
WIDTH/DEPTH defaults in that order. Last ports are unsigned scalar payloads.
The Python scoreboard oracle maps each accepted tuple to its eventual identical
output tuple; it is not an occupancy, scheduling or backpressure model. Examples
include identical data with different markers to expose accidental coupling.
The independent temporal checker supplies the scheduling evidence.

## Independent verification and admission

| Instance | WIDTH | DEPTH | DUT |
|---|---:|---:|---|
| Default | 8 | 3 | Mechanical top wrapper |
| Minimum | 1 | 1 | Explicit parameterized child |
| Legacy capacity | 8 | 2 | Explicit parameterized child |
| Power of two | 8 | 4 | Explicit parameterized child |
| Wide/non-power-of-two | 13 | 5 | Explicit parameterized child |
| Maximum corner | 16 | 8 | Explicit parameterized child |

The independent testbench maintains a queue of expected tuples and temporal checks
for capacity/readiness, no empty bypass, order, stalls, simultaneous transfers,
wraps and reset. Directed marker sequences must distinguish identical data with
opposite markers, consecutive markers, unmarked partial packets, marker stalls
and reset while occupied. Producers must hold pending tuples until acceptance.
Every selected checker must complete; an enclosing watchdog or a compile error
is not a behavioral mutant kill.

`qualification/reference.v` is a supervised packed-tuple ring-buffer control,
**never a model seed**. Qualification contains nineteen distinct source
mutations: thirteen adapted FIFO mutations and six marker-specific mutations.
These are not nineteen independent observable fault classes. In particular,
payload capture truncation and output truncation can expose the same lost high
bits. The capture mutation retains symbolic packed storage and its marker bit,
then masks the captured data to eight effective bits; it does not change the
declared physical memory width.

On October 22, 2026, live simulator admission produced all **20 expected
verdicts**: the control passed all six selected configurations, and each of the
nineteen mutants produced a concrete behavioral assertion failure. Compilation
errors, infrastructure failures and watchdog expiry were not counted as kills.
The fixture checkpoint also passed the complete **1,105-test** regression suite.
See the [retained admission evidence](../../../evidence/2026-10-22/packet-fifo-admission/)
for source identities and raw verdicts. Use generated golden verification
together with this independent trusted TB for subsequent model experiments.

## Evidence limits

This checkpoint establishes supervised fixture admission and regression
success. It establishes no generated-design success, routed PPA gain or held
tier. The selected matrix does not prove every WIDTH/DEPTH combination, formal
equivalence or a general packet protocol.
