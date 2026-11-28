# AutoRTL results in detail

Moved from the README on November 15, 2026. The front page keeps a summary;
every number here links to its evidence.

## What the agent actually changed

In the FIR run, the baseline core passed the backpressure signal through a
three-stage combinational chain and multiplied by constants:

```verilog
wire ready3 = !valid3 || out_ready;
wire ready2 = !valid2 || ready3;
wire ready1 = !valid1 || ready2;
assign in_ready = ready1;
...
(x_wide * 16'sd3) - (history1_wide * 16'sd5) + (history2_wide * 16'sd7) - (history3_wide * 16'sd2)
```

The verified winner tracks pipeline occupancy in a register instead, which
cuts the input-ready path to a single gate, and it uses shift-and-add terms:

```verilog
assign in_ready = !full || out_ready;
...
full <= next_valid1 && next_valid2 && next_valid3;   // inside the clocked block
...
wire signed [15:0] x_times3        = (x_wide <<< 1) + x_wide;
wire signed [15:0] history1_times5 = (history1_wide <<< 2) + history1_wide;
wire signed [15:0] history2_times7 = (history2_wide <<< 3) - history2_wide;
```

Full sources: [baseline core](../evidence/2026-10-26/generated-signed-fir4-attempt-01/run/modules/signed_fir4_core/signed_fir4_core.v)
and [winner](../evidence/2026-10-26/generated-signed-fir4-attempt-01/run/signed_fir4_best.v).
The [FIR case study](CASE_STUDY_FIR.md) explains the routed path,
resource tradeoff and independent hardware checks.

## Verified results

| Design | Result | Verification |
|---|---|---|
| Signed stateful FIR filter | 78 → 52 LUTs · setup −0.327 → +0.169 ns · hold +0.106 ns | Independent 800-cycle test |
| Elastic dot product | 328 → 20 LUTs · 4 DSPs · setup +0.155 ns · hold +0.206 ns | Independent 852-cycle test |
| Three-module pipelined dot product | 325 → 17 LUTs · 4 DSPs | Independent 685-cycle test |
| Iterative divider (8-bit) | 38 → 26 LUTs · setup +0.315 ns · hold +0.129 ns | Independent test of the saved winner |
| FIFO timing recovery | Setup −0.931 → +0.108 ns · hold +0.076 ns · 22 LUTs / 13 FFs | 50,000 transactions on the board |
| Packet-tagged FIFO | 23 LUTs / 31 FFs · setup +0.078 ns · hold +0.106 ns | Independent test of the saved winner |
| UART transmitter (harness-built) | 40 → 24 LUTs | 1,000,000-byte line-rate stream on the board |
| Fault-qualified verification | 27 FIR, 18 elastic dot-product and 20 divider faults detected | Correct controls passed |
| UART receiver + FIFO + error counters (4 modules, tier 5) | Setup −1.166 → +0.443 ns · 70 → 55 LUTs after timing recovery | Independent fault-qualified test · 1,000,000-byte echo on the board |
| UART transmitter + FIFO from a prose request (tier 3) | Setup −1.188 → +0.179 ns · 170 → 36 LUTs / 117 → 27 FFs | Independent fault-qualified test · 1,000,000-byte echo on the board |
| AXI4-Lite register block (tier 5, out of context) | Built from specification: 95 LUTs · setup +5.441 ns | Independent fault-qualified test |
| 16-tap symmetric FIR at 150 MHz (tier 5, out of context) | 394 → 148 LUTs · 9 DSPs · setup −10.25 → +0.751 ns | Independent fault-qualified test · 50,000 transactions on the board at 100 MHz |
| RISC-V RV32I core, 6 modules (tier 6, out of context) | 2,093 → 1,530 LUTs / 4,356 → 3,325 FFs · setup +0.916 ns | ISA-level checker, fault-qualified · 50,000 programs run on the board |
| AES-128 encryption core (tier 6, out of context) | 9,108 → 614 LUTs · setup −9.76 → +2.216 ns | 15 FIPS-197/AESAVS known answers · 50,000 blocks encrypted on the board |
| CORDIC sin/cos, 4 modules (tier 6) | Setup −1.757 → +0.076 ns · 194 LUTs | Bit-exact model · 50,000 angles on the board |
| SPI master (tier 4) | 25 → 19 LUTs / 37 → 33 FFs · setup +0.354 ns | Independent fault-qualified test · 50,000 exchanges on the board |
| CRC-16 stream, arbiter + register file (tier 4) | Built from specification: 16 and 42 LUTs, timing met | Independent fault-qualified test · CRC-16 on the board |
| Curriculum tier 0 (counter, mux4) | Held: 3 consecutive qualifying runs · counter 55 → 31 LUTs | All mandatory gates |

