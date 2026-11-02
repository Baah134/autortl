# AutoRTL v4 — Design Document (single source of truth)

This document describes the intended architecture. Runtime code and retained
verification evidence establish implemented behavior; docs/HARNESS_REVIEW.md
records feature coverage, limits and simplification decisions.

## Thesis
The harness carries the intelligence; the models are replaceable function
calls. The goal is small, explicit model tasks backed by deterministic
verification and actionable repair feedback. Weak-model reliability is an
experimental target, not an established result. If the system only performs well with the best
model, the design has failed its own requirement.

Optimization contracts are rendered mechanically from frozen harness evidence.
Model roles do not negotiate or amend their verification requirements.

Structural interface checks preserve signedness, packed shape and symbolic
public-parameter declarations; see [interface contracts](INTERFACES.md) for the
supported schema and limits.

## The seven pillars
1. **Task decomposition into module contracts.** The planner's only creative
   output is `design_spec.json` (typed schema in `autortl/spec.py`). Each
   module is an independent generate-verify subtask. Top-level wiring is
   generated mechanically (`linter.top_verilog`) — zero LLM. A validated complete
   transparent single-child wrapper inherits that child's known latency contract;
   arbitrary module graphs receive no inferred aggregate numeric latency.
   Mechanical wrappers explicitly declare a 1 ns / 1 ps timescale before optional
   latency metadata, so elaboration does not depend on file order.
2. **Verification ladder.** static checks (ms) → xvlog (s) → unit sim →
   integration sim → synthesis. A candidate that dies at rung 1 costs
   milliseconds, not minutes.
3. **Golden models + generated testbenches.** Python oracle per module,
   qualified against the spec's IO examples first. Testbenches are generated
   code (tbgen.py) in two compare modes: fixed_latency (shift-register
   compare) and scoreboard (queue-based, for valid/ready). Pulse mode is
   deliberately stubbed.
   Scoreboard stimulus includes unique complete payload vectors from declared
   examples that explicitly assert input-valid and deassert the configured
   reset. Scheduling remains driver-owned; oracle outputs remain authoritative.
   Three existing corners and the seeded random tail are preserved. Signed-data scoreboard modules also receive six alternating
   minimum/maximum accepted payloads between examples and the random tail, with
   unsigned payloads zero and no change to driver scheduling or oracle semantics. This is
   payload coverage, not replay of example timing/state traces. Fixed-latency
   example sequences are unchanged; total stimulus plus reset remains bounded.
   Scoreboard traffic includes legal invalid bubbles/noise while preserving blocked
   producer offers. Sync-only reset pulses end before sampling edges, preserving
   oracle/queue state; occupied reset policy remains independently specified.
   The oracle runs in a restricted worker (golden_worker.py) with fixed
   budgets per invocation: 200,000 Python trace events (calls, lines and
   returns across one whole stimulus sequence), 100,000 allocation units, and
   1 MB of request and result JSON. The budget is not configurable per module.
   It bounds what one spec example can express. Both archived harness-built
   UART golden models (harness-uart-tx-02, harness-uart-tx-v2-01) run out
   between 2,500 and 3,000 cycles, about 70 to 80 events per cycle, so one
   frame at 868 clocks per bit (8,680 cycles) cannot be an example; a
   7,813-cycle example exhausted it. Long-period serial designs therefore
   keep spec examples short, about 2,000 cycles (the UART examples are frame
   prefixes of 869 and 1,737 cycles), and check full frames at real timing
   with an independent, mutation-qualified `--tb`
   (taxonomy `golden_budget_long_period_examples`;
   hardware/basys3/harness_built/uart_tx).
4. **Best-of-N (N=4)** with objective-weighted mutation prompts (bestofn.py),
   hash dedupe, deterministic selection: (rungs, timing feasibility, objective
   metric, resource tie-break, brevity). A verified timing recovery can use more resources; it is
   recorded separately from objective savings. While the incumbent is still
   timing-infeasible, a verified infeasible candidate with strictly better setup
   WNS (hold no worse than 0.05 ns) replaces it as `timing_progress`, and
   infeasible candidates rank by setup WNS; a feasible design always outranks an
   infeasible one, and progress is never closure (`timing_closed` stays false and
   curriculum acceptance still fails; taxonomy `infeasible_progress_discarded`).
