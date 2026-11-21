# Release v1.0.0 — checklist and drafts

Prepared November 20, 2026 while `final-02` runs, so the release is a few
commands once it finishes. Text in `<angle brackets>` comes from the
`benchmark.finish` output; nothing else is filled in by hand.

## Checklist

1. `final-02` complete: `campaign.log` ends with `"reason": "all cells attempted"`.
2. `python -m benchmark.finish ...` (ROADMAP B1) on `codex/contract-context`;
   read the false acceptances and non-`done` cells, add taxonomy entries,
   re-seal; commit the evidence folder.
3. README: replace the "Registered comparison" row of *Results at a glance*
   with the printed row; update "Known limits" if the verdict changes the
   first bullet. Commit.
4. Merge `c6-dedupe` into `codex/contract-context`; run the harness suite
   (`python -m pytest tests/ -q -n auto`), the tooling suite, `ruff check .`
   and `python tools/evidence_audit.py --rev HEAD`. Commit.
5. Owner approval: open the PR below to `main`; after CI passes and the owner
   merges, tag `v1.0.0` on the merge commit and publish the release notes.

## Pull request: `codex/contract-context` → `main`

**Title:** AutoRTL v1.0.0: verified harness, hardware evidence and a registered benchmark

**Body:**

> AutoRTL writes and optimizes Verilog with bounded model roles and accepts a
> design only on deterministic evidence: mutation-qualified testbenches,
> Vivado synthesis, place and route, and a metrics integrity gate.
>
> This branch brings `main` up to the release:
>
> - **Registered comparison** on 40 public VerilogEval tasks, three arms
>   (single call, harness without mutation qualification, full harness),
>   three trials. A single model call passes more tasks than the full harness: C 86.1% vs A 94.1%, difference -9.2 pp (95% CI -19.2 to -0.8 pp, 40 tasks); the harness used 7.4x the model calls per pass. About one in ten harness-accepted designs
>   failed the official test: planner misreadings that the oracle shared,
>   and two official references that contradict their own prose. Evidence: `evidence/2026-11-21/final-02-results`. Tasks and decision rule were fixed
>   before grading (`docs/DECISIONS.md`, `benchmark/claim.py`).
> - **Fixes from the failure review** (after grading; not counted in the
>   result): single-module plans when no trusted testbench is supplied, the
>   golden model's latency-0 observation phase, a planner rule against
>   behaviour the request does not state, and tool-using model replies
>   counted as failures rather than infrastructure.
> - **Hardware:** twelve harness-optimized cores (RV32I, AES-128, CORDIC,
>   16-tap FIR and others) passed 50,000 transactions each on a Basys 3
>   against independent models.
> - **Optimization:** e.g. AES-128 from 9,108 to 614 LUTs with timing met.
> - **Benchmark tooling:** VerilogEval adapter with an upstream-faithful
>   grader, sealed receipts, restart-safe campaign runner that waits out model
>   quota, task-clustered bootstrap report, one-command finish and archive.
> - **Robustness fixes** found by the pilots: empty netlists, Vivado
>   shutdown crashes, clockless and single-register designs out of context,
>   infrastructure stops never counted as verdicts.
> - **Repository:** MIT licence, one agent guide, compact README, shared
>   synthesis-template blocks and file helpers, ruff lint and parallel tests
>   in CI (about 2,380 harness and 325 tooling tests).
>
> Known limits: public tasks do not exclude training contamination; one model
> and backend; one FPGA family and Vivado version; a request the planner
> misreads can be verified and accepted (recorded case, ROADMAP V1).

## Release notes: v1.0.0

**AutoRTL v1.0.0** — an LLM harness for Verilog in which the model proposes and
deterministic checks decide.

- A single model call passes more tasks than the full harness: C 86.1% vs A 94.1%, difference -9.2 pp (95% CI -19.2 to -0.8 pp, 40 tasks); the harness used 7.4x the model calls per pass. (40 VerilogEval tasks x 3 arms x 3 trials, pre-registered
  rule; `evidence/2026-11-21/final-02-results/README.md`). The harness's value
  is in optimization and hardware-proven builds, not single-module functional tasks.
- Twelve generated and optimized cores verified on a Basys 3 board, 50,000
  transactions each, 0 mismatches.
- Optimization through Vivado feedback: AES-128 9,108 to 614 LUTs; FIR16 closes
  150 MHz; dot product 328 to 20 LUTs through DSP inference.
- Every result archived with SHA-256 manifests and audited in CI.

Next (v1.1): an optimization benchmark where the harness is expected to
differ (ROADMAP B3) and mitigation for planner misreadings shared by the
testbench and the design (V1).