Standalone results target 100 MHz with ideal zero I/O delays unless marked
otherwise; FIR16's 150 MHz result is out of context. Physical-board checks use
a 100 MHz shell with board pin constraints. The dot products use DSP slices.
Details: [hardware targets](TARGETS.md).

A controlled public-task comparison against a single model invocation
(`final-02`, registered November 20, 2026, before grading) found the single
call better: on 40 VerilogEval spec-to-RTL tasks with three trials, one call
passed 94.1% and the full harness 86.1% (difference -9.2 pp, 95% CI -19.2 to
-0.8), with 7.4 times the model calls per pass for the harness. The harness
without mutation qualification of its generated testbenches scored 84.7%, no
material difference from the full harness (+0.4 pp, 95% CI -5.0 to +5.8). About one in ten designs the harness accepted failed the official
testbench ([results](../evidence/2026-11-21/final-02-results/README.md)).

Failure review (after grading; the registered verdict stands unchanged):
- Most of the gap comes from the extra step of rewriting the prose into a
  typed spec. On Prob066 and Prob139 the planner added or shifted behaviour
  the request never stated (a reset that clears a history register, an input
  sampled one cycle early), and the oracle, generated testbench and RTL all
  followed it, so the wrong designs were accepted. Arm A read the prose
  directly and passed. Taxonomy: `planner_spec_error_shared_by_oracle_and_rtl`.
  A later closed-book single call with Gemini 3.8 Flash-low (`flash-03`,
  85.8%) failed both tasks with the same mismatch counts, so these readings
  are ambiguities of the task text, not errors only the harness makes
  ([results](../evidence/2026-11-26/flash-03-results/README.md)).
- Prob131 (multi-module plan without a trusted testbench) and Prob153
  (golden-model observation phase) ended without a design in most harness
  trials; both are fixed and tested since, but not counted here.
- Two tasks, Prob093 and Prob149, have official references that contradict
  their own prose; every arm fails them, and they account for 5 of the full
  harness's 11 false acceptances (`official_reference_contradicts_request`).
- One correct design (Prob027, full) failed only because the Icarus-based
  grader rejects a Vivado synthesis attribute (`grader_rejects_vendor_attribute`).

**Fmax.** Out of context, the six winners close at 181.8 MHz (FIR) to
425.5 MHz (packet FIFO). The harness reports both the board-level
I/O-constrained slack it accepts on and the register-to-register slack of the
same routed design ([Fmax study](../hardware/basys3/fmax/README.md)).

Evidence: [signed FIR](../evidence/2026-10-26/generated-signed-fir4-attempt-01/README.md),
[FIR fault qualification](../evidence/2026-10-25/signed-fir4-admission-attempt-01/README.md),
[second FIR run](../evidence/2026-10-26/generated-signed-fir4-attempt-02/README.md),
[generated-verifier audit](../evidence/2026-10-26/fir4-driver-comparison-01/README.md),
[elastic dot product](../evidence/2026-10-25/generated-elastic-dot4-attempt-02/README.md),
[three-module dot product](../evidence/2026-10-24/generated-dot4-attempt-01/README.md),
[divider](../evidence/2026-10-23/generated-divider-attempt-01/README.md),
[FIFO](../evidence/2026-10-22/generated-fifo-attempt-05/README.md),
[packet FIFO](../evidence/2026-10-22/generated-packet-attempt-01/README.md),
[Fmax](../evidence/2026-10-29/fmax-characterization-01/README.md).

## Hardware validation on a Basys 3

[`hardware/basys3/harness_winners`](../hardware/basys3/harness_winners/README.md)
runs every harness winner on the board through one generic, tested shell:

| Design | On board vs model | Winner LUT / FF / DSP on board | Harness-measured |
|---|---|---:|---:|
| Signed FIR | 50,000/50,000 | 51 / 67 / 0 | 52 / 67 / 0 |
| Elastic dot product | 50,000/50,000 | 20 / 20 / 4 | 20 / 20 / 4 |
| Pipelined dot product | 50,000/50,000 | 17 / 18 / 4 | 17 / 18 / 4 |
| Iterative divider | 50,000/50,000 | 26 / 30 / 0 | 26 / 38 / 0 |
| Packet FIFO | 50,000/50,000 | 22 / 29 / 0 | 23 / 31 / 0 |
| Sync FIFO | 50,000/50,000 | 21 / 13 / 0 | 22 / 13 / 0 |

- **Independent models.** Each design is checked against a Python model
  written from the frozen specification, not from the harness's own oracle.
- **Real backpressure.** An LFSR traffic shaper creates the valid/ready stress
  that UART traffic alone never would. Coverage counters prove it happened,
  and each design's injected fault must make its simulation fail.