5. **Error taxonomy** keyed on official Vivado message IDs
   (data/taxonomy.yaml). Unknown IDs: query Vivado's own help, log for
   curation. Severity promotion only — never demote.
6. **Skills** (.claude/skills/, Anthropic SKILL.md format) replace RAG.
   Conventions are law (always in system prompt); skills are optional
   expertise, matched protocol-first (skill_loader.py). Claude Code loads
   natively; harness injects for other backends.
7. **Resumable FSM orchestrator** (fsm.py) with budgets, caches, watchdog.
   Crash anywhere, resume from state.json.

## The six potholes and intended fixes (see handoff for verified status)
1. Bad blueprint → contract linter + stub elaboration before any generation.
2. Behavioral-vs-cycle-accurate → latency field + two compare modes;
   spec-is-law via `// @latency N` header when the current top declaration
   is known (mismatch = graded failure). Unknown annotation metadata is not zero
   and cannot justify a missing-header rejection. Typed child contracts still
   require numeric latency; scoreboard latency is minimum accepted-transfer age,
   with later delivery possible under backpressure.
3. Anchored horde → forced architectural mutation portfolios + dedupe.
4. Replan amnesia → contract-hash artifact cache; unchanged modules imported;
   max 2 replans with budget-forced degradation.
5. Pattern library square peg → protocol-first matching from spec metadata.
6. Timing gap → Timing Doctor: tool knobs (retiming/phys_opt) first, RTL
   surgery second (slack -0.5/-3.0 ns thresholds), replan last.

## The six defences (see handoff for verified status)
7. Testbench qualification by bug injection (tbqual.py) — the oracle must
   FAIL a sabotaged design before it grades anything.
8. Reset/X discipline — reset per spec + 2-cycle settle before comparing.
9. Infra-vs-design triage (triage.py) — infra failures never mutate the
   design or enter history. A third kind, target, covers an interface that
   cannot fit the configured device (see target capacity failures).
10. Metrics integrity gates (metrics_gate.py) — the lut_total:0 class of bug
    is fatal, never a silent score.
11. TCL injection boundary — LLM output only in .v files; paths sanitised.
12. Router stats — recording-only (llm/router_stats.jsonl) until ~10 runs.

## Provider architecture
`llm/routing.yaml` routes planner, generator, evaluator and timing doctor to
`codex.default`. A route entry is `backend.alias`. `llm/client.py` is the only
call path. It resolves the backend by name: `codex` (Codex CLI), `openai`
(OpenAI-compatible HTTP), or a user endpoint from the local endpoints file.
The earlier claude_code, nvidia_nim and openrouter adapters were removed.
`run.py --route` is rejected. With no `--model`, every role uses the Codex CLI
with the existing login and its configured default model. No API key is
required for that path.

**Codex CLI** (`llm/backends/codex_cli.py`). AUTORTL_CODEX_BIN names the
executable; otherwise `codex` must be on PATH. The alias `default` passes no
`--model`; any other alias is passed as `--model <alias>`.
Workers receive prompts over stdin in a temporary working directory with a
read-only sandbox and ephemeral session. The harness requires a completed
JSONL turn and nonempty final response. Usage is recorded when reported;
unknown model/cost stays null. Timeouts and cancellation terminate the owned
worker, including a Windows process-tree termination attempt. The adapter
enforces wall time, not the historical max_turns parameter. Read-only is not
a guarantee that the worker has no tools.

