# First combined streaming build: stopped at qualification

No completed build, physical result or optimization gain is claimed.

At the runtime later published with combined verification, the Codex-generated
Python payload oracle qualified and generatedRTL passed both the generated unit
TB and independent893-cycle queueTB. Generation used two model calls; no reference
implementation was supplied as a seed. The source is a shift-register queue.

The selected primary fault flips count<2 into count>2, changing readiness/capacity.
Its payloads still remain ordered, so the generated payload TB passed the faulty
variant. The harness correctly refused to qualify that testbench and stopped
before integration/routing. The independent capacity TB had already exposed this
class of coverage gap in the separate capacity-one experiment.

This observed failure motivates bounded alternative behavioral fault injections,
without editing or regenerating the testbench. The missed readiness mutation must
remain visible. Qualification is a minimum non-vacuity check, not proof that every
fault is detected. Exact capacity remains independently verified.

The original run reports generic module_failed. A separate reviewer identified
that this summary also loses infrastructure causes; the next change adds typed
blocked diagnostics. This recorded failure must not be resumed across changed
runtime source. Preserve it and start a fresh run after tests pass.

Raw sources/TBs, Python/stimuli, logs, receipts, journal metadata, config/runtime,
and budgets are retained. Compiled trees/duplicated artifacts omitted. This is an
evidence subset, not a resumable execution directory.
