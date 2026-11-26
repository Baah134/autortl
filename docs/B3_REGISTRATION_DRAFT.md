# B3 optimisation benchmark — registration DRAFT

**Status: DRAFT, not frozen, awaiting the owner's approval.** No B3 trial
has run, and none may run until the owner freezes this registration and the
decision rule (`docs/DECISIONS.md`, the DRAFT B3 entry). Freezing means:
copying the final task list and settings into a new evidence folder
(`evidence/<date>/b3-registration-01/`, like `final-registration-01`),
pinning the model, recording the runtime commit, and dating the DECISIONS entry.
Machine-readable draft: `evidence/2026-11-21/b3-candidates-01/registration_draft.json`.

Spec: `docs/ROADMAP.md` task B3.

## Question

On designs that both arms get functionally right, does the harness with
optimisation produce smaller or faster routed designs than a single model call?

## Arms

| Arm | Cell arm | What runs | Budget per cell (draft) |
|---|---|---|---|
| A single call | `single_call` | one model call from the task prompt, as in final-02 | 1 model call, 35 min wall |
| C-opt harness | `full` | `run.py build --iterations 5 --best-of-n 4 --implementation out_of_context --objective minimize_luts`, target 100 MHz | 64 model calls, 120 min Vivado, 180 min wall |

Three trials per task and arm. Same pinned model in both arms (`--model`,
owner to name it). Neither arm sees the official testbench or reference. The
harness optimises against its own 100 MHz OOC flow, the same part and period
the PPA measurement uses.

## Measurement

1. Grade function first: `python -m benchmark.report grade` (official
   testbench, upstream-compatible verdict), unchanged from final-02.
2. Synthesise every passing cell of both arms: `python -m benchmark.ppa measure
   --attempt <dir> --vivado <vivado.bat>`. Out of context, `xc7a35tcpg236-1`,
   10 ns, the harness's OOC template (hash recorded), Vivado 2025.2. It refuses
   unsealed, tampered, missing or functionally failing submissions; Vivado
   infrastructure failures write no record and are retried.
3. Report: `python -m benchmark.ppa_report render --attempt <dir> --out <report.md>`.
   Paired LUT ratio (primary), timing closure, FF ratio and WNS difference,
   only over tasks where both arms pass at least once; task-clustered bootstrap.

## Tasks (proposed)

Filled from `evidence/2026-11-21/b3-candidates-01/` (see its README for every
measured number).

**20 tasks: 8 VerilogEval and 12 RTLLM v2.1.** Reference LUTs are routed,
out of context, with the same flow `benchmark/ppa.py` uses.

VerilogEval (`c498220`), the 8 of 35 tasks where arm A and arm C each passed
at least one final-02 trial and the official reference has at least 20 LUTs
(the other 27 have 0 to 16):

| Task | Reference LUT | FF | final-02 passes A / C |
|---|---|---|---|
| Prob018_mux256to1 | 68 | 0 | 3 / 3 |
| Prob043_vector5 | 20 | 0 | 3 / 3 |
| Prob055_conditional | 36 | 0 | 3 / 2 |
| Prob097_mux9to1v | 49 | 0 | 3 / 3 |
| Prob108_rule90 | 510 | 512 | 3 / 3 |
| Prob115_shift18 | 97 | 64 | 3 / 3 |
| Prob144_conwaylife | 1018 | 256 | 3 / 3 |
| Prob153_gshare | 560 | 263 | 3 / 1 |

RTLLM v2.1 (`hkust-zhiyao/RTLLM` at `51ed553d0ffd32797a1a0a13e051656bf302c81f`,
MIT licence, no per-file notices): 43 of 50 references pass their own
testbench under Icarus 12; 13 also have one clock named `clk` or none,
synthesise in Vivado and reach 20 LUTs; the 12 largest are proposed (the 13th,
`traffic_light`, 21 LUTs, is left out by the "8 to 12" cap):