**OpenAI-compatible HTTP** (`llm/backends/openai_http.py`). One standard-library
POST to `<base>/chat/completions`. It is configured only by environment:
AUTORTL_OPENAI_API_KEY (required, sent as a Bearer token), AUTORTL_OPENAI_BASE_URL
(default `https://api.openai.com/v1`; local Ollama or vLLM servers work) and
AUTORTL_OPENAI_MODEL (used for `openai.default`). Redirects are refused, so the
key never reaches another host. Loopback hosts bypass any proxy. Responses are
capped at 16 MB. The key, prompt and system text are redacted from every error.
HTTP 401/403 map to auth, 429 to quota, 408 to timeout, 5xx and connection
failures to network, a malformed body to protocol, and any other refusal to
unavailable.

**User endpoints** (`llm/endpoints.py`). Endpoints live in
`endpoints.local.yaml` at the repository root (ignored by Git, outside the
hashed harness folders, so editing it never makes resume refuse) or the file
named by AUTORTL_ENDPOINTS; `llm/endpoints.example.yaml` shows the format. Each endpoint
has a name and a kind. Names are lowercase letters, digits, `_` or `-`, start
with a letter, have at most 32 characters, and cannot be `codex` or `openai`.
Unknown fields are rejected. The file never holds a key, only the name of the
environment variable that holds one.
- `kind: openai` takes `base_url` and optional `api_key_env`. It reuses the HTTP
  backend. It sends a key only when `api_key_env` names one, and it needs an
  explicit model (`<name>.<model>`).
- `kind: command` takes `argv` and optional `model_flag`
  (`llm/backends/command_cli.py`). The command runs as an argument list, never
  through a shell, from an empty temporary folder, with the prompt on stdin and
  the harness timeout. Only the endpoint's own model name reaches its arguments,
  through `model_flag`; `<name>.default` passes none. A timeout kills its process
  tree. AutoRTL does not sandbox a command; it should have no tools or
  permissions it does not need.

Every backend returns text plus metadata and raises the same typed codes:
CODEX_AUTH, CODEX_QUOTA, CODEX_NETWORK, CODEX_TIMEOUT, CODEX_PROTOCOL,
CODEX_UNAVAILABLE. The client retries timeout and network failures on the same
entry with exponential backoff (`max_retries_per_backend`, default 2). Auth and
quota failures stop the run as model_blocked, an infrastructure outcome. Any
other failure moves to the next chain entry. An empty answer is a protocol
failure. Every attempt is recorded in `llm/router_stats.jsonl`.

**Model pinning.** `run.py --model` sets RunConfig.model, and every role call
uses it. A plain alias (`--model <alias>`) keeps each routing entry's
backend and replaces its alias. A value whose prefix before the first `.` names
a built-in backend or a defined user endpoint, such as `openai.gpt-4o-mini` or
`ollama.llama3.1`, replaces the whole chain with that one entry. Any other
value is treated as a plain alias, except that a prefix within one edit of a
backend or endpoint name (two edits for names of six or more letters, ignoring
case), such as `olama.x`, is refused as a likely misspelling, and any dotted
value is refused while the endpoints file is unreadable. `run.py` checks this
before a run or resume starts and the client checks it on every call, so such a
value is never sent to Codex (`llm.client.check_model`,
mistyped_endpoint_routes_to_codex). The value must match
`[A-Za-z0-9][A-Za-z0-9._:/-]{0,119}`, so hosted IDs such as
`together.meta-llama/Llama-3.1-8B-Instruct` work (it stays one argument, never
a path); `default` alone is rejected because it would be the unpinned default.
The model is saved in config.json, and resume reads it from there.

**Model identity in the cohort.** The bench does not read back the model name a
backend reports (that goes only to router_stats.jsonl), so it records the
requested model, not an observed one. Without `--model`,
the campaign identity has `model_identity` null and status
`unobserved_cli_default`. When every entry names the same model, it records
that value with status `requested`, in the campaign identity and in every
entry's runtime_identity (entry_identity_omits_requested_model). When the
value's prefix names a user endpoint, it also records `model_endpoint_sha256`,
the SHA-256 of that endpoint's definition, so editing the endpoint starts a new
cohort. For the built-in `openai` backend the digest covers
AUTORTL_OPENAI_BASE_URL and AUTORTL_OPENAI_MODEL (never the key). An unreadable
endpoints file at the end of a campaign is recorded, not raised. The model is
also part of each entry's configuration in the cohort. The Codex CLI version is
not part of the cohort.

