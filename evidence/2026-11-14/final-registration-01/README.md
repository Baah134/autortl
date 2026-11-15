# VerilogEval final task registration — November 14, 2026

Frozen after the pilot gate (pilot-06, all three arms clean) and before any
final-set trial. `final_selection.json` is the exact output of
`python -m benchmark.registration` over:

- the two-reviewer adjudicated catalog `benchmark/catalogs/verilogeval-c498220.json`
  (evidence/2026-11-14/catalog-review-01; 156 tasks, 106 families);
- dataset NVlabs/verilog-eval c498220d0a52248f8e3fdffe279075215bde2da6;
- pilot tasks Prob036_ringer, Prob033_ece241_2014_q1c, Prob147_circuit10,
  Prob038_count15, Prob135_m2014_q6b, Prob107_fsm1s (every family containing
  one is excluded);
- `benchmark/catalogs/exclusions_c498220.json`: four broken official references
  (Prob082_lfsr32, Prob141_count_clock, Prob156_review2015_fancytimer: the
  testbench watchdog prints TIMEOUT for the reference; Prob099_m2014_q6c: port
  mismatch), evidence/2026-11-14/pilot-grader-controls-01. An exclusion removes
  only that task, not its family.

Eligible: 144 tasks in 99 families (53 logic, 6 arithmetic, 25 sequential, 15
FSM). Largest-remainder quotas for N=40: combinational_logic 21,
combinational_arithmetic 3, sequential 10, fsm_control 6. Within a category,
families are ranked by SHA-256 of `autortl-public-v1|<commit>|<family>` and each
contributes its best-ranked task. selection_sha256
c85666ff35447db217906e9d9de1a2173f35a3af942f615ed84a99cf1030b593.

Disclosures: the proportional rule makes about half the set simple
combinational logic. Prob027_fadd was also one of four grader-control tasks
(reference and hand-made mutants only; no model output was involved). The
protocol: 3 arms (single_call, ablation, full) x 3 trials, budgets and arm
settings as in the pilot, grading only after every cell is sealed, all failures
retained. Public tasks do not establish freedom from training contamination.
