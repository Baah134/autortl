# B3 task candidates and RTLLM survey — November 21 to 25, 2026

Preparation for ROADMAP task B3 (optimisation benchmark). No model, harness
run, campaign or board activity. Reference designs only. Not a benchmark
result. The proposed registration is a DRAFT awaiting the owner's approval
(`docs/B3_REGISTRATION_DRAFT.md`, `registration_draft.json`).

## Identity

- VerilogEval: NVlabs/verilog-eval `c498220d0a52248f8e3fdffe279075215bde2da6`,
  `dataset_spec-to-rtl` (MIT). Selection input: final-02 graded rows
  (`evidence/2026-11-21/final-02-results/summary.json`).
- RTLLM: `https://github.com/hkust-zhiyao/RTLLM` at
  `51ed553d0ffd32797a1a0a13e051656bf302c81f` (commit message "v2.1", August 16,
  2026). Licence: MIT ("Copyright (c) 2024 Nora Lu"), `LICENSE` SHA-256 in
  `rtllm_survey.json`; no per-file licence notices in the design folders.
- Both are cloned outside the repository; only names, hashes, licences and
  metrics are committed here.
- Vivado 2025.2, part `xc7a35tcpg236-1`, 10 ns, the harness's out-of-context
  template (`autortl.vivado.run_synthesis`, `implementation=out_of_context`),
  routed reports parsed by `autortl.report_parser`. This is the flow
  `benchmark/ppa.py` uses for B3 trials. Harness code: commit `1c341f798`.
- Icarus Verilog 12.0 (`iverilog -g2012 testbench.v <top>.v`, then `vvp -n`).

## Method

- `synth_refs.py`: synthesise and route each reference out of context; one
  `metrics.json` per design (LUT, FF, DSP, BRAM, WNS, WHS). Up to three
  Vivado processes at once. A run that stopped with the machine was resumed;
  only designs without a `metrics.json` were rerun.
- `rtllm_sweep.py`: every RTLLM reference against its own testbench. The
  reference's `verified_*` top module is renamed to the makefile's
  `TEST_DESIGN` (the name the testbench instantiates); pass = the testbench
  prints "Your Design Passed".
- `build_candidates.py`: composes `verilogeval_candidates.json` and
  `rtllm_survey.json` from those outputs.

## Results

VerilogEval: 35 of the 40 final-02 tasks had at least one passing trial in
both arm A and arm C. 8 of them have a reference of at least 20 LUTs:
Prob018_mux256to1 (68), Prob043_vector5 (20), Prob055_conditional (36),
Prob097_mux9to1v (49), Prob108_rule90 (510), Prob115_shift18 (97),
Prob144_conwaylife (1,018), Prob153_gshare (560). The other 27 have 0 to 16
LUTs.

RTLLM: 43 of 50 references pass their own testbench under Icarus. Failing:
adder_pipe_64bit and multi_pipe_4bit (makefile names a module the files do not
define), ring_counter (elaboration), asyn_fifo (testbench uses `break`, not
supported by Icarus 12), freq_divbyeven (invalid instantiation), radix2_div and
clkgenerator (finish without the pass message). Twenty were synthesised (the
designs likely to be large); 13 pass, have one clock named `clk` or none, and
reach 20 LUTs. The 12 largest are proposed: div_16bit (790), alu (685),
fixed_point_adder (152), fixed_point_substractor (118), multi_16bit (95),
adder_32bit (77), multi_pipe_8bit (74), multi_booth_8bit (68), sub_64bit (65),
pe (47), up_down_counter (37), RAM (34). traffic_light (21) is 13th.

## Findings to carry forward

- **fixed_point_substractor**: its makefile `TEST_DESIGN` is misspelt; the
  reference and testbench use `fixed_point_subtractor`, which is the top
  synthesised and the top a B3 adapter must use.
- **multi_8bit** (loop variable declaration, `[Synth 8-10936]`) and
  **float_multi** (mixed edge and level sensitivity, `[Synth 8-434]`) pass
  Icarus but do not synthesise in Vivado as Verilog; excluded.
- **Prob137_fsm_serial**: the official reference infers latches
  (`[Synth 8-327]`) and its routed timing is `NA`. `benchmark/ppa.py` refuses
  such a report rather than recording a value; the registration must decide
  the rule before freezing (open item 5 in the draft).
- Five RTLLM designs clock on `CLK`, `Clk`, `CLK_in` or two clocks; the OOC
  template times only a port named `clk`, so they are excluded rather than
  measured untimed.
- div_16bit's reference misses 10 ns by 37 ns (combinational divider), a task
  where timing optimisation has room.

## Limits

- Candidate VerilogEval tasks are chosen from final-02 results, so B3 on them
  is not a fresh functional comparison.
- "Small by inspection" designs were not synthesised; the cut is a judgement,
  recorded per design in `rtllm_survey.json`.
- Reference LUT counts describe the references, not what either arm will
  produce.
