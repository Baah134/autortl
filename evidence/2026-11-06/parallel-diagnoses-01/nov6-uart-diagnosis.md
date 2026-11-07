# UART signoff diagnosis — November 6, 2026

Inspected canonical `C:/Users/prince.baah/Downloads/autortl-work` at
`e61665c53552788f6d3690f4f1ddb8a94fecad93`. No canonical edits, leases,
simulators, synthesis, hardware or model calls. The source freeze stays intact.
This is diagnosis, not a new passing UART run or a regrade of old results.

## Finding

The three signoff4 tier3 UART failures share a planner sampling-contract error:
clocked children were declared `fixed_latency: 0`, which the harness explicitly
defines as combinational, while their Python models return outputs **after the
current clocked state transition**. Their generated benches instead compare
before that transition. Fixing RTL repeatedly cannot reconcile those contracts.

| Run directory under logs/ | Failing child | Declared latency | Recorded calls / tool seconds / wall seconds | First candidate mismatches explained by sample phase |
|---|---|---:|---|---|
| signoff4-t3-01/tier3_6h_ol6d8/uart_fifo_build | sync_byte_fifo | 0 | 7 / 30.25 / 199.27 | Exactly 62/62 |
| signoff4-t3-02/tier3_cn0rc15p/uart_fifo_build | uart_tx | 0 | 11 / 62.02 / 257.14 | Exactly 3/3 |
| signoff4-t3-03/tier3_70q5kppw/uart_fifo_build | sync_byte_fifo | 0 | 7 / 27.93 / 179.47 | 62/69; seven additional empty-data checks |

Each stops as `module_failed` before mechanical-top integration, independent
top verification, routing or optimization. Budgets allow 30 calls, 90 tool
minutes and 150 wall minutes: none exhausted. The saved first-candidate tool
receipts contain successful exited xvlog/xelab/xsim processes, and the logs show
ordinary behavioral assertions, not infrastructure failures. The golden models
were generated and validated; this is not golden generation timeout/budget loss.
Run02's FIFO uses latency1 and passed its unit control/mutant qualification;
its UART then fails with latency0. In runs01/03 the UART child is never reached.

## Evidence and bounded probe

For each run above inspect `design_spec.json`, `run_summary.json`, `budget.json`,
`events.jsonl`, `journal/*/{started,completed}.json`, and the failing child's
`modules/<child>/{golden.py,stimulus.json,<child>_tb.v}` plus
`candidate_standard_0/{<child>.v,sim_log.txt,tool_exit_records.log}`.
The archive counterparts are under
`evidence/2026-11-02/signoff4-t3-0N/run/<tier-directory>/uart_fifo_build`.

`autortl/tbgen.py:3` defines latency0 as combinational. At line239 the driver
waits for a posedge only if latency is positive. Actual saved latency0 benches
drive at a negedge and check after #1 without an intervening posedge. Saved
FIFO models enqueue/dequeue first, then return new occupancy/head; UART's model
accepts a byte first, then returns start-bit0/ready0.

Example: input row1 offers255 to an empty FIFO. The current-row oracle expects
valid1/data255. At that row's pre-edge comparison a correct synchronous FIFO
still has valid0/data0. Likewise UART row1 expects start0/ready0 before the
accepting edge actually occurs. Run02's three raw failures are index1 ready,
index1 tx and index17 tx, exactly the phase changes predicted independently.

Reproduction, requiring only Python's standard library:

```
C:/Users/prince.baah/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe work/nov6_uart_probe.py
```

`work/nov6-uart-probe.json` retains the result and hashes of inspected inputs.
The probe does not execute generated Python or RTL: independent queue and UART
age models reproduce all103 saved expected rows in each failing child. Sampling
their previous state predicts exactly the first candidate's assertion set in
runs01/02, and62 assertions in03. It asserts independent post-edge agreement
and zero recorded process exits; no simulator was launched. This proves the
sample-phase explanation for those traces, not full RTL correctness.

Run03's other seven checks concern `data_out` while empty. Its candidate reads
uninitialized/stale memory unconditionally (`assign data_out = mem[rd_ptr]`),
while oracle/examples require0. The module behavior does not define empty data,
so there is also an underspecified child contract. Do not mask or delete checks
to get a pass: planner behavior, examples and generated RTL must agree.

Run01's later repair illustrates harm from misdiagnosis: candidate3 makes
out_valid/data combinationally depend on in_valid/data and allows full-queue
acceptance on a dequeue. Both contradict its registered-occupancy/requested
k+1 frame-start behavior. The gate correctly rejects it; this is not a reason
to accept a final failed candidate.

## Successful hardware run is compatible with this diagnosis

`evidence/2026-11-01/explore-tier3-08/run/uart_fifo_build/design_spec.json`
declares **latency1 for both byte_fifo and uart_tx** with the same synchronous
queue and accepted-edge UART behavior. That gives post-edge comparison and led
to the winner used in the million-byte echo. Hardware board parameters were
changed in a handwritten wrapper; forcing those parameters into this fixture
would not fix pre-edge sampling and would change the task.

## Smallest justified next change (not implemented)

Clarify `SPEC_PROMPT` (`autortl/prompts.py:84`) with the actual fixed-latency
sampling contract: stimulus at falling edge; latency0 checks before the next
rising edge; latency1 checks after that edge. A cycle-by-cycle state machine,
counter or registered-state FIFO returning the current step's post-edge outputs
uses1, even if its head is first-word-fall-through. FWFT is not combinational
current-input acceptance. Keep scoreboard semantics separate.

Add regressions for planner prompt rendering and a small executable comb0 /
clocked1 control pair: same saved stateful oracle versus pre-edge0 must fail,
post-edge1 must pass; combinational0 must remain valid. Include a renamed
stateful child so the fix is not UART-name-specific. An independent top test
must still reject true off-by-one frames, combinational bypass, early ready and
empty-data disagreements. Then one NEW budgeted UART build on the changed
identity determines whether clearer instructions help; never resume/regrade
these three spent runs.

Do not globally convert0 to1, reject every clock-bearing latency0 module,
infer sequential behavior using prose keywords, change default board values,
expand budgets or weaken the independent testbench. The existing runtime phase
definition is consistent; the immediate justified change is exposing it to the
planner, not adding a new role, schema or verification mode.
