# VerilogEval c498220 catalog: second review and adjudication — November 14, 2026

Two classifications of all 156 spec-to-RTL tasks from statements only.

- `reviewer1_catalog.json`: Claude (coordinator), keyword pass plus 21 hand
  corrections (committed earlier as benchmark/catalogs/verilogeval-c498220.json).
- `reviewer2_catalog.json`: an independent Claude subagent instructed to read
  only `*_prompt.txt`, blind to reviewer 1's catalog and all evidence.

Category agreement 152/156 (0.974), Cohen's kappa 0.962. Adjudication:

| Task | R1 | R2 | Decision |
|---|---|---|---|
| Prob008_m2014_q4h | sequential | combinational_logic | R2: the statement is a combinational wire; R1 had wrongly grouped it with the latch/DFF questions |
| Prob055_conditional | combinational_logic | combinational_arithmetic | R2: minimum of four values by magnitude comparison is arithmetic by the category definition |
| Prob037_review2015_count1k | fsm_control | sequential | R1: part of the review2015 fancytimer question; family takes the FSM category |
| Prob063_review2015_shiftcount | fsm_control | sequential | R1: same family as above |

Families are the union of both reviewers' groupings (connected components), so
related tasks can never straddle pilot and final sets: 106 families, 28 with
several members. Final categories: 66 combinational_logic, 42 sequential,
40 fsm_control, 8 combinational_arithmetic. The family rule changed no
category. Same reviewer model family for both reviews is a limitation.

The pilot tasks were selected and frozen (pilot-04) before this review and are
kept; final selection excludes every merged family containing a pilot task.
