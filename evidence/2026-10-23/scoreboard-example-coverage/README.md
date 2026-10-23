# Scoreboard specification-payload coverage correction

Observed divider01 grader missed zero_divisor_remainder_zero despite an explicit
accepted255/0=>remainder255 specification example. Oracle examples were checked
separately; RTL stimulus contained only0/0. Original model trial and misses are
retained unchanged in generated-divider-attempt-01.

The fix seeds unique complete accepted-example payloads in scoreboard mode.
It requires explicit input-valid and deasserted configured reset; skips valid
partial/inactive/reset examples; rejects malformed examples. The driver keeps
handshake scheduling, and the qualified oracle still computes expectations.
All three existing corners and the exact100 seeded random rows are preserved.
Bounds include payload seeds and reset before random allocation/oracle/output.
Fixed-latency examples and stateful after_cycles traces are not replayed.

## Controlled real-simulator result

Frozen original qualified oracle/spec and unchanged reference/fault source hashes:
- Old control passed; old zero-remainder mutant passed, reproducing the miss.
- New control passed; that same mutant failed an actual remainder assertion.
- Full applicable default-width portfolio improved13/17->14/17 detections.
-103->108 payload vectors, with255/0 added. Exact random tail equality verified.
- Remaining misses: retirement-edge readiness, asynchronous reset and held-result
  reset. Independent temporal checker already detects these across selected widths.
- Three width-only faults are equivalent at default8 and excluded honestly.
- Original completed run protected identities/state/budget unchanged; no model
  call, original FSM resume or PPA remeasurement.20 supervised simulator cases.

Full regression **1226passed175.87seconds**, focused140passed2.35seconds;
all193 frozen source/test/fixture/guard identities matched. Read-only review found
no blocker. Raw simulator logs, hashes and the exact helper are retained.

Initial helper stopped before any simulator/model call because it incorrectly
expected the oracle in final_artifacts. Completed optimization freezes rendered
TB; the helper was corrected to verify oracle qualification receipt and published
archive hash. Original prelaunch console is retained, not counted as a test.

This establishes payload coverage for eligible examples, not complete example
timing/state replay, general mutation completeness or weak-model reliability.
Fresh fulltier0 remains required before main merge. Runtime identity changed,
so earlier cohort streaks must not be carried across this correction.
