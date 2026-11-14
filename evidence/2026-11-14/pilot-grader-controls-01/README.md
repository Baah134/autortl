# VerilogEval pilot grader controls and selection — November 14, 2026

Pilot preparation only. No model, Vivado, harness run or board activity. Not a
benchmark result.

## Identity

- Dataset: NVlabs/verilog-eval `c498220d0a52248f8e3fdffe279075215bde2da6`
  (2025-02-07), `dataset_spec-to-rtl`, 156 tasks, MIT licence. Cloned outside
  the repository and outside model-visible folders.
- Simulator: Icarus Verilog 12.0 (stable), MSYS2 `mingw-w64-ucrt-x86_64-iverilog`
  `1~12.0-1`, Windows 11. Upstream documents Icarus v12.
- Grader: `benchmark/verilogeval.py` at the uncommitted November14 working copy;
  the committing change records its source commit.
- Upstream semantics confirmed against the pinned commit: `Makefile.in` line 54
  (`-Wall -Winfloop -Wno-timescale -g2012 -s tb`), line 156 (`timeout 30`, a
  `TIMEOUT` line on exit 124), and `scripts/sv-iv-analyze` `analyze_result`,
  ported line for line as `upstream_passfail`.

## Results

`grader_controls.json` (script `grader_controls.py`): four tasks, one per
category (Prob001_zero, Prob027_fadd, Prob035_count1to10, Prob107_fsm1s), four
controls each. All 16 as expected; strict and upstream classifications agree:
reference pass/`.`, one-line behavioral mutant fail/`R` (20/20, 105/214,
336/439, 229/230 mismatches), syntax error compile_error/`S`, zero-time
infinite loop timeout/`T`.

`reference_sweep.json` (script `reference_sweep.py`): every reference renamed to
TopModule. 152/156 pass both rules. Four official-reference defects:

| Task | Strict | Upstream | Cause |
|---|---|---|---|
| Prob082_lfsr32 | pass | T | testbench's own 1,000,000 ps watchdog prints `TIMEOUT` even for the reference |
| Prob141_count_clock | pass | T | same watchdog |
| Prob156_review2015_fancytimer | pass | T | same watchdog |
| Prob099_m2014_q6c | compile_error | C | testbench connects ports Y2/Y4; reference declares Y1/Y3 |

Under Nov6 protocol rule 3 (broken official reference controls) these four are
excluded from final selection, with these reasons published. None is a pilot task.

## Catalog and pilot selection

`catalog_keyword_draft.json` is the keyword pass (`draft_catalog.py`, prompts
only). The committed catalog `benchmark/catalogs/verilogeval-c498220.json`
applies 21 hand corrections from reading statements (muxes, parity,
thermostat and K-map tasks to combinational_logic; LFSRs, cellular automata,
history shift, gshare, the saturating counter and circuit10 to sequential).
Categories: 66 combinational_logic, 7 combinational_arithmetic, 43 sequential,
40 fsm_control tasks; 116 families. The catalog is one reviewer's draft (Claude);
the protocol's second reviewer is pending and final selection must wait for it.

`pilot_selection.json`: fixed slots 1/1/2/2 (logic/arithmetic/sequential/FSM),
families ranked by SHA-256 of `autortl-public-v1|<commit>|<family>`:
Prob036_ringer, Prob033_ece241_2014_q1c, Prob147_circuit10, Prob038_count15,
Prob135_m2014_q6b (family m2014_q6), Prob107_fsm1s (family fsm1). The slot rule
changed twice before any trial: round-robin took 2 of 7 arithmetic tasks;
proportional allocation gave three trivial wiring tasks. Clocked categories
carry the adaptation risk the pilot exists to find.

`sanitize_logs.py` produced the anonymised real-log parser fixtures in
`tests/fixtures/verilogeval/`.

## Limits

Controls diagnose grader coverage, not candidate correctness. Logs contain
absolute paths; a path containing the word "error" would trip the upstream
classifier, so grading directories must avoid it. Hidden-grader isolation is not
enforced at OS level.
