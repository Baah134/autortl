# Generated parameterized FIFO attempt01: functional pass, timing failure

Source **ffc15fc**. Four model calls;226.360chargedtoolseconds;284.528elapsed.
The generated oracle and child RTL passed on the first answer. Generated payload
and independent six-configuration tests passed and qualified. The same-byte
readiness mutation passed payload verification but asserted under the independent
matrix; coverage-gap.json retains exact source/TB identities and outcomes.

Baseline routed **13LUT/6FF**, setup slack **-0.931ns**, hold slack **0.091ns**.
**Timing is not closed. This is not a successful physical design or an accepted
improvement.** Vivado2025.2,xc7a35tcpg236-1,10ns,ideal zero min/max I/O delays.
The failing path runs from read pointer through inferred distributed memory to
out_data. No latency, clock or constraints were relaxed.

The candidate redeclared its frozen sync_fifo_core companion. The deterministic
compile guard rejected it before elaboration; no candidate PPA was measured.
The experiment completed retaining the invalid-timing baseline. The previous
CLI status done meant experiment completion, not timing success. The next source
adds explicit timing_closed and improvement_kind outcome fields.

The exact saved top and declared child independently passed all six matrix cases
again. DONE nominal replay and a controlled qualification-report tamper test
verified184selected identities unchanged after original bytes were restored;
no additional model or vendor calls occurred during those replay checks.
Do not resume this run across later runtime changes.

A controlled comparison proof uses the real13LUT failed baseline and a synthetic
14LUT feasible candidate to demonstrate the old area-first policy rejection.
That14LUT value is a unit policy example, not a physical measurement. This and
the repeated frozen-companion mistake motivated the recovery repairs recorded
in HARNESS_REVIEW. Later review also found a preexisting child-source omission
in DONE identity; later source fixes that rather than relabelling this trial.

Raw sources, graders/misses, reports, receipts and failed candidate remain.
Compiled simulator trees and journal artifact copies are omitted. Absolute paths
preserve provenance; this archive is not directly resumable. Original state
hash lists may reference omitted journal copies; archive-manifest.json hashes
the files actually retained here.
