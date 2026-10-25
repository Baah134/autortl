# Three-child dot-product build fixture

## Recorded validation

The independent checker admitted its control and all 12 behavioral mutants:
**13/13 expected verdicts**, with actual assertion failures for each fault.
The generated build's exact saved top plus three children independently passed
**685 cycles**. DONE reuse and eight restored tamper probes preserved recorded
source, budget, router and file identities.

| Resource / routed result | Baseline | Winner |
|---|---:|---:|
| LUTs | 325 | 17 |
| Slice FFs | 52 | 18 |
| DSPs | 0 | 4 |
| Setup slack (ns) | 0.087 | 0.354 |
| Hold slack (ns) | 0.202 | 0.254 |

This is a fabric-to-DSP tradeoff, not a reduction in every resource or power.
Slice FF counts exclude registers internal to the DSP primitives. The accepted
editable top inlined the computation under the explicit contract allowance;
the frozen child sources were preserved. This is not evidence that only rewiring
the original three instances produced the measured resource change.
Reported total power was 0.157 to 0.158 W. Measurements use Vivado 2025.2,
xc7a35tcpg236-1 and a 10 ns clock with ideal zero boundary I/O delays.
The original run used 11 model calls and 235.344 charged tool seconds.
It needed one model repair after the mechanical top lacked a timescale;
the original failure is retained and is not relabeled as a clean first pass.

See [checker admission](../../../evidence/2026-10-24/dot4-admission-01/README.md),
[generated build and independent replay](../../../evidence/2026-10-24/generated-dot4-attempt-01/README.md),
and [controlled timescale repair](../../../evidence/2026-10-24/top-timescale-order-01/README.md).
This is one verified design experiment, not formal proof, exhaustive fault
coverage, a held tier or a controlled comparison of models.

## Contract and wiring

`dot4_pipeline` mechanically wires three generated children:

| Child | Unsigned data inputs | Registered output |
|---|---|---|
| dot4_pair01 | a0,b0,a1,b1: 8 bits each | pair01_sum: 17 bits |
| dot4_pair23 | a2,b2,a3,b3: 8 bits each | pair23_sum: 17 bits |
| dot4_merge | left_sum,right_sum: 17 bits each | dot_result: 18 bits |

Connect pair01_sum to left_sum and pair23_sum to right_sum explicitly. Only
clk/rst share external names across children; all eight operand names are
unique, avoiding accidental mechanical auto-binding of both branches.

Each child registers its result at a rising edge. Synchronous active-high rst
clears its output. Outputs hold between edges; no handshake or enable exists.
Pairs compute a*b+c*d exactly, maximum 130050. The merge accepts its complete
independent 17-bit input domain, maximum 262142. The integrated maximum 260100
is smaller. Neither operand signedness nor addition carry may be discarded.

Input before edge k appears after edge k+1: two sampled edges, with one result
per edge once filled. A reset edge discards both stages. First released edge
produces zero; the following edge produces the first released input's result.
A reset pulse spanning no rising edge has no effect on retained pipeline state.

Typed children declare latency 1/known=true. No aggregate top annotation is
invented: existing mechanical propagation only covers a single transparent
child. The independent TB checks the required top two-edge behavior.
Module goldens should return current-sample arithmetic; the driver owns delay.

## Independent checker

`dot4_pipeline_tb.v` delays direct mathematical dot products in separate
reference state. It never reads DUT internals or uses DUT partial sums.
Directed checks isolate every term, both branches, pair/final carries,
unsigned high bits, all-zero/all-maximum and asymmetric vectors. It adds 256
directed patterns and 400 deterministic random samples, continuous traffic,
occupied resets, off-edge hold checks and final drain.

A short reset pulse entirely between rising edges followed by another sample
detects asynchronous clearing of a hidden partial-sum register. Checking only
top output during an asserted reset would miss that child fault.

A separate `dot4_merge` instance checks its full declared domain, including
131071+131071=262142. Coverage counters, X-safe comparisons, a watchdog and
completion of both checkers are required before the enclosing verdict.
Live checker admission is recorded above; it does not establish exhaustive coverage.

## Independent admission cases

The reference is qualification material only, never a generated seed or winner.
`qualification/cases.py` prepares a control plus 12 distinct compiling
behavioral faults:

1. Drop a product.
2. Truncate pair carry to 16 bits.
3. Truncate final carry to 17 bits.
4. Treat an unsigned operand pair as signed.
5. Bind the second branch to the first branch's external inputs.
6. Duplicate one partial sum at the merge.
7. Remove the merge register using combinational logic.
8. Add an extra merge pipeline stage.
9. Delay only one pair branch by one cycle.
10. Make one pair's reset asynchronous.
11. Ignore the merge's reset.
12. Leak a current input bit into the output between clock edges.

No commutative swap is counted as a fault. Wiring faults alter only a prepared
wrapper copy; other faults alter qualification child source. Exact replacement
targets must occur once and all source tuples must remain distinct.
`materialize_cases(output)` creates a fresh directory, source/TB files and raw
SHA256 identities; it launches no tools. Requalification is required after changing checker or fault sources.

Admission requires actual control PASS and concrete behavioral assertion
failures for every mutant. Compiler failures, watchdogs, absent verdicts and
infrastructure errors are not kills. Preserve misses rather than weakening tests.

## Suggested invariant checks and integration sequence

- Schema/lint: three unique children, exact unsigned widths, two connections,
  no dangling or multiply-driven boundary; wrapper retains eight input bindings.
- No aggregate top latency header; correct per-child declared latency.
- Exactly 13 unique cases and 12 mutations, each edit target unique.
- All prepared TB bytes identical; manifest hashes match raw bytes; existing
  output directory rejected rather than overwritten.
- Child and wrapper module/port signatures preserved for every mutation.
- Arithmetic boundaries 130050/260100/262142 and asymmetric isolated terms.
- Existing multichild journals: completed-stage replay and child-source tamper
  rejection. Add harness changes only if a concrete missing behavior is reproduced.

Then review -> qualification compile/simulation -> retain all evidence -> bounded
generated build with generated module graders and this independent top TB ->
exact final-source replay and routed measurements. Pure fixture tests establish structural/materialization invariants only. Actual
compilation and simulation evidence is retained separately in the linked archive.

Current build optimization freezes children and edits the mechanical top. This
fixture primarily demonstrates generated arithmetic composition and verification;
retain exact child identities during wrapper optimization and disclose any DSP
mapping tradeoff rather than interpreting LUT savings as a universal cost gain.