These are independent role invocations. The development-session coordinator
and its helper agents supervise integration; persistent runtime dialogue and
fully reliable FSM resume remain separate development work.

## Modes
- `optimize`: existing design+tb in, fixed contract rendered from frozen evidence.
- `build`: intent → spec → lint → stubs → per-module build → mechanical
  integration → flows into optimize as its baseline.
- `resume`, `bench` complete the CLI.
- `doctor` checks the machine and runs no design; see
  [environment check and offline demo](#environment-check-and-offline-demo).

## Post-build edit scope
A build hands its integrated design to the optimize loop in one of two modes,
decided by the harness, recorded as `edit_scope` in harness_facts.json, the
fixed contract, state.json and run_summary.json, and checked on resume.

- **whole_design.** The supplied testbench (a frozen run input, never the
  harness-adapted child testbench) exists and instantiates the top. The
  optimizer edits one source unit (`modules/<top>_unit.v`): every generated
  child module in spec order, then the mechanical top, the same verified
  text. No frozen companion is compiled beside it. Only the top carries the
  contract (name, ports, parameters and defaults, reset, clocking, latency
  annotation rule, observable cycles at its ports). Child names, ports and
  boundaries are internal. A candidate must define the top once (static
  interface check and the unit gate); modules the trusted testbench
  instantiates directly must stay defined and live-reached from the top (the
  live-companion rule applied to the candidate's own modules), so those
  checks never test a module the top no longer uses. The trusted testbench
  and every other gate (static, RTL safety, latency, compile, simulation,
  routed timing, metrics, receipts, evaluator) verify every candidate. The
  per-child generated oracles and testbenches verified the baseline children
  only and are never cited for changed children. `<top>_best.v` holds the
  whole unit.
- **frozen_children.** No supplied testbench (a single-child build whose
  integration testbench the harness adapted from the generated child
  testbench), or a supplied testbench that does not instantiate the top. The
  children stay frozen companions and only the top wrapper is editable, as
  before; the recorded reason says which. A multi-module build without a
  supplied testbench is still build_blocked.

The mode applies to every build with at least one child, single-child builds
included: their mechanical wrapper is just as unable to change the objective.
Taxonomy `frozen_children_block_build_optimization` (explore-tier4-01).

## Role-output parsing
Roles answer in free text, and its format varies between models. The harness
extracts what it needs with tolerant parsers. Tolerance only decides which text
is extracted; it never makes a candidate pass. Extracted RTL still climbs the
full ladder, an extracted oracle must still qualify against the spec's
examples, and an unclear verdict is REJECT.

- **RTL** (`llm.client.extract_verilog`). Think tags are removed. Fences tagged
  verilog, systemverilog, sv or v (any case), or untagged, are read before
  fences with other tags. When several HDL fences each start a module and every
  module name is distinct, they are joined, so a multi-module answer is never
  returned in part. Repeated names keep the first block. Otherwise the first
  fence that starts a module wins, then the first fence holding
  module…endmodule, then a raw module…endmodule span. As a last resort the whole
  text is returned, and rung 1 rejects it if it holds no module. Generated RTL
  without a timescale directive receives `` `timescale 1ns/1ps``
  (`roles.generated_rtl`); the verified optimize baseline copy gets the same
  default mechanically, with no model call.
- **Golden models** (`roles.golden_source`). The first fence tagged python, py or
  python3 (any case); else the first fence that defines both `init` and `step`;
  else the raw response, which then fails validation and costs a repair.
- **Evaluator verdict** (`Evaluation.parse`). Every Recommendation heading or
  label line is collected, allowing emphasis, a colon and blank lines before the
  verdict word. A verdict is read only when each such line names exactly one of
  ACCEPT, REJECT or RESTART and all lines agree. A missing verdict, a copied
  `ACCEPT | REJECT` template or a contradiction reads as REJECT. The deterministic
  vetoes then apply. The result is REJECT unless `Passed: N of M` and
  `Failed: K` are both present with N > 0 and N + K = M. Any `- …: FAIL` or
  `INVESTIGATE` criterion line forces REJECT. ACCEPT with K > 0 is REJECT. A
  forced REJECT counts at least one failure.

Each rule exists because of a recorded failure: fence_tag_drops_generated_modules,
golden_fence_tag_keeps_prose, evaluator_verdict_format_rejects_verified_gain,
evaluator_verdict_conflict_or_blank_line and seed_without_timescale_costs_model_repair.

## Planner spec repair
In build mode, a spec file that loads as a DesignSpec is law. A lint error ends
the run as spec_lint_failed, and a load error is raised. A prose request is
turned into a spec by the planner. That planner-written spec gets its lint or
load errors back for at most `max_fix_attempts` repairs (default 3). Each repair
prompt carries the errors and the previous spec. The planner receives at most
8,000 characters of that feedback (the errors plus up to 6,000 characters of the
previous spec), so the previous spec is not cut short (backend_configuration_rough_edges). Each repair is a journaled
planner call charged to the budget. If errors remain, the run ends as
spec_lint_failed with the errors in the checkpoint. The spec prompt also states
the structural rules, such as a top_name that differs from every module name
(spec_lint_failure_skips_planner_repair).

## Per-run token accounting
Backends report usage as `input_tokens`, `cached_input_tokens` and
`output_tokens` when they can. After a successful call the client adds them to
the run's Budget, which saves them under `tokens` in budget.json. Tokens are
accounting only. They have no ceiling and do not affect best-of-N degradation
or replanning. Missing or malformed usage adds no tokens; the call is counted
instead in `calls_without_token_usage` in budget.json, and the run reports show
the totals as incomplete when that count is nonzero. Command endpoints never
report usage, so each of their calls is counted there; no estimate is invented
(command_endpoint_tokens_reported_as_zero). The model budget is `max_llm_calls`, which
counts every attempt, retries included. Tokens are charged outside the retry
handling, so a checkpoint lock after a successful response still propagates as a
resumable lock (token_save_lock_misattributed). A budget.json saved before token
accounting loads with zero tokens, and one saved before the unreported-call count
loads with a count of zero. `tools/role_report.py` shows the totals per
run.

## Register-to-register slack
Acceptance timing is unchanged. The routed WNS and WHS of the full design, with
zero input and output delay on every data port (chip_top flow; the
out_of_context flow leaves data ports unconstrained), decide timing_met, timing
feasibility, the ranking of timing-infeasible candidates, timing_progress, the
Timing Doctor and curriculum acceptance. With I/O buffers in the path, those
numbers mostly measure pad delay (io_dominated_timing_metric).

After routing, the same synthesis script also writes `timing_reg2reg.rpt`:
`report_timing` from all registers to all registers, one path. The command is
guarded. It runs only when the design has registers, inside `catch`, because
`report_timing` errors when there are none (Vivado 12-4739). The parser reads
that path's slack into `VivadoMetrics.reg2reg_wns_ns`. The value stays null when
the report is absent or has no slack line. The planner and evaluator prompts
show it, labelled as not a timing gate.

**maximize_freq comparison.** Only the maximize_freq objective comparison
between timing-feasible verified designs reads it: `improvement_kind` between a
candidate and the incumbent, and best-of-N selection among feasible candidates,
compare `reg2reg_wns_ns` when every compared design has a finite value, and
otherwise compare `wns_ns` for all of them, never a mix
(`objectives.objective_field`). The fixed optimize contract states this rule.
No gate or curriculum criterion reads it (maximize_freq_ranks_on_pad_delay).

**Resource objective tie-break.** Between two verified timing-feasible designs,
minimize_luts compares (`lut_used`, `ff_used`) and minimize_ffs compares
(`ff_used`, `lut_used`) lexicographically. An equal primary count with a
strictly lower secondary count is an objective improvement, recorded as kind
`objective`; a higher primary count never is. When either design lacks a
finite, nonnegative secondary value there is no tie-break and only the primary
counts (`objectives.tie_break_field`). `improvement_kind`, best-of-N selection
among feasible candidates (secondary before code length, used only when every
feasible candidate reports it), the fixed optimize contract and its saved
objective policy, and the planner and evaluator prompts all state this rule.
Promotion still needs evaluator ACCEPT, so the evaluator prompt says not to
reject such a candidate for an unchanged primary count. maximize_freq and
minimize_power have no tie-break; feasibility, recovery and progress are
unchanged. The saved objective policy is contract evidence, so checkpoints
saved before this rule do not resume (equal_lut_ff_saving_discarded;
crc16_stream_build in explore-tier4-01 and -02: 16 LUT, 34 to 18 or 19 FF,
timing met, rejected).

## Implementation flow
`RunConfig.implementation` chooses one of two harness templates in
`autortl/vivado.py`; models never choose or write it. A curriculum entry sets
it with `implementation:` in meta.yaml and `run.py optimize|build` with
`--implementation` (`chip_top` by default; a bench takes it from each entry,
never from a flag). It is saved in config.json (resume refuses a change; a
config saved before it existed loads as `chip_top`), part of the cohort
configuration, the metrics-cache context (with the template's hash), the Doctor's
no-op flow proof and the fixed contract evidence, whose contract text names the
mode (taxonomy chip_top_flow_for_soc_block).

- **chip_top** (default, `SYNTH_TCL`, unchanged). The top is the whole FPGA
  design: every port bit gets an I/O buffer on a package pin, data ports get
  zero input and output delay to `clk`, and WNS/WHS include pad delay
  (see register-to-register slack below).
- **out_of_context** (`OOC_SYNTH_TCL`), for a block that sits inside a larger
  design, such as tier5 axil_regs_build (an AXI4-Lite slave, 169 port bits
  against 106 user I/O). The XDC creates `clk` at the target period and sets
  `HD.CLK_SRC BUFGCTRL_X0Y0` on it, so the clock is modeled as driven by a
  global buffer. `synth_design -mode out_of_context` inserts no I/O buffers;
  `opt_design`, `place_design`, the optional Doctor `phys_opt_design` and
  `route_design` then run on that netlist in the same batch session, with the
  same reports, metrics parsing and SYNTH_COMPLETE marker. Data ports get no
  input or output delay: there are no pads, and without partition-pin
  locations Vivado cannot route or time them accurately (Route 35-198). They
  are unconstrained I/O, so the routed WNS and WHS, which still decide
  timing_met and curriculum acceptance, cover the internal clocked paths only
  (register to register, RAM and DSP registers included). Combinational logic
  between a port and its first or last register is not timed; behavior there
  is still checked by the testbench. Utilization excludes I/O buffers (Bonded
  IOB 0). `reg2reg_wns_ns` is the same register-to-register report. A design
  with no internal clocked path reports no numeric WNS and fails the metrics
  gate, as it would with missing reports. The clock and synthesis lines are
  the same as `hardware/basys3/fmax/fmax.py`'s ooc mode, which closed timing
  live on Vivado 2025.2; the complete harness script has not yet run live.

## Target capacity failures
A `[Place 30-415]` ERROR line means the top has more I/O ports than the
package has user I/O. The contract fixes the ports, so no RTL repair can help.
`triage.classify` returns FailureKind.TARGET (value `target`) for such a log,
after host failures and before any design ID; the `[Place 30-68]` not-placed
and `[Place 30-99]` lines that follow are its consequences, while a 30-68 line
alone stays a design failure. Every FailureKind branch treats it this way:

- The stage journal settles it like a design outcome (`triage.SETTLED_KINDS`):
  committed, replayed on resume, never retried as infrastructure.
- Baseline: `_fix_loop` only repairs DESIGN, so the generator never sees it
  and no fix attempt is charged; the run stops as `target_infeasible` with
  `failure_kind: target` and `target_capacity` (Vivado's port count, available
  user I/O, device and package, plus the configured part and implementation).
  A part the message does not state stays null, never guessed.
- Candidate synthesis: the same stop, keeping the verified incumbent as
  best_iteration; the Doctor runs only after a candidate's synthesis passed.
- Curriculum: the entry is a FAIL with reason `target_infeasible: ...`, which
  enters the history like any failed entry. It is not infrastructure: rerunning
  on a healthy host gives the same result, so withholding a verdict would block
  the tier forever and hide a misconfigured entry. It is not a model failure:
  the reason names the entry configuration. Counting it as a FAIL can only
  lower a pass rate, so it cannot help a tier qualify.

Severities are unchanged: nothing is demoted. Taxonomy
io_overutilization_sent_to_fixer (explore-tier5-01 and -02 axil_regs_build: a
testbench-passing top was "repaired" three times and broken).

## Curriculum governance
Tier held = 3 consecutive runs ≥80%. Regressions on held tiers block harness
changes. Stage gates: S1-2→tier0-1, S3-4→tier2, S5→tier3, S6-7→tier4-5.
Tier 4 targets RTLLM v2 / VerilogEval. External optimization percentages require
matched tasks, technology, tools, contracts and budgets before comparison; see
[research decisions](RESEARCH.md) for CRADLE and other related systems.

**Cohort.** A cohort binds each entry's source hashes and configuration (the
model included), the frozen runtime identity of every entry, the governance code
hash and the model identity described under provider architecture. `--jobs` is
not part of it.

**Parallel entries.** Entries run one at a time by default. `bench --jobs N`
runs up to N entries at once as separate processes. Each entry keeps its own run
folder, budget and journal. Records are still assembled in entry order. A worker
process that dies yields an exception record for its entry. Build mode's top name
is read from the run summary, because a worker's configuration change does not
reach the parent (parallel_build_winner_digest_lost). Parallel entries share one
host.

**History.** The history file `curriculum/results.jsonl` is read when a campaign
starts, and the campaign's record is appended when it ends. The append happens
only under an exclusive lock file (`results.jsonl.lock`), and only if the
history bytes read at the start are still an exact prefix of the file and every
record added since is for a different tier. Governance for a tier reads only
that tier's records, so benches of different tiers may run at once; earlier
bytes are never rewritten (cross_tier_benches_serialized). A held lock, a
rewritten history or a record of the same tier added meanwhile fails closed as
infrastructure. Nothing is written, the record stays in the campaign's
summary.json and the bench exits 3 (concurrent_bench_drops_history). The lock
records the owning process ID. A lock whose recorded owner is no longer running
(checked without signalling it; OpenProcess on Windows) was left by a crashed
bench and is replaced at once (dead_bench_lock_blocks_until_stale). A lock with
no readable owner is replaced only when older than ten minutes
(stale_history_lock_blocks_benches).

**Infrastructure-blocked campaigns.** A campaign with any entry whose summary
has `failure_kind: infra` gets no verdict. This covers infra_blocked and
model_blocked runs and an escaped checkpoint lock. Its record, with
`infra_blocked_entries`, goes only to summary.json. The history is untouched and
the bench exits 3. Resume or rerun it on a host that stays awake
(infra_blocked_entry_enters_history, host_standby_stalls_tools). An entry that
raised a Python exception is a failed entry, not infrastructure. Otherwise the
bench exits 0 when the campaign qualifies and 1 when it does not.

**Gate runner.** `tools/tier0_gate.py` runs the merge gate for tier 0 or 1. It
freezes the runtime source identities, requires a full pytest receipt with the
source unchanged, then runs the bench with fixed per-tier budgets. Afterwards it
requires the source, the router statistics prefix and the history prefix to be
unchanged. It refuses to run when a higher tier is held and never overwrites an
earlier attempt. `--model` and `--jobs` pass through to the bench.

## Conventions (enforced by autortl-conventions skill + code)
Spec is law (latency, interfaces). Promote never demote. One driver per
signal. Defaults first in combinational blocks. Clock is `clk`. All TCL from
harness templates only.

## Deferred by decision (not forgotten)
Pulse compare mode; LLM watchdog-diagnosis layer; router reordering (after
10 runs); Tier-3 skill regression evals; formal verification rung.

## Exit evidence and latency authority

Each tool invocation writes tool_exit_records.log with actual process exits,
distinct driver outcomes, process identity, duration and output-log hash.
Timeout124 and launch126/127 are driver codes, never successful process exits.
Context validates the full receipt history and exposes bounded records plus
latest outcomes. Cache and DONE retain evidence hashes; source-identical physical
Doctor trials explicitly cite prior simulation evidence rather than claim reruns.

Unannotated optimization inputs have unknown declared numeric latency. They do
not acquire a zero-cycle contract; every observable source cycle remains fixed.
Typed builds require known numeric latency for generated reference comparisons.
An annotation alone is never independent proof of behavior.

Curriculum cohorts bind tasks, configuration, frozen implementation/Python/tool
identity and governance code. Missing or mixed runtime provenance cannot qualify
a tier. A cohort records at most the requested model, never one observed from
the backend (see provider architecture). A tier result does not establish
a frozen-model experiment or weaker-model robustness.

## Proposal identity and planning

Candidate deduplication skips only exact UTF8 generation text using full SHA256.
Whitespace/comment normalization is advisory; it does not prove equivalent
Verilog and cannot justify discarding a candidate. Metrics reuse additionally
requires the existing exact source, flow, inputs and environment context.

Planner instructions are bound to the SHA256 of the actual generation seed
text and the returned plan. A changed accepted seed requires a fresh plan;
source-identical physical improvements retain existing planning policy. Planner
prompts distinguish the editable source from verified incumbent measurements,
including restarts that return generation to the original source.

Without room for a required replan, the loop keeps its verified incumbent and
stops without executing stale instructions. Raised execution-budget errors
retain the existing budget_exhausted status; provider quota failures remain
model_blocked. Neither is a design failure or a successful new proposal.

Bounded chronological proposal records remain retained and integrity checked.
Their additional prompt context is experimental and defaults off after the
three-pair study did not establish a repetition benefit. New runs may enable
--proposal-feedback or explicitly use --no-proposal-feedback; saved configuration
controls resume. No extra role, retry or budget is introduced.

## Environment check and offline demo

`run.py doctor` checks a machine before a run. It runs no design and sends
nothing to a model; it runs only local version and login-status commands.
Required checks: Python 3.12 or newer; pyyaml; vivado, xvlog, xelab and xsim
(the given paths, else PATH as the name, `.bat` or `.exe`); the Codex CLI
(AUTORTL_CODEX_BIN or PATH) answering `--version`; `codex login status`
reporting logged in; and a writable checkout. `xvlog --version` that does not
name the Vivado Simulator is a warning. Optional checks only warn: pytest, the
AUTORTL_OPENAI_* backend (whether the key is set, never its value) and each user
endpoint (a command on PATH, or its key variable set). When one of those other
backends is ready, the Codex checks become optional warnings
(backend_configuration_rough_edges). The exit code is 0 when
every required check passes and 1 otherwise.

`scripts/demo.py` is a simulated walkthrough of one optimize run. It runs the
real Orchestrator (state, journal, budget, checkpoints and acceptance gates) on
curriculum/tier0/mux4 for one iteration. The model roles and the Vivado tool
functions are fixed stand-ins, and process launch, socket connection and the
model client are blocked while it runs. It needs no Vivado, model login or
network. Every LUT count and slack it prints is made up, and it says so. It
shows what a run writes and where. It is not a measurement and not evidence.
