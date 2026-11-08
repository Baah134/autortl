# AES03 controller oracle: first-attempt qualification observed

Read-only source review of
`logs/explore-aes-20261108-03/aes128_core_build/modules/aes_ctrl/`.
The parent reports source revision `defd87f` and the same separately qualified
CLI0.167 used for AES02. This review inspected the current oracle, its actual
qualification receipt and the run's supplied module specification. It did not
launch a model, vendor tool, test, hardware server, serial/JTAG action or board
operation, execute generated Python, or modify canonical files. Files were read
and closed immediately; no live-run handle was retained.

## Bound observation

Raw file SHA256:
`31bcce019523f4b0528095f9ebb4ccb7c41415e03eb16e1ce0239d3346928ef2`.
This exactly matches `golden_attempt_1.log`, whose status is `oracle_qualified`.
The receipt explicitly limits qualification to specification examples and
generated stimulus, excluding formal equivalence and reset-kind proof. The
module has three public examples, fixed_latency1 and active-high synchronous
reset. This review does not independently rerun those checks.

Unlike AES01's three failed controller sources, this oracle directly consumes
the controller's supplied neighbor values. `inputs.get("key_next",0)` at
line27 updates the round-key register on each busy edge. The state register
reads `inputs.get("round_out",0)` at line31 for rounds above zero. Both values
are masked to128bits. There is no AES-round/key-schedule reimplementation,
S-box setup, GF table construction or helper call; top-level functions are
only init and step. There are no hardcoded public-example ct/rk constants or
special-case example branches in the inspected source.

## Contract consistency visible in the source

- init clears busy, out_valid, rnd, ct and rk. A supplied rst does the same on
  a step. Outputs are views of post-transition state, matching the stated
  latency1 oracle API without adding a delay queue. This is a Python step
  model; it cannot establish physical between-edge reset behavior by itself.
- Busy operation uses saved pre-edge rnd. It always loads key_next; rnd0 is
  key preparation, advancing only rnd. Rounds1–10 load round_out. The final
  round clears busy, sets out_valid and returns rnd to0.
- While out_valid is asserted, only out_ready clears that flag; ct and rk
  hold. Idle acceptance uses in_valid, loading masked pt XOR key, masked key,
  rnd0 and busy1. This preserves the contract's priority and next-block gap.
- The round-constant tuple matches the public values for rnd0–9, and returns0
  for rnd10 or above. Last is true exactly at rnd10; in_ready is derived from
  the resulting busy/out_valid. Reset therefore makes in_ready1 and rcon1,
  rather than falsely requiring every derived output to be zero.
- ct/rk are normalized to128-bit patterns at read/update boundaries. rnd is
  internally initialized0 and advances through the stated0–10 sequence; the
  review found no reachable-state need for an additional four-bit wrap mask.

These are source-consistency findings, not exhaustive verification of every
state/input combination or the RTL implementation.

## What can be claimed now

The fresh AES03 controller oracle qualified on its **first attempt**, and its
source visibly respects the independently driven neighbor-input boundary that
the earlier failed sources violated. This is concrete bounded recovery
evidence. It is not yet an AES RTL pass, successful top-level integration,
routed timing closure, curriculum hold, benchmark improvement or board result.

Because this was a first attempt, the new **previous-failed-source** repair
context was not exercised for this controller. Public examples and the earlier
module/helper instructions were available, but one fresh stochastic result
cannot identify which change caused recovery or establish general model gain.
Requested versus observed model identity remains a separate provenance issue.

Machine-readable source/receipt/input-read audit is retained in
`work/nov8-aes03-controller-audit.json`; the read-only inspector is
`work/nov8_aes03_controller_audit.py`. The parent must continue monitoring the
remaining actual module/RTL/integration/implementation gates and retain any
later failures rather than infer success from this single oracle receipt.
