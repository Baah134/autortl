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
and the separate Codex-generated counter trial. Complete build/optimization
campaigns using the new journal still need live end-to-end validation. Passing
mocked recovery tests does not establish autonomous optimization improvement.

Reproduce the live testbench cases:

```powershell
python scripts/check_tbgen_cli.py --bin-dir C:/AMDDesignTools/2025.2/Vivado/bin --output runs/tbgen-001
```
