# FIFO recovery regression evidence

The first model-generated FIFO passed functional tests but failed routed setup
(-0.931 ns). Its candidate duplicated a frozen child and failed compilation.
The prior selection policy also preferred a smaller timing-invalid candidate
in a controlled comparison. The failed hardware run remains in
`../../2026-10-20/generated-fifo-attempt-01/`.

Repairs use the existing roles and verification ladder: explicit compilation
boundaries, shared bounded compile/simulation recovery, feasibility before
objective ranking, UTF-8 source IO, and original child/TB identities retained
through completed-run reuse. Timing recovery is distinct from objective gain.
No testbench, clock or acceptance requirement was relaxed.

Retained regression history:
- Pure feasibility/selection tests: 64 passed.
- First integrated focus: 168 passed, two legacy fixture failures. Corrected a
  contradictory timing flag/slack fixture and a test expecting repair at zero
  configured attempts; negative assertions retained.
- Second integrated focus: 172 passed.
- Two Unicode and three child-integrity tests failed before their fixes.
- Intermediate binding run: 31 passed, one test expected an exception where the
  existing API correctly returned infra_blocked. Updated the API assertion.
- Final integrated focus: 187 passed in 143.87 seconds.
- Strict manifest schema version: 12 passed, including bool/float rejection.

Final full-suite: **939 passed in 349.85 seconds**, frozen runtime. The prior
full run had 938 passes and one synthetic cache fixture missing source/TB
lineage; its truthful fixture repair passed all 20 file tests before the rerun.
This development checkpoint contains the tested runtime. The fresh FIFO and
full tier0 hardware gates remain pending before main integration.
Controlled tests are not evidence of live hardware timing recovery.
