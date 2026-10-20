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
zero-latency contract permits same-edge forwarding. This minimum transfer age does
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

Build without `--tb` to exercise generated oracle/testbench verification. Supplying
an independent TB directly selects the trusted-test branch and bypasses oracle
generation for a single-module build. The final check is a separate step and uses
the saved `<top>_best.v` and exact declared child files. It does not rerun synthesis.
Golden execution is capped at10000steps, including reset initialization; leave room
for the specified reset prefix when choosing a custom stimulus count.
