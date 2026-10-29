# First full tier1 gate: 3/4, not qualifying

**3/4 passed (75%, below the 80% qualifying line), streak 0, held false.**

| Entry | Mode | Status | Baseline LUT | Best LUT / FF | Setup ns | Calls | Vivado s |
|---|---|---|---:|---:|---:|---:|---:|
| counter8_build | build | PASS | 6 | 6 / 8 | 0.424 | 4 | 242 |
| debouncer_build | build from prose | FAIL: spec lint | — | — | — | 1 | 0 |
| encoder8_build | build | PASS | 6 | 5 / 4 | 0.452 | 4 | 246 |
| pwm | optimize | PASS (no gain) | 7 | 7 / 9 | 0.553 | 16 | 648 |

The first full run of curriculum tier 1, made with `tools/tier0_gate.py
--tier 1` on the same 232-file identity that holds tier0 (freeze
`a611829c…`). The full test receipt passed (1,461 tests) and the source,
router-statistics and history prefixes were unchanged. Budgets per entry:
iterations from each entry's meta.yaml, best-of-1, 30 model calls, 40 tool
and 60 wall minutes, 1 infrastructure retry. Vivado 2025.2,
xc7a35tcpg236-1, 100 MHz, ideal zero I/O delay. The model is the
unobserved Codex CLI default.

## What the roles did, and the two harness gaps they exposed

- **debouncer_build** starts from a five-line prose request
  (`curriculum/tier1/debouncer_build/spec.md`). The planner wrote a
  reasonable spec, but named the top `debouncer`, the same as its only
  module. Structural lint rejects that, and the run ended at once with
  `spec_lint_failed` after one model call. The spec prompt never stated the
  rule, and a planner-written spec got no repair round.
  Taxonomy: `spec_lint_failure_skips_planner_repair`.
- **pwm** printed `baseline failed verification`. The curriculum seed has
  no `` `timescale `` while its testbench has one, so xelab stopped with
  XSIM 43-4099. The harness spent a generator repair call, and the model's
  repair added only `` `timescale 1ns/1ps `` (diffed). Generated RTL already
  gets that directive mechanically; the seed did not.
  Taxonomy: `seed_without_timescale_costs_model_repair`.
  The five optimization proposals that followed were all larger (8 to
  10 LUTs) and were rejected, so the 7-LUT baseline stood.
- **encoder8_build** improved 6 → 5 LUTs; **counter8_build** kept its
  6-LUT baseline. Both passed the independent top-level testbench.

Both gaps are fixed on `claude/model-portability`; the tier1 series restarts
on that identity.

`run/` holds the bench output, with simulator snapshots and Vivado scratch
folders left out. `history-at-tier1-campaign-01.jsonl` is the curriculum
history at the end of the gate. `archive.py` built this folder, and
`archive-manifest.json` hashes every file.
