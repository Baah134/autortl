# Golden-model verification

A golden model is a small Python reference for the specified behavior. It is an
oracle for expected data, not an implementation seed or a proof by itself.
AutoRTL checks concrete specification examples, executes the model in a bounded
isolated worker, generates a Verilog testbench, and requires a deliberately faulty
RTL implementation to trigger a behavioral assertion before trusting the testbench.
Infrastructure failures and watchdog expiry do not qualify as detecting a fault.

## Time and reset

The harness gives the Python model an asserted-reset prefix followed by normal
payload rows with reset deasserted. Clock edges are implicit. Fixed-latency models
return the logical result for each input step; the Verilog testbench applies the
specified cycle offset. Do not add a second pipeline delay inside the reference.

For a ready/valid scoreboard, each Python step describes one accepted transaction
and returns its eventual payload. It does not model queue occupancy or output
scheduling. The Verilog scoreboard drives backpressure, checks order and stalled
payload stability, and records acceptance cycles. Output transfers earlier than
`latency` cycles after input acceptance fail; stalls may increase that age. A
zero-latency contract permits same-edge forwarding. The finite drain budget reserves
latency per transaction plus backpressure allowance; it is not a liveness proof
for arbitrary initiation intervals or unbounded internal stalls. This minimum transfer age does
not by itself prove exact capacity, readiness, or earliest valid assertion.

## Independent authority and limits

Examples anchor the generated Python reference but are not automatically inserted
as separate temporal sequences into the generated RTL stimulus. Generated random
stimulus and startup reset provide partial coverage. They do not establish every
reset kind, midstream reset behavior, or all possible sequences. A generated oracle
and generated implementation can share a misunderstanding.

Independent curriculum testbenches therefore check counter wrap/enable/reset,
encoder priority/validity/registered timing, and streaming capacity/readiness/
ordering/backpressure/reset. Qualify these with supervised controls and distinct
compiling faults, retaining raw simulator logs and process receipts. Passing tests
is bounded evidence for these contracts, not formal equivalence or universal
correctness. Adding a fixture alone establishes no measured simulation result.


## Reproduction commands

Use fresh output paths and your installed Vivado bin directory:

```powershell
python scripts/check_build_tbs.py --bin-dir $vivadoBin --output runs/build-tb-check
python scripts/check_build_tbs.py --suite skid --bin-dir $vivadoBin --output runs/skid-tb-check
python scripts/check_generated_build.py --run runs/my-build --tb curriculum/tier2/skid_buffer_build/skid_buffer_tb.v --output runs/my-independent-check
```

Build without `--tb` to exercise generated oracle/testbench verification alone.
With a single-child build, `--tb` alone uses the existing trusted-only path.
Add `--generate-golden` to run both:

```powershell
python run.py build --spec curriculum/tier2/skid_buffer_build/design_spec.json --tb curriculum/tier2/skid_buffer_build/skid_buffer_tb.v --generate-golden --top skid_buffer
```

The generated unit TB and adapted independent TB both gate child generation and
rerun after repairs. The failing TB and diagnostics reach the child repair worker;
infrastructure failures stop without RTL mutation. Both TBs must detect sabotage.
The original supplied top TB stays unchanged for baseline and every optimization
candidate. Separate workdirs preserve both source/TB identities and tool receipts.
For a multi-module hierarchy, the supplied TB is integration authority; it cannot
be mechanically renamed into an arbitrary child's independent testbench.

`check_generated_build.py` separately verifies the exact saved winner and declared
children. This additional final check does not rerun synthesis or establish the
quality of an unqualified user-supplied testbench. Golden execution is capped at
10000 steps, including reset initialization; custom data counts must reserve room
for the specified reset prefix. The configuration flag is frozen on resume and
changes curriculum cohort identity. Legacy schema1 configs default only this new
field to false; all previous required fields remain mandatory.


## Qualification sensitivity and missed faults

Qualification tries a fixed bounded portfolio: the original operator/increment
fault, interface-preserving stuck-zero outputs, then stuck-one outputs. The
unchanged control must pass and at least one fault must emit retained assertion
detail and a failure verdict. Missed probes remain in qualification.json with
source/TB/log identities; they are not silently relabelled as detected.
Infrastructure/unknown failures stop the portfolio. No testbench regeneration
occurs during qualification. This minimum sensitivity check does not establish
complete behavior coverage. In particular, a payload scoreboard can miss readiness
and capacity faults that the independent queue TB must detect.

An exhausted module tool failure reports build_blocked with its failure kind,
stage, diagnostic and testbench. It never enters RTL rejection history or triggers
RTL repair. Budget exhaustion remains a separate outcome. Start a fresh experiment
when changing runtime implementation; do not reset an interrupted trial's budgets.
