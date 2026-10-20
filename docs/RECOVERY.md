# Recovery and validation

New runs save `config.json`, immutable input copies and their hashes,
`runtime.json` (implementation/Python/tool identity), `budget.json`, `state.json`,
stage journals, events and tool evidence. Resume uses the saved configuration:

```powershell
python run.py resume --run runs/example
```

Resume configuration overrides are rejected. Completed model responses and
tool results are replayed from verified journal records. Their artifact copies
are checked before restoration; completed work is not charged again. Pure
orchestration decisions are rebuilt from the journal. An interrupted stage
without a completed record may run again; its previous spent budget remains.
This is at-least-once execution of unfinished work, not an exactly-once external
model or tool guarantee.

Modified frozen inputs, implementation/Python/tool identity, journal artifacts,
final source, final summary or retained final reports fail recovery explicitly.
Changes to original external input files do not alter the frozen run. Move a
development checkout between completed runs; existing run snapshots currently
contain absolute paths and should not be relocated during execution.

Infrastructure failures use bounded retries of the same tool stage and source.
Exhausted infrastructure rounds stop without RTL repair, design rejection or
stall history. A later explicit resume can retry an uncommitted blocked stage,
within remaining budgets. Design failures can invoke bounded repairs, with
interface and latency checks repeated before simulation.

Model workers expose typed provider failures. Bounded, credential-redacted
error events and diagnostic stderr are retained without ordinary generated
stdout. Quota/auth failures stop immediately; timeout/network retries remain
bounded. Exhausted failures save status `model_blocked` with role/code/diagnostics
and the previous best pointer. They do not create a design rejection. Resume
retries only uncommitted stages within the existing budget; restoring access
does not reset spent calls or time.

Typed JSON specs bypass model planning. Build mode generates/verifies child
modules, qualifies their testbenches and mechanically integrates the top.
Multiple modules require an independent top testbench. For a single module,
a supplied top testbench can be adapted to the child; generated verification
is used when no independent testbench is supplied. Tests cover these control
paths with deterministic model/tool fixtures.

Generated Python golden models run in a separate process with restricted
syntax, a minimal environment and deadlines. This supports pure bounded oracle
functions, not arbitrary Python libraries. It is defense in depth, not a
general operating-system sandbox for hostile programs.

Fixed-latency testbenches define latency0 as combinational and latency1 as the
first rising edge after falling-edge stimulus. Streaming scoreboards sample
accepted transfers before sequential updates, compare every data port, and
check output stability under backpressure. All cases have finite completion.

Live Vivado validation has exercised nine positive/negative testbench cases
plus five counter32 reference/mutation cases and the separate generated counter
trial. A real failed evaluator was resumed with one additional model call,
unchanged physical tool time and no repeated completed physical stages. Both
runs in that original failed cohort later reached DONE with baselines retained.
Full live build campaigns, process-kill recovery and accepted autonomous gains
still need validation; model-worker recovery does not prove those paths.

Reproduce the live testbench cases:

```powershell
python scripts/check_tbgen_cli.py --bin-dir C:/AMDDesignTools/2025.2/Vivado/bin --output runs/tbgen-001
```


## Windows checkpoint contention

Atomic writes flush a sibling temporary file and replace the target without
removing the previous checkpoint. Recognized Windows access/sharing contention
errors (5, 32 and 33) receive seven attempts with at most 0.63 seconds of bounded
backoff. Other errors fail immediately; exhaustion preserves the original error
and previous target. Cleanup cannot hide a failed write.

This protects the observed transient replacement boundary. It does not make an
external tool invocation and its later budget charge one transaction. A persistent
storage failure or hard process kill can leave tool work beyond the last saved
budget. Preserve its logs and do not claim exact accounting or silently treat
that work as free. Full process-interruption accounting remains a separate live
validation requirement.

## Process exit receipts

New invocations retain append-only logical history in tool_exit_records.log,
written by atomic replacement. Records separate actual returncode from the
driver code and status (exited, timed_out, launch_failed, cancelled). Successful
log markers cannot convert timeout or failed launch into success. Missing or
malformed evidence remains unknown/invalid; no older successful attempt replaces
a later failed attempt. No command arguments or tool output are copied into
receipts. Raw output remains in its separately hashed log.

Cache entries and DONE checkpoints retain receipt hashes. Changing or removing
retained receipts invalidates reuse. A physical-only Doctor trial can reuse
source-identical simulation evidence with explicit source, testbench, companion
source and original log identities. It does not pretend to rerun simulation.

Receipt persistence improves traceability. It does not make process execution
and budget charging a single external transaction, or prove hard-kill recovery.
