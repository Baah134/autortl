# Tier1 campaign02: no valid verdict (host standby, then a mid-run source change)

**Recorded 3/4, streak 0, but the run is not a valid tier1 verdict.** Two
things invalidate it, and both are recorded rather than hidden:

1. **Host standby.** The Windows System log shows the laptop entering Modern
   Standby (Reason: Lid) at 11:26:55 EDT and leaving it at 14:21:47. The
   debouncer's integration elaboration stalled under standby; xelab ran 420 s
   against a 120 s limit and the following xvlog reported 10,088 s. The
   harness classified the result as infrastructure
   (`failure_kind: infra`, status `baseline_blocked`), as it should, but the
   bench then recorded it as a failed entry. That is the hard-rule violation
   now fixed (taxonomy `infra_blocked_entry_enters_history`, merged e53f511):
   an infrastructure-blocked entry now gives the campaign no verdict.
2. **The source changed during the run.** The supervisor merged
   `claude/infra-not-history` into this checkout while the bench was still
   running, so the gate reports `source_unchanged: false` and the curriculum
   record's runtime identity is `unknown` ("governance implementation
   changed during campaign"). The running bench had already loaded its code,
   so its behavior was unaffected, but the record cannot qualify, correctly.

| Entry | Mode | Status | Baseline LUT | Best LUT / FF | Calls |
|---|---|---|---:|---:|---:|
| counter8_build | build | PASS | 6 | 6 / 8 | 4 |
| debouncer_build | build from prose | infrastructure-blocked | — | — | 3 |
| encoder8_build | build | PASS | 6 | **4** / 4 | 4 |
| pwm | optimize | PASS (no gain) | 7 | 7 / 9 | 16 |

Identity: freeze `919059c3…` (237 files), model `gpt-6-luna` requested.
The full test receipt passed (1,521 tests).

## What the roles showed

- **The planner spec fix works.** The debouncer, which ended at spec lint in
  tier1-campaign-01, now passed lint on the first planner call (the
  structural rules in the prompt were enough; no repair round was needed).
  Its golden model, generated testbench and mutation qualification all
  succeeded before the standby stalled the integration simulation.
- **The seed timescale fix works.** PWM's baseline carried the default
  `` `timescale 1ns/1ps `` and passed first time, with no model repair.
- **A new role behavior.** In PWM iteration 5 the generator hand-instantiated
  a Xilinx `CARRY4` primitive. The harness simulates behavioral RTL without
  the UNISIM library, so elaboration failed (VRFC 10-2063, no taxonomy hint)
  and a repair call was spent. Recorded as
  `generator_instantiates_unsimulated_primitive`; the generator and timing
  doctor are now told to infer primitives, and both message IDs have repair
  hints.
- encoder8 improved 6 → 4 LUTs (tier1-campaign-01 reached 5).

`role-report.md` lists every role's calls and verdicts. `run/` holds the
bench output without simulator snapshots or Vivado scratch folders;
`archive.py` built this folder and `archive-manifest.json` hashes every file.
