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
interface and known-latency checks repeated before compilation and simulation.
Compile and simulation design failures share max_fix_attempts; zero permits no
repair. Each changed answer has its own repair_NNN directory with source/logs.
Infrastructure or unknown failures never consume RTL repair attempts.

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
Later typed counter, encoder and streaming builds and an accepted counter
optimization have retained live evidence; see PROGRESS and the public README
for their exact source revisions and limits. Hard process-kill recovery and
accounting remain separate validation requirements.

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


## Completed verification dependencies and outcome

Before publishing a winner, the harness validates each retained verification
input manifest against its originally recorded source and testbench digests.
This includes generated child RTL and cached or source-identical Doctor evidence.
Changing or deleting a companion after DONE invalidates reuse, even when its
manifest file itself is unchanged. Malformed or missing lineage blocks completion.
Journal artifact copies retain their separate replay checks; obsolete journal
snapshots are not treated as new live simulation input manifests.

Source and JSON IO use UTF-8 explicitly, including repaired candidates and Doctor
trials, so Windows default encodings cannot change source/evidence comparisons.

The summary and CLI expose timing_closed and improvement_kind. Status done and
exit zero mean the bounded experiment completed; timing_closed must also be true
before calling a design timing closed. A verified feasible candidate may replace
a known timing-failing baseline even with higher area, labeled timing_recovery.
Among timing-feasible designs, promotion still requires strict improvement of
the selected objective. Missing or contradictory timing cannot establish recovery.
All behavior, metric, receipt and final evaluation gates continue to apply.


## Physical feedback and resolved build contracts

Role evidence retains a bounded violated-path excerpt from the same original
report bytes as its SHA. It identifies setup/hold from the path's own fields;
report-wide WNS/WHS are distinct measurements. Missing path identity stays
unknown. Context does not replace metric or process-exit gates.

Build optimization retains the complete validated resolved specification within
an explicit size budget, preserving defined behavior and any explicit
unspecified cases. Oversized semantic context fails rather than silently dropping
qualifiers. Standalone optimization remains governed by its frozen source.

Non-adopted Doctor trial observations reach subsequent planning as advisory
facts, separately from candidate/incumbent metrics. Their original source/report/
script digests and the resolved build-spec digest are protected at finalization
and DONE. Merely improved negative slack never establishes timing recovery.

Exact unchanged RTL surgery is skipped only when source bytes, verified prior
inputs/exits and the exact current default synthesis flow match. Changed or
unknown flow options and intentional physical-only trials still run. A skipped
trial records no_source_change/tools_ran=false and creates no new measurement.

## Top latency annotation authority

Optimization annotation requirements come from current-top
declared_latency.known/cycles, not child metadata alone. Validated complete
transparent single-child wrappers inherit the typed child contract annotation;
arbitrary aggregate tops remain unknown. Scoreboard latency denotes minimum
accepted-transfer age, not a fixed delivery deadline under stalls. Unknown
metadata does not waive defined behavior, static checks or simulation. FIFO04's
false reviewer requirement remains archived and is never retroactively accepted.

Annotation parsing uses real standalone line comments attached to the selected
module header or within that module. It masks block comments, quoted strings
and escaped identifiers, and never takes another module's declaration. Equal
duplicates are allowed; conflicting, malformed or out-of-range (0..1024) selected
annotations are static design failures. The optional no-top client form returns
unknown for multi-module files. This is a lexical supported subset, not a
Verilog preprocessor or elaborator; annotations are never behavioral proof.
