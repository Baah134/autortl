# Generated priority encoder: accepted6to5LUT improvement

A fresh typed8-bit priority-encoder build completed the generated Python oracle,
examples, generated module testbench and sabotage qualification, mechanical top
integration, baseline routing and one model-driven optimization iteration.
The promoted exact winner plus saved declared child separately passed the
independently qualified exhaustive256-pattern ascending/descending TB, including
zero-input validity, registered-edge behavior and synchronous reset checks.

| Metric | Baseline | Accepted winner |
|---|---|---|
| Routed LUTs |6|5 (16.67% reduction)|
| Flip-flops |4|4|
| Setup slack |0.528ns|0.531ns|
| Hold slack |0.009ns|0.156ns|

Check raw baseline report for exact hold measurement; structured run_summary.json
is authoritative if this human table disagrees. Five model calls and495.720charged
toolseconds. All actual tool process exits and deterministic gates passed; final
review accepted7/7criteria. This is a bounded result on small logic, not a broad
benchmark/model-strength claim. Source runtime is978c742 (53frozenimplementation
files matched before any subsequent runtime edit), full regression suite746pass.

Vivado2025.2,xc7a35tcpg236-1,10ns,ideal-zero min/max I/O constraints. Build used
no--tb to exercise golden generation. Its optimization candidate was graded by
the generated-derived top TB; the independent final check is a separate measured
step. The later combined-verification option does not retroactively apply here.
No held tier, multi-module generation or formal-equivalence claim follows.

Retained: exact sources/TBs/Python/stimuli, runtime/config, routed reports, tool
receipts, input manifests, budgets, stage journal metadata and final review.
Compiled trees and duplicated journal artifacts are omitted. Historical absolute
paths are not portable execution directories. Reproduce with run.py build and
curriculum/tier1/encoder8_build/design_spec.json, top priority_encoder8,
--iterations 1 --best-of-n 1, explicit bins/budgets;
then independently run scripts/check_generated_build.py against the saved run and
curriculum/tier1/encoder8_build/priority_encoder8_tb.v in a fresh output directory.