- **Explained differences.** The divider's 8-FF difference turned out to be
  `opt_design` replicas that exist only when it is built standalone
  ([analysis](../evidence/2026-10-28/divider-ff-replica-analysis-01/README.md)).
- **Replayable.** The tested bitstreams are archived and tied by hash to the
  hardware runs, so a board and a fresh clone can rerun every check without
  synthesis. A replay reproduced all six results exactly
  ([replay](../evidence/2026-10-28/basys3-bitstream-replay-01/README.md)).

### Harness-built UART transmitter

The harness generated a UART transmitter from a typed specification written
for the board (34 → 22 LUTs, 14 model calls, 9.4 minutes). The unedited file
drives the board's TX pin and echoed 100,000 of 100,000 bytes, while a
wrong-baud control failed as required. No human-written RTL is in the
transmit path ([design](../hardware/basys3/harness_built/uart_tx/README.md),
[evidence](../evidence/2026-10-29/harness-uart-tx-01/README.md)).

Line-rate testing on the board then refined the specification itself: a
stop bit shortened by 1/16 tolerates the PC's slightly faster clock. The
harness regenerated the transmitter from the revised spec, and it streamed
1,000,000 bytes with 0 errors
([evidence](../evidence/2026-10-29/harness-uart-tx-v2-01/README.md)).

<details>
<summary>Board bring-up history</summary>

- **UART echo.** The board path was proven first with a hand-written echo
  ([`uart_echo`](../hardware/basys3/uart_echo/README.md)), tested at full line
  rate: it streamed 1,000,000 bytes with zero loss, and each design rule it
  depends on has a simulation that fails when the rule is reverted
  ([evidence](../evidence/2026-10-28/basys3-uart-echo-02/README.md)).
- **FIR alone.** [`fir4_on_board`](../hardware/basys3/fir4_on_board/README.md)
  ran the FIR winner, byte-identical to the verified file, behind a
  hand-written UART shell: 100,000 samples matched across 4 restarts, a model
  with one wrong coefficient failed on 4,965 of 5,000 outputs, and the build
  had 0 warnings with +2.718 ns setup slack
  ([evidence](../evidence/2026-10-28/basys3-fir4-01/README.md)).

</details>

## How the harness improves itself

- **Every failure mode becomes a rule.** Each problem a run surfaces gets an
  entry in the error taxonomy ([`data/taxonomy.yaml`](../data/taxonomy.yaml))
  before its fix lands, so the harness, its prompts and its repair hints grow
  with every campaign.
- **Verifiers are measured, then strengthened.** Signed boundary values,
  legal idle traffic and off-edge reset pulses raised the generated
  testbenches' fault detection from 18 to 22 of 27 injected faults with no
  extra model calls, and the independent checker catches all 27.
- **Candidates cannot game the tests.** Before any tool runs, model-written
  RTL is rejected if it uses system tasks, preprocessor directives, synthesis
  pragmas, hierarchical references or escaped identifiers, the constructs a
  design could use to fake a pass or show simulation and synthesis different
  logic. A candidate that stops instantiating a component the trusted
  testbench checks is rejected too
  ([evidence](../evidence/2026-10-29/harness-uart-tx-02/README.md)).
- **Every check must catch a fault.** New checks ship with a deliberately
  broken design that they are required to fail.
- **Independent review.** Harness changes, and the harness as a whole, are
  reviewed by separate agents; each confirmed finding gets a taxonomy entry
  and a regression test before it is fixed.
- **New tiers are qualified first.** Tier 4 (a CRC-16 stream, an SPI master
  and a two-module arbiter with a register file), tier 5 (an AXI4-Lite
  register block, a UART receiver with a FIFO, and a 16-tap symmetric FIR at
  150 MHz) and tier 6 (an RV32I CPU, AES-128 and CORDIC) entered the
  curriculum only after each independent testbench passed its reference
  design and caught all ten planted faults
  ([tier 4](../evidence/2026-10-29/tier4-qualification-01/README.md),
  [tier 5](../evidence/2026-10-30/tier5-qualification-01/README.md),
  [tier 6](../curriculum/tier6/README.md)).
- **Each hard run teaches the roles something.** Runs on tiers 3 to 5 turned
  into concrete harness rules: optimizing children and top as one unit when an
  independent testbench guards the top, keeping partial timing progress,
  reporting every violated testbench rule to the fixer, and routing spec
  mistakes back to the planner with the exact ports to fix
  ([tier 4](../evidence/2026-10-30/explore-tier4-02/README.md),
  [tier 5](../evidence/2026-10-30/explore-tier5-01/README.md)).
- **The evidence is audited.** CI checks archived SHA-256 bindings against
  committed bytes and requires explicit records for historical losses
  ([publication policy](PUBLICATION.md),
  [audit](../evidence/2026-10-28/evidence-integrity-01/README.md)).
