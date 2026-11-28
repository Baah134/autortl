# Tier3 exploration 02: the first run of every tier3 entry

Exploratory, not a curriculum verdict: `tools/explore.py --tier 3 --jobs 2
--model gpt-6-luna` ran each entry through `run.py build` from its prose
request, without writing the curriculum history. Code: branch `claude/post-hold`
at 7c0e9188 (timing progress, live companions, planner repair of spec examples,
inlining guidance), from the `autortl-portability` worktree. Budgets per entry:
iterations from meta.yaml, best-of-1, 30 model calls, 40 tool and 60 wall
minutes. Exploration 01 is not archived: every entry stopped at once with
CODEX_UNAVAILABLE because the Codex app had moved its binary (classified as
infrastructure, no design touched); explore.py now runs the doctor first.

| Entry | Built from prose | Baseline (Basys 3, 100 MHz) | Best | Calls | Wall |
|---|---|---|---|---:|---:|
| dot4_pipeline_build | yes | 325 LUT, 52 FF, WNS +0.087 ns | **17 LUT + 4 DSP, WNS +0.354 ns** | 9 | 15.7 min |
| elastic_dot4_build | yes | 328 LUT, 54 FF, WNS +0.108 ns | **20 LUT + 4 DSP, WNS +0.105 ns** | 11 | 37.5 min |
| signed_fir4_build | yes | 79 LUT, WNS -0.305 ns (missed timing) | **80 LUT, WNS +0.001 ns (timing recovered)** | 11 | 29.1 min |
| iterative_divider_build | yes | 57 LUT, 59 FF, WNS +0.313 ns | unchanged (3 rejected) | 11 | 30.6 min |
| uart_fifo_build | no: spec_lint_failed | — | — | 4 | 1.9 min |

## What the roles showed

- **Large verified gains above tier2.** In both dot-product designs the planner
  moved the four 8x8 multiplies into DSP48 slices (`use_dsp`), cutting LUTs by
  about 94%, with the elastic valid/ready behavior and timing intact. Note that
  `minimize_luts` does not charge DSP use.
- **Timing recovery works on tier3.** signed_fir4's generated baseline missed
  100 MHz; the roles closed it for one extra LUT. A later 51-LUT candidate
  missed timing by 0.024 ns and was correctly rejected.
- **Frozen children blocked the divider.** All three proposals could only edit
  the wrapper around the frozen divider core, so nothing changed (taxonomy
  `frozen_children_block_build_optimization`; children are now editable as one
  unit when an independent top testbench exists).
- **uart_fifo_build's spec failed lint four times.** The planner tagged the
  FIFO's payload ports `valid_ready`, leaving no checkable output, and the error
  did not name the ports, so repairs repeated the mistake (taxonomy
  `payload_ports_tagged_valid_ready`; the error now names them and the spec
  prompt states the rule). The new example check caught it before any oracle
  ran.

Per-entry role reports: `role-report-<entry>.md` (tools/role_report.py).
Simulator snapshots (xsim.dir) and Vivado scratch (.Xil) are not copied.