| Design | Top | Reference LUT | FF | DSP | Reference WNS at 10 ns |
|---|---|---|---|---|---|
| Arithmetic/Divider/div_16bit | div_16bit | 790 | 0 | 0 | -36.988 (combinational, does not close) |
| Miscellaneous/RISC-V/alu | alu | 685 | 0 | 0 | 0.958 |
| Arithmetic/Other/fixed_point_adder | fixed_point_adder | 152 | 0 | 0 | 4.492 |
| Arithmetic/Other/fixed_point_substractor | fixed_point_subtractor | 118 | 0 | 0 | 4.209 |
| Arithmetic/Multiplier/multi_16bit | multi_16bit | 95 | 70 | 0 | 4.560 |
| Arithmetic/Adder/adder_32bit | adder_32bit | 77 | 0 | 0 | 3.727 |
| Arithmetic/Multiplier/multi_pipe_8bit | multi_pipe_8bit | 74 | 92 | 0 | 5.845 |
| Arithmetic/Multiplier/multi_booth_8bit | multi_booth_8bit | 68 | 101 | 0 | 5.784 |
| Arithmetic/Substractor/sub_64bit | sub_64bit | 65 | 0 | 0 | 4.469 |
| Miscellaneous/RISC-V/pe | pe | 47 | 32 | 3 | 7.178 |
| Control/Counter/up_down_counter | up_down_counter | 37 | 16 | 0 | 6.105 |
| Miscellaneous/RISC-V/RAM | RAM | 34 | 78 | 0 | 7.241 |

Excluded RTLLM designs and the reason for each are in `rtllm_survey.json`
(7 fail their own test, 5 use a clock not named `clk`, 2 do not synthesise in
Vivado, 5 are under 20 LUTs, 18 were not synthesised as small by inspection). With 20 tasks
the 10-pair minimum of the draft rule leaves room for tasks where one arm
never passes.

## Prerequisites before freezing (found while drafting)

1. **Arm settings.** `benchmark/pilot.py` fixes `FULL_SETTINGS` at one
   iteration and best-of-1, and `benchmark/campaign.py` has no per-arm settings.
   C-opt needs `--iterations 5 --best-of-n 4` passed per registered cell (a
   settings field in the frozen manifest, recorded in each run). `pilot.py` is
   being edited by another session; this change waits for it.
2. **RTLLM adapter.** `full_command` passes `--top TopModule` and the grader
   is VerilogEval-specific. RTLLM needs a `benchmark/rtllm.py` adapter
   (dataset format `rtllm` is already accepted by `benchmark/artifacts.py`):
   public file `design_description.txt`; private testbench, reference and data
   files; top from the makefile's `TEST_DESIGN`; grader compiles the testbench
   with the candidate under Icarus and passes on "Your Design Passed". Data
   files (`*.dat`, `*.txt`) are read by the testbench from its working
   directory. Each adapter needs pytest fixtures, as for VerilogEval.
3. **Finish flow.** `benchmark.finish` should run `ppa measure` and
   `ppa_report render` after grading and archive the records.
4. **Budgets.** The draft budgets above are estimates (reference OOC runs take
   3 to 15 minutes each on this laptop); a two-task pilot of C-opt should
   confirm them before freezing.
5. **Designs with no timed register.** The official Prob137_fsm_serial
   reference infers latches (`[Synth 8-327]`); its routed timing summary shows
   WNS and WHS as `NA`. `benchmark/ppa.py` refuses such a report (it never
   records a zero), which would leave the cell unmeasured and block the report.
   Before freezing, decide the rule (proposed: record it as measured, LUT
   counted, timing not closed) and add the taxonomy entry before the change.

## Open decisions for the owner

1. Approve or change the task set (VerilogEval subset plus RTLLM, see above).
2. Pin the model name for both arms.
3. Whether arm A's prompt stays exactly the task prompt (proposed: yes, so A
   is the same baseline as final-02) or gets a one-line "minimise area" hint.
4. Approve the decision rule thresholds (ratio band 1/1.10 to 1.10, at least
   10 measured pairs, 10% infrastructure limit).

## Limits known now

- The VerilogEval candidates were chosen from final-02 results (both arms
  passed there), so B3 is not a fresh functional comparison on them.
- Out-of-context timing covers internal clocked paths; ports are unconstrained
  unless a design has no register-to-register path.
- Many VerilogEval tasks are tiny; area differences there are a few LUTs.
- One part, one period, one model.
