# Iterative unsigned divider experiment

A build task with child `iterative_divider_core #(WIDTH=8)` and fixed
eight-bit top `iterative_divider`. One accepted request contains unsigned
`dividend` and `divisor`; its result is the atomic `(quotient, remainder)` pair.
The mechanical wrapper binds WIDTH=8 and has no public parameters. Future
physical measurements apply only to that default instance.

## Fixed arithmetic and schedule

- Supported integer WIDTH domain: 1..16. Preserve all four unsigned symbolic
  `[WIDTH-1:0]` operand/result boundaries.
- Capture operands at rising edge k only when `in_valid && in_ready`.
  `in_ready = !busy && !out_valid`: accept no request during computation or a
  held result. Output retirement does not enable input acceptance on that same
  edge; earliest next acceptance is the following edge.
- Execute WIDTH compute steps at edges k+1 through k+WIDTH. First assert result
  valid after the NBA update of edge k+WIDTH; earliest retirement is edge
  k+WIDTH+1. No shortcuts for trivial operands or divide by zero.
- For divisor != 0, return unsigned floor division and modulo. For divisor=0,
  return all-ones quotient and the original captured dividend as remainder.
  Both cases use the same schedule.
- Hold valid and both result fields stable during an output stall. Invalid
  result fields are unspecified. Inputs may change after acceptance without
  affecting the outstanding result.
- Synchronous active-high reset aborts computing and held results, dominates
  transfers at the rising edge, and leaves no abandoned result to appear later.
  Reset does not gate readiness or validity combinationally between edges.

Typed numeric latency 9 and `// @latency 9` describe the default WIDTH=8
minimum accepted-transfer age. Overridden children instead have age WIDTH+1;
the independent testbench checks their exact availability and boundary
schedule. Scoreboard latency metadata alone does not enforce exact first-valid
timing. The golden oracle maps accepted operands to eventual arithmetic outputs,
without implementing busy state, handshake scheduling or a delay queue.

## Independent verification and admission

| Instance | WIDTH | DUT |
|---|---:|---|
| Default | 8 | Mechanical top wrapper |
| Minimum | 1 | Explicit parameterized child |
| Small | 2 | Explicit parameterized child |
| Exhaustive small | 4 | Explicit parameterized child |
| Non-power-of-two width | 13 | Explicit parameterized child |
| Maximum | 16 | Explicit parameterized child |

The independent checker verifies quotient and remainder, exact pre-edge
and post-NBA availability, legal held producers, busy/result boundaries,
backpressure stability, operand noise after capture, reset at each compute
phase and while holding a result, and transaction conservation. It exhaustively
checks widths 1, 2 and 4, and exercises high-bit operands, exact division, maximal
values, divide by zero and deterministic larger-width random cases. An enclosing
watchdog and all-case completion gate prevent an unfinished case from passing.

`qualification/reference.v` is a supervised restoring-divider control, never
a model seed. It uses a WIDTH+1-bit trial remainder and a bounded step counter.
Admission covers twenty distinct source mutations in arithmetic, width,
capture, schedule, stalls, readiness and reset. Distinct mutations may expose
overlapping observable failure classes. Compile errors, infrastructure failures
and watchdogs do not qualify as behavioral kills.

On October 23, 2026, fresh qualification produced **21/21 expected verdicts**:
the control passed all six selected widths and all twenty mutants triggered
actual behavioral assertions. The complete regression suite passed **1,180
tests in 429.28 seconds**; all 192 frozen identities remained unchanged through
validation and archiving. See the [retained successful admission evidence](../../../evidence/2026-10-23/divider-admission-attempt-02/)
for exact inputs, identities and raw verdicts.

The [first admission attempt](../../../evidence/2026-10-22/divider-admission-attempt-01/)
exposed a verification gap: reset with output ready high allowed normal result
retirement to conceal a mutant that ignored reset while holding a result. That
failed attempt remains preserved. The corrected checker retains the original
case and adds reset while a result is held with ready low, mandatory
`reset_stalled_result` coverage, and omission regressions. The previously missed
mutant now fails actual assertions. Specification, reference and mutant sources
were unchanged; this is fresh qualification rather than a revised old verdict.

## Evidence limits

This checkpoint establishes supervised fixture admission and regression success,
not generated-design success, routed PPA gain or a held tier. Behavioral tests
establish arithmetic and timing
semantics; they cannot prove an implementation performs sequential iterative
arithmetic instead of delaying a combinational result. Retain source review of
the implementation for an iterative-structure claim. No operator ban or new
runtime gate is introduced. Selected widths do not prove the whole supported
domain, formal equivalence or board timing.
