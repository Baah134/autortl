# AutoRTL v4 | Complete File-by-File Documentation

Every file in the repository, what it does, the design choices inside it, and why those choices were made. `docs/DESIGN.md` is the architecture spec; this document is the implementation record. Written for the engineer (you, or a Claude Code session) who needs to modify any file and wants the reasoning that produced it.

**Repository totals:** 146 files | 23 harness modules | 3 LLM backends | 8 skills | 6 curriculum tiers | 84 passing tests.

---

## 1. Repository Layout

```
autortl_v4/
|- run.py                      CLI entry: optimize | build | resume | bench
|- requirements.txt            pyyaml, pytest (stdlib for everything else)
|- README.md                   quick start
|- CLAUDE.md                   standing instructions for Claude Code sessions
|- docs/
|  |- DESIGN.md                architecture spec (single source of truth)
|  |- DOCUMENTATION.md         this file
|- autortl/                    the harness (23 modules)
|- llm/                        model routing + 2 backends
|- data/taxonomy.yaml          Vivado message-ID dictionary
|- .claude/skills/             8 SKILL.md guidebooks + verified snippets
|- curriculum/                 tiered benchmark designs + runner
|- tests/                      84 pytest checks + captured Vivado fixtures
```

**Why this shape:** the harness (`autortl/`) never imports from `llm/` backends directly | it goes through `llm/client.py` only. Knowledge (`skills/`, `taxonomy.yaml`) is data, not code. Tests mirror module names one-to-one. Anything an LLM writes lands in `.v`/`.py` files only | never in TCL, shell, or paths (defence #11).

---

## 2. Root Files

### run.py
The CLI. Four subcommands sharing one parent parser for the common flags (part, frequency, objective, iterations, N, tool paths, route override).

- **Design choice: subcommands over flags.** `optimize` and `build` are different entry states of the same FSM, not different programs. The CLI makes the mode explicit, then both converge on `Orchestrator(cfg).run()`.
- **Design choice: tool paths are flags** (`--vivado`, `--xvlog`, `--xelab`, `--xsim`) with bare-name defaults. Windows installs put Vivado at nonstandard paths (`C:\AMDDesignTools\2025.2`); hardcoding broke us repeatedly in v1-v3.
- **Design choice: `--route generator=openrouter.nemotron-super`** exists so routing experiments never require editing routing.yaml. Routing is data; the CLI is just a one-shot override.
- `bench` imports lazily so curriculum runs do not pay orchestrator import cost when only listing entries.

### requirements.txt
Two packages: `pyyaml`, `pytest`. Everything else is stdlib.

- **Why so lean:** the system must run on a locked-down Windows student laptop. Every dependency is a future install failure. HTTP is `urllib.request`; hashing is `hashlib`; no requests, no pydantic, no numpy in the harness itself (golden models may import what they like | they are user-space).

### CLAUDE.md
The standing session contract for Claude Code: hard rules (spec is law, promote-never-demote, infra never mutates design, every parser gets a fixture test), the working protocol (one stage per session, pytest + tier 0 before merging), the current-state line, and env vars.

- **Why it exists:** you lose access to this conversation. `CLAUDE.md` is how every future session inherits the decisions without the transcript. It deliberately duplicates the five most-violated rules from DESIGN.md because a session that reads only one file should still be safe.

### README.md
Quick start only. Points at DESIGN.md for architecture. Kept short so it stays true.

---

## 3. The Harness | `autortl/` (23 modules)

Ordered by pipeline position, not alphabet.

### 3.1 config.py | RunConfig
One dataclass holding every knob: mode, paths, target part/frequency, objective, iteration/N/replan/fix limits, tool binaries, and the three budget ceilings (LLM calls, Vivado minutes, wall minutes).

- **Design choice: a dataclass, not YAML config files.** The CLI is the config surface; a second config format would drift. Curriculum `meta.yaml` files construct RunConfigs | that is the one place config is data.
- **Design choice: `target_period_ns` is a property**, derived from frequency. One source of truth; v1 had both stored and they disagreed once.

### 3.2 spec.py | the typed schema (Pothole 1's foundation)
`Port`, `ResetSpec`, `IOExample`, `ModuleSpec`, `Connection`, `DesignSpec`. Every field the linter, testbench generator, and skill matcher rely on is typed and validated here. Enums as module-level sets: `PROTOCOLS = {none, valid_ready, pulse, level}`, `COMPARE_MODES = {fixed_latency, scoreboard}`.

- **Design choice: protocol is an enum field, not prose.** The linter cannot regex "this port sort of sounds like valid/ready". Making protocol/clock_domain/reset formal fields is what makes Potholes 1, 2, and 5 solvable with plain code.
- **Design choice: `pulse` exists in PROTOCOLS but not COMPARE_MODES.** The port protocol is describable today; the testbench compare mode for it is deliberately stubbed (raises NotImplementedError in tbgen). Honest stubs over silent wrong behavior.
- **Design choice: `contract_hash()`** = SHA-256 over name + behavior text + ports + latency + compare_mode + reset + params, truncated to 16 hex chars. **Behavior text is included on purpose**: same interface with changed behavior must regenerate (Pothole 4 fix). Truncation to 16 chars: collision odds are irrelevant at this scale and short keys keep artifact_cache.json readable.
- **Design choice: `IOExample` is mandatory in the planner prompt** (2-3 per module). These examples qualify the golden model before it becomes the oracle | the defence nobody's review caught: a wrong answer key grading everything.
- **Design choice: hand-rolled `from_json`** instead of pydantic: two dependency-free pages, and error messages we control.

### 3.3 linter.py | contract linting + stub elaboration + mechanical integration
Three jobs: `lint_spec` (pure-Python structural checks), `stub_verilog` (black-box shells), `top_verilog` (deterministic top-level wiring), `write_stub_project` (both, to disk, for the xvlog elaboration check).

- **lint_spec checks:** per-module validity, connection endpoint existence, direction correctness (src must be output, dst input), **width equality**, **protocol equality**, **clock-domain equality** (a crossing without a CDC module is rejected at spec time | this is the cdc skill's law enforced in code), and dangling inputs (driven by nothing, not external, not clk/rst).
- **Design choice: the top level is generated by code, never by the LLM.** Wiring is exact, boring work | precisely what models fumble and code cannot. This single decision removes the largest integration-failure class before it can exist.
- **Design choice: stub elaboration runs through xvlog** before any generation. If empty shells cannot elaborate, the wiring/contract is broken and zero LLM tokens have been spent on it (the "bad blueprint death spiral" fix).
- Wire naming convention `w_<module>_<port>`: collision-free by construction, greppable in Vivado reports.

### 3.4 static_checks.py | ladder rung 1 (milliseconds)
`check(verilog, contract)` returns pass/fail + error list. Checks: a `module` declaration exists at all (the v3 "extracted testbench fragment" bug, now fatal at rung 1), `endmodule` present, no `initial` blocks, begin/end imbalance heuristic, contract interface conformance (module name, every port name present), and the latch heuristic.

- **Design choice: the latch check is a heuristic, flagged as such** (`if` without `else` in an `always @(*)`). xvlog and the promoted [Synth 8-327] are the authorities; rung 1 exists to kill the obvious cases for free.
- **Design choice: comment stripping before all checks** | v3 once flagged a keyword inside a comment.
- Every check here is a failure class we actually hit in v1-v3. Nothing speculative.

### 3.5 triage.py | infra vs design (defence #9)
`classify(text) -> INFRA | DESIGN | UNKNOWN` by ordered signature lists. Infra: license, file locks on `.wdb/.pb` (xsim holds handles), permission denied, connection failures, disk full, tool-not-found, timeouts, HTTP 429/5xx. Design: any `[Facility N-M]` message ID, syntax error, port mismatch, TEST FAILED.

- **Design choice: infra checked first.** A log can contain both (a lock message plus stale error text); blaming the design for a locked file "fixes" correct code and poisons the history the planner learns from. When in doubt the FSM retries once and only then treats UNKNOWN as design.
- **Design choice: HTTP codes live here too** so OpenRouter free-tier 429s flow through the same triage as Vivado locks. One classifier, every failure source.

### 3.6 metrics_gate.py | integrity gates (defence #10)
`validate(metrics, synthesis_ran)` raises `MetricsGateError` on: totals <= 0, used > total, WNS outside (-1000, 1000).

- **Why it exists:** v3 shipped `lut_total: 0` producing a nonsense 4800% utilization that flowed silently into scoring. **A parse failure must be an infra event, never a score.** The gate makes that class of bug loud. The exact v3 bug is a regression test (`test_metrics_gate.py::test_zero_total_rejected`).
- **Design choice: exception, not boolean.** Callers must handle it explicitly; a forgotten `if` would recreate the silent-poison path.
- **Design choice: `synthesis_ran` flag** | sim-only results carry no resource claims and must not be gated on them.

### 3.7 cache.py | dedupe + artifact reuse
`code_hash` (comments stripped, whitespace collapsed, **spaces around operators removed**), `MetricsCache` (code hash -> metrics; identical Verilog never synthesised twice), `ArtifactCache` (contract hash -> verified module; survives replans | Pothole 4).

- **Design choice: normalize around operators.** `y = x` and `y=x` must dedupe. This exact gap was caught by the test suite during the build and fixed | the operator-space rule exists because a test failed.
- **Design choice: two caches, two key types.** Code hash answers "have I synthesised this text"; contract hash answers "is this module's *interface+behavior* unchanged across a replan". Conflating them would either miss reuse or reuse stale modules.
- JSON files, human-readable, tolerant of corruption (falls back to empty on decode error) | a corrupt cache must never kill a run.

### 3.8 budget.py | graceful degradation
Tracks LLM calls, Vivado seconds, wall minutes against ceilings. `fraction_left()` = worst of the three. `effective_best_of_n`: full N above 50% remaining, 2 above 20%, 1 below. `allow_replan()` above 30%. State persists to `budget.json` so resume continues the same budget.

- **Design choice: degrade, never die.** A run that stops mid-flight wastes everything spent; a run that shrinks to best-of-1 and skips replans still delivers its best-so-far with a clean summary.
- **Design choice: the worst fraction governs.** Whichever resource is scarcest is the binding constraint | the Pro-plan 5-hour window maps onto `max_llm_calls`/`max_wall_minutes` without special-casing Claude.
- Thresholds (50/20/30) are named constants in behavior, tested in `test_budget.py`, tunable without touching the FSM.

### 3.9 watchdog.py | deterministic pathology detection (the "MCE" answer)
`inspect(history, recent_codes, recent_errors, budget_fraction)` -> typed `Signal`s: **STAGNATION** (3 iterations, no best), **CHURN** (last two candidates hash-identical), **REPEATED_ERROR** (same signature 3x), **BUDGET_ANOMALY** (>50% spent, nothing gained).

- **Design choice: no LLM.** 80% of what an observer agent would catch is mechanically detectable from the state files (this is why Karpathy's write-to-disk rule pays). Signals are handed to the planner as evidence; the LLM diagnosis layer is deferred until the mechanical layer proves insufficient.
- **Design choice: signals are data, not actions.** The watchdog reports; the FSM decides. Keeps the pathology detector testable in isolation (5 tests, synthetic histories).

### 3.10 report_parser.py | Vivado reports -> VivadoMetrics
`VivadoMetrics` dataclass (sim, WNS/WHS, LUT/FF/DSP/BRAM used+total, power, error strings) with `to_dict`/`from_dict`. Parsers for sim logs, utilization tables, timing summaries, power. `extract_message_ids` pulls every `[Facility N-M]` ID.

- **Design choice: parse both table dialects.** Vivado renders utilization with 5 or 6 columns depending on version/flags ("Prohibited" column). The regex accepts both | version drift bit us in v1.
- **Design choice: `lut_pct`/`ff_pct` are properties**, excluded from `from_dict` input. v3 stored them and round-tripping crashed; computed-only cannot desync.
- **Design choice: sim verdicts are machine-parsed** from mandated marker lines (`TEST PASSED` / `FAIL index=...`). The tbgen emits exactly these markers; parser and generator are two halves of one contract.
- **Tested against captured real report files** in `tests/fixtures/` | parser tests against synthetic strings prove nothing.

### 3.11 vivado.py | the toolchain driver
`xvlog_check` (rung 2), `xsim_run` (rungs 3-4: xvlog -> xelab -> xsim, batch, **no project mode**), `run_synthesis` (rung 5: templated non-project TCL with auto-generated XDC, optional `-retiming`/`phys_opt_design` for the Timing Doctor's knob rung), `promotion_tcl` (severity promotion from the taxonomy), `_tcl_path` (path sanitiser).

- **Design choice: batch xvlog/xelab/xsim replaces `create_project`.** Project mode costs 30-60 s per run **and caches compiled sources** | stale caches caused false failures across multiple v1-v3 debugging sessions. Batch is faster and stateless. This is the largest single speed win in v4.
- **Design choice: TCL is template-only; `_tcl_path` rejects quotes, braces, `$`, `;`** and converts to forward-slash absolute paths (the Windows backslash bug from v1, plus injection defence #11). No LLM string ever reaches TCL.
- **Design choice: the XDC is written by the TCL itself** so the clock constraint always exists | [Timing 38-282] "no clock" failures are structurally impossible.
- **Design choice: promotion only.** `promotion_tcl` skips any entry whose override is not ERROR. The demote path does not exist in code, so a future "make the run look clean" temptation has nothing to call.
- **Design choice: `SYNTH_COMPLETE` sentinel** printed at script end; return code alone is unreliable across Vivado versions.
- Every runner records wall seconds (`vivado_seconds()`) for the budget, and `message_ids_in()` aggregates IDs across all four logs for the evaluator.

### 3.12 golden.py | the Python oracle
`GoldenModel` wraps a user/LLM `.py` file exposing `init()` and `step(state, inputs) -> (state, outputs)`; `qualify_against_examples` replays the spec's IOExamples through it.

- **Design choice: one clock cycle per `step`.** The simplest contract that still models sequential behavior; anything fancier and weak models cannot write golden models reliably.
- **Design choice: qualification before use.** The oracle is checked against the blueprint's concrete examples before it grades anything | the one failure mode differential testing cannot survive is a wrong oracle. One regeneration attempt on failure, then hard stop for that module.
- Import via `importlib` from an explicit path: golden models are per-run artifacts, never installed packages.

### 3.13 tbgen.py | testbench autogeneration (Pothole 2 resolved)
`gen_stimulus` (3 corner vectors + N seeded-random vectors), then one of two emitters chosen by the contract's `compare_mode`:

- **`generate_fixed_latency_tb`** | expected outputs delayed by `latency` cycles before compare (the "15-line core" as an index offset: check `chk_idx` only once `drv_idx > latency`).
- **`generate_scoreboard_tb`** | queue-based for valid/ready: expected value pushed per accepted input beat, popped and compared per output beat; **periodic `ready` deassertion (every 7th cycle) exercises backpressure**.

Both emit: reset per the contract (kind, polarity, duration) + **2-cycle settle margin before the compare window opens** (defence #8), `!==` four-state compares, and the exact marker lines the parser expects. Stimulus + expectations are also written to `stimulus.json` for post-mortem.

- **Design choice: two modes, pulse stubbed with a loud NotImplementedError.** Fixed-latency covers FIR/MAC/counters; scoreboard covers streaming. Pulse mode was the genuinely speculative third and was cut on your overengineering challenge | the stub documents the decision in code.
- **Design choice: seed 1234 default, 99991 for requalification.** Deterministic stimulus makes failures reproducible; the second seed exists so a testbench that failed qualification is rebuilt with different vectors, not identical ones.
- **Design choice: corners first** (all-zeros, all-ones, MSB-only) | they catch sign and wrap bugs that uniform random rarely hits early.

### 3.14 tbqual.py | oracle qualification by bug injection (defence #7)
`mutate` applies the first matching operator from a fixed list (flip `<`->`>`, `==`->`!=`, `+1`->`+2`, `&&`->`||`) to a known-good module; `qualify` runs the testbench against the sabotage and **requires a FAIL**.

- **Why:** the entire correctness story rests on generated testbenches catching bugs; nothing else verifies they can. This is mutation testing aimed at the oracle. Cost: one extra unit-sim per module. Payoff: "we hope the tb works" becomes "we proved the tb catches bugs".
- **Design choice: lookaround regexes, not `\b`.** `\b<\b` never matches (no word boundary beside punctuation) | the test suite caught this during the build; the current patterns exist because a test failed.
- **Design choice: mutations are guaranteed behavior-changing** operators only. A mutation that might be semantics-preserving would produce false "tb is broken" verdicts.

### 3.15 taxonomy.py + data/taxonomy.yaml | the error dictionary (Upgrades A/B)
YAML keyed on **official Vivado message IDs**: `meaning`, `repair` (an instruction written for the generator), `severity_override`. `Taxonomy.promotions()` feeds vivado.py; `repair_instruction()` implements the fallback ladder: known ID -> our repair | unknown ID -> query Vivado's own `help -message` (offline, deterministic) -> log to `unknown_message_ids.log` for post-run curation.

- **Design choice: message IDs as keys, not invented regexes.** AMD maintains the ID namespace across versions; our v3 regex signatures were brittle. The taxonomy now grows against a stable namespace.
- **Design choice: curation-by-experience.** 10 entries seeded | every one an error class actually hit in v1-v3 ([Synth 8-327] latch and [Synth 8-3352] multi-driven promoted to ERROR; [Vivado 12-4473] documented as a wrapper whose real cause lives in the referenced logs). Bulk-ingesting AMD's thousands of IDs was explicitly rejected: noise destroys trust in the dictionary.
- **Design choice: the YAML is the machine view; the `vivado-messages` skill is the model-facing view of the same content.** One knowledge source, two renderings, harvest pipeline feeds both.

### 3.16 bestofn.py | forced diversity + deterministic selection (Pothole 3)
`MUTATIONS` (six architectural directives: standard, pipeline, share, narrow, infer, wildcard), `PORTFOLIO` (per-objective ordered pick of 4: e.g. minimize_luts -> standard, narrow, share, wildcard), `dedupe` (code-hash), `select` (sort by rungs passed desc, then objective metric, then code length).

- **Design choice: objective-weighted portfolios + exactly one wildcard.** Under a single-provider setup, mutation prompts are the *only* decorrelation mechanism | spending a slot on "maximize throughput" when minimizing LUTs is a wasted candidate, but zero wildcards forfeits diversity insurance. N=4 was your decision; the portfolio tables encode mine.
- **Design choice: selection is a sort, not a judgment.** No LLM picks the winner. Rungs-passed dominates (a correct slow design beats a fast broken one), objective metric breaks ties, brevity last (shorter correct code is easier to keep improving).
- **Design choice: the pipeline mutation instructs a `// @latency` update** | and the FSM then *rejects* any candidate whose declared latency differs from the contract. Spec is law; the mutation text teaches the discipline, the check enforces it.

### 3.17 timing_doctor.py | timing triage (Pothole 6)
`parse_worst_path` (WNS, logic levels, max fanout, path snippet), `diagnose` -> category (**LOGIC_DEPTH** >=8 levels -> pipeline instruction | **HIGH_FANOUT** >=64 -> replication instruction | **CDC** -> synchroniser instruction | UNKNOWN -> split-the-path instruction) and action by slack magnitude: **> -0.5 ns and knobs untried -> `tool_knobs`** (retiming + phys_opt, zero code risk) | otherwise **`rtl_surgery`**.

- **Design choice: knobs before surgery.** Vivado's own options rescue small deficits with zero correctness risk and zero LLM calls. The `already_tried_knobs` flag prevents knob-loops.
- **Design choice: the diagnosis is deterministic; only the surgery is an LLM call.** A weak model cannot read a 10,000-line timing report, but it can execute "insert one pipeline register mid-path and update the latency header" | the harness converts the report into that sentence.
- Thresholds (-0.5 / -3.0 ns) are named constants; the -3.0 replan boundary is documented but surgery is still attempted once first (a surgery that works is cheaper than a replan).

### 3.18 skill_loader.py | the RAG pipeline collapsed to one function
Frontmatter parser, `conventions()` (the law | always injected into the **system** prompt), `select_for_module` (**protocol-first**: >1 clock domain -> cdc; behavior keywords like multiply/ram -> xilinx-inference; verilog-idioms always), `select_for_timing` (timing-closure + vivado-messages), `inject` (concatenate bodies under a 12,000-char cap).

- **Design choice: conventions are not a skill lookup.** Optional loading is fine for expertise; it is unacceptable for law. `autortl-conventions` rides the system prompt of every role, every call.
- **Design choice: harness-side loading exists at all** because generator/evaluator run `--max-turns 1` (no native skill discovery) and the NIM/OpenRouter fallbacks have no skills mechanism. One knowledge format, two loading paths: Claude Code native when agentic, harness-injected everywhere else.
- **Design choice: protocol-first matching** (Pothole 5): the presence of two clock domains in the *typed spec* selects the cdc skill | never the word "FIFO" in a name. The interface dictates hardware reality; names are semantics.
- The char cap prevents skill bloat from crowding the actual task out of context.

### 3.19 prompts.py | four system prompts + nine task templates
PLANNER/GENERATOR/EVALUATOR/DOCTOR system prompts, plus SPEC_PROMPT, CONTRACT_PROPOSAL/REVIEW/REFINE, PLAN, RESTART_PLAN, GENERATE, FIX, EVALUATE, GOLDEN_MODEL.

- **Design choice: every template mandates an exact output structure** (headed markdown sections, single fenced block) because the harness *parses* these outputs (`extract_instruction`, `Evaluation.parse`, `extract_verilog`). Prompt format and parser are one contract; change one, change both.
- **Design choice: the EVALUATE prompt states "ladder results are authoritative".** 80% of evaluation became deterministic in v4; the LLM evaluator rules only on the subjective residue (has this line plateaued). Telling it so prevents it re-litigating what the ladder already proved.
- **Design choice: FIX shows diagnosed message-ID repairs first, raw log excerpt second, previous failed attempts last** with an explicit "do not repeat" | the ordering matches how a weak model actually reads.
- **Design choice: testbenches appear in ```text fences** inside prompts | the v3 extraction bug (grabbing testbench fragments from ```verilog fences) is prevented at the source *and* at the extractor.

### 3.20 state.py | the files-on-disk protocol (Karpathy rules IV/V)
`RunState` owns: `contract.md` (written once), `plan.md` (planner-rewritten; `extract_instruction` pulls the generator's section), `progress.md` (append-only diary), `designs.jsonl` (one JSON line per iteration), per-iteration `evaluation.md`, and `state.json` (`save_fsm`/`load_fsm` for crash-resume).

- **Design choice: roles communicate only through these files.** The isolation that keeps the evaluator honest is enforced by what each role's prompt-builder is *given*, and what it is given comes from here.
- **Design choice: progress is append-only, read as a tail.** Full history stays on disk; the planner sees the last ~60 lines | context cost stays flat as runs grow.
- **Design choice: jsonl for designs** | appendable without rewriting, one corrupt line loses one record, and the watchdog/curriculum tooling stream it trivially.

### 3.21 roles.py | Planner, Generator, Evaluator, TimingDoctor
Thin classes: each method builds a prompt from its allowed inputs and calls `llm.client.ask(role, ...)`. `Evaluation.parse` regexes the recommendation (ACCEPT|REJECT|RESTART, default **REJECT** when unparseable) and pass/fail counts.

- **Design choice: the isolation lives here structurally.** The Generator's methods do not *accept* metrics or history as parameters | wrong context cannot be passed by accident.
- **Design choice: unparseable evaluation defaults to REJECT.** Fail-closed: a garbled report never accidentally accepts a design.
- **Design choice: the Doctor is the only role with `max_turns=3`.** Reading a timing path benefits from bounded agency; generation and grading are deliberately de-agented so the harness stays the only loop.

### 3.22 fsm.py | the Orchestrator (the heart)
Explicit resumable state machine. **Build mode:** spec (planner) -> lint -> stub elaboration -> per-module build (golden model -> qualify -> tbgen -> generate through the ladder -> tbqual; artifact-cache hits imported wholesale) -> mechanical top -> compiles -> flows into optimize as its baseline. **Optimize mode:** baseline (fix loop if broken | your v3 decision that the agent should repair, not refuse, is preserved) -> contract negotiation (propose/review/refine, <=3 rounds) -> main loop: watchdog -> conditional replan -> best-of-N through the ladder (static -> latency law -> xvlog -> sim with one taxonomy-guided fix -> synthesis with metrics gate + cache) -> deterministic select -> Timing Doctor (knobs -> surgery, surgery re-faces the ladder) -> LLM evaluation -> best/stall bookkeeping -> restart mechanism (<=2 replans, budget-gated) -> summary + `<top>_best.v`.

- **Design choice: `_snapshot` after every transition.** Kill the process anywhere, `resume` continues from `state.json` | tested manually as a stage gate.
- **Design choice: infra failures skip, never kill.** An infra-classified rung failure leaves the candidate alive without rung credit; design failures kill it and feed `recent_errors` (watchdog food).
- **Design choice: the latency law is an FSM check**, not a prompt hope: `declared_latency != contract.latency` -> candidate dead with the reason spelled out.
- **Design choice: surgery output re-enters the ladder.** Nothing the Doctor writes is trusted; it is a candidate like any other.
- **Design choice: restart preserves the best.** The working design resets to baseline; `best_v/best_m` survive | restarts are free options, never gambles.
- **Design choice: `_infer_contract`** regexes an interface-only ModuleSpec from an existing design so optimize mode gets static interface checks without demanding a spec file from the user.

### 3.23 __init__.py
Version string. Nothing else | import side effects in `__init__` files caused a circular-import scare in v3.

---

## 4. The LLM Layer | `llm/`

### 4.1 routing.yaml | routing is data
Per-role chains: planner/doctor `claude opus -> sonnet -> openrouter ultra -> nvidia ultra`; generator `sonnet -> nvidia super -> openrouter super`; evaluator `sonnet -> openrouter super`. Defaults: 2 retries per backend, 180 s timeout.

- **Why YAML:** re-routing is an experiment you run weekly; it must never require a code change. The CLI `--route` prepends a one-shot override.
- **Why planner/doctor get the big model and generator/evaluator do not:** planning and timing surgery are the judgment-heavy roles; generation and grading are deliberately constrained roles where Opus is wasted window budget. If Opus is unavailable on Pro, the chain silently continues at sonnet | **the harness must not care** (the thesis, enforced by fallback).

### 4.2 client.py | one public function
`ask(role, prompt, system, budget, route_override, max_turns)`: walk the chain, retry with exponential backoff on retryable signatures, charge the budget on success, **record every attempt** (role, entry, ok, seconds) to `router_stats.jsonl`, raise only when the whole chain fails. Plus `extract_verilog` (module-validating, think-tag-stripping, multi-fence-aware | the hardened v3 extractor) and `declared_latency` (`// @latency N` parser).

- **Design choice: recording-only stats (your decision #2).** The data accumulates from run one; reordering by observed success is enabled only after ~10 runs exist. Acting on 3 samples is noise.
- **Design choice: retryable vs non-retryable split.** A 429 retries with backoff on the same backend; an auth error moves to the next chain entry immediately | retrying a bad key 3 times wastes 15 s per call.
- **Design choice: extractor prefers the block that *starts* with `module`**, then any block containing module...endmodule, then a raw-text module scan, and warns loudly as last resort. Every tier of that ladder corresponds to a real v3 failure.

### 4.3 backends/codex_cli.py
`codex exec --sandbox read-only --ephemeral --json` with the prompt on stdin, using the existing Codex login. Returns the final message plus model, usage and session metadata; failures raise typed `CodexError` codes (`CODEX_AUTH`, `CODEX_QUOTA`, `CODEX_NETWORK`, `CODEX_TIMEOUT`, `CODEX_PROTOCOL`, `CODEX_UNAVAILABLE`) that the client keys its retries on.

### 4.4 backends/openai_http.py
Standard-library client for any OpenAI-compatible `POST <base>/chat/completions` endpoint, routed as `openai.<model>` (or `--model openai.<model>`). Configuration is environment-only: `AUTORTL_OPENAI_API_KEY` (required), `AUTORTL_OPENAI_BASE_URL` (default `https://api.openai.com/v1`; local Ollama or vLLM servers work), `AUTORTL_OPENAI_MODEL` (used for `openai.default`). HTTP failures map onto the same `CodexError` codes (401/403 auth, 429 quota, 5xx and connection network, timeout, malformed body protocol). The key, prompt and system text are redacted from every error, redirects are refused so the key never reaches another host, and token usage is reported in the same `input_tokens` / `cached_input_tokens` / `output_tokens` shape.

The earlier `claude_code`, `nvidia_nim` and `openrouter` adapters were removed; OpenAI-compatible providers are reached through `AUTORTL_OPENAI_BASE_URL`.

---

## 5. Knowledge | `.claude/skills/` (8 skills)

Format: Anthropic SKILL.md (YAML frontmatter description + markdown body + `snippets/`). **The frontmatter description is an engineering surface** | it is both Claude Code's native loading trigger and the text the harness matcher reads. Vague description = skill never loads.

| Skill | Content | Why it exists |
|---|---|---|
| autortl-conventions | Output format, interface law, `// @latency` law, coding rules, promote-never-demote, file boundaries | **Law, not expertise.** Injected into every system prompt; the one skill whose loading is unconditional |
| verilog-idioms | Two-process FSM, latch avoidance (defaults first), reset discipline, valid/ready rules, width discipline + 3 verified snippets | The generation-quality floor for weak models; always selected for generation |
| vivado-driving | Forward-slash absolute paths, the batch fast path, stale-cache trap, promotion TCL, infra signatures | v1-v3's debugging pain, written down once so no session re-learns it |
| vivado-messages | The model-facing view of taxonomy.yaml: high-frequency IDs + repairs + the promoted set | Loaded by fix paths and the Doctor; grows via the same harvest as the YAML |
| xilinx-inference | DSP48 (register in/out, plain `*`), BRAM (`ram_style` + registered read), SRL (no reset on delay lines), carry chains + MAC snippet | Selected by behavior keywords; the difference between 1 DSP and 200 LUTs is a coding pattern |
| timing-closure | Read-the-path-first, the knobs->surgery->replan order, pipelining rules, fanout replication, the never-do list | The Doctor's textbook; mirrors timing_doctor.py's thresholds so model and harness agree |
| cdc | Two-flop sync, toggle sync, gray-coded async FIFO, constraints discipline + 2 snippets incl. full async FIFO skeleton | Selected when clock_domains > 1. "Simulation lies about metastability" | structure is the only safety |
| testbench-craft | Marker-line discipline, the reset/X window, both compare modes, stimulus corners, oracle qualification rationale | Documents the tbgen contract for any model asked to reason about tests |

- **Design choice: snippets are verified code**, not sketches | the async FIFO skeleton and MAC pattern are complete, synthesisable, and the only teaching examples the model ever sees. Teach only from verified examples.
- **Evolution path (staged in DESIGN.md):** Tier 1 hand-written (done) -> Tier 2 post-run harvesting with human approval -> Tier 3 versioned skills with regression evals. Deliberately deferred until runs exist to justify them.

---

## 6. Curriculum | `curriculum/`

### runner.py
`run_tier(N)`: iterate entry folders, build a RunConfig from each `meta.yaml`, run the orchestrator, check `pass_criteria` (max_luts, timing_met) against `best_metrics`, append to `results.jsonl`, return shell-friendly 0/1 at the 80% threshold.

- **Design choice: meta.yaml per entry** | curriculum entries are data; adding one is a folder, never a code change.
- **Design choice: exceptions become entry failures**, not runner crashes | one broken entry cannot hide the results of the rest.

### Entries shipped
- **tier0/counter** | the v1-v3 counter, verbatim, with its testbench. `pass_criteria: max_luts 67` (v3's iteration-1 cleanup) | **the past is the regression bar**. The known v3 best (48 LUTs, WNS 4.092) is recorded in the meta as the stretch target.
- **tier0/mux4** | trivially-correct registered mux. Pure plumbing smoke: if this fails, the toolchain is broken, not the design.
- **tier1/pwm** | deliberately wasteful (32-bit counter for an 8-bit job); the testbench measures duty statistically over a full period (62-66 highs for duty=64) so registered-output implementations are not falsely failed | a lesson from the v3 counter-testbench latency fights.
- **tier1/debouncer_build** | first build-mode exam: prose spec -> planner -> golden model -> tbgen -> tbqual, one module, no integration complexity.
- **tier2/fir8** | naive 8-tap FIR (single-cycle sum of 8 products) at **150 MHz** | on purpose: the impulse-response testbench pins correctness while the aggressive clock forces the DSP-inference and pipeline mutations and gives the Timing Doctor real work.
- **tier3/uart_fifo_build** | two modules + mechanical top from a prose spec; the FIFO uses scoreboard mode, the UART fixed-latency | exercises decomposition, both compare modes, and integration in one entry.
- **tier4/README, tier5/README** | populated-at-runtime by design: RTLLM v2 / VerilogEval problems (with **CRADLE's 48% LUT / 40% FF as the published number to beat**) and the heavy set (AES round, async FIFO as the cdc exam, RISC-V slice). Benchmarks are downloaded, not vendored | licensing and freshness.

**Governance (in DESIGN.md, enforced by habit + CLAUDE.md):** tier held = 3 consecutive runs >= 80%; regressions on held tiers block harness changes; every wild failure becomes a taxonomy or curriculum entry before its hotfix lands.

---

## 7. Tests | `tests/` (84 checks, all passing)

One test file per harness module, plus `conftest.py` (path bootstrap) and `fixtures/` (captured real Vivado report text).

| File | Covers | Notable cases |
|---|---|---|
| test_spec.py | schema validation, contract hash | **behavior text changes the hash** (Pothole 4's exact requirement); pulse mode rejected; JSON round-trip |
| test_linter.py | all five connection checks + dangling inputs + stub/top generation | width, protocol, and CDC mismatches each individually caught |
| test_static.py | rung 1 | the v3 "testbench fragment" input fails; latch heuristic fires; missing contract port caught |
| test_triage.py | classifier | locks/licenses/timeouts/429 -> INFRA; message IDs / TEST FAILED -> DESIGN; unknown stays UNKNOWN |
| test_metrics_gate.py | integrity gates | **the literal v3 lut_total:0 bug as a must-raise regression** |
| test_cache.py | hashing + both caches | comment/whitespace/operator-space insensitivity; logic sensitivity; disk round-trips |
| test_budget.py | degradation curve, replan gate, disk resume | 4->2->1 at the documented thresholds |
| test_watchdog.py | all four signals + healthy silence | synthetic histories |
| test_bestofn.py | portfolios, dedupe, selection | objective->portfolio mapping; cosmetic-duplicate kill; rungs-dominate ordering |
| test_taxonomy.py | dictionary + promotions + unknown logging | promotions are ERROR-only |
| test_report_parser.py | every parser **against captured fixtures** | real utilization + timing report text; message-ID dedup order |
| test_tbgen.py | stimulus determinism + both emitters + pulse stub | corners first; scoreboard emits backpressure; golden-computed expectations present |
| test_golden.py | oracle wrapper + example qualification | a subtly-wrong golden model is caught by the examples |
| test_tbqual.py | mutation operators | operator regexes actually match |
| test_timing_doctor.py | thresholds + categories | knobs vs surgery boundary; knobs-tried escalation; level/fanout categorisation |
| test_skill_loader.py | conventions, protocol-first selection, injection cap | two clock domains -> cdc |
| test_llm_client.py | extractor + latency parser | prefers module block over text fence; strips think tags; raw-module fallback |
| test_state.py | instruction extraction, jsonl, fsm resume, progress tail | |

- **Design choice: tests target the harness, never the designs.** Design correctness is the ladder's job at runtime; these 84 checks are what let you refactor the harness without fear.
- **Proof they work: the suite caught two real bugs during this very build** (operator-space dedupe gap; `\b`-beside-punctuation mutation regexes). Both fixes exist because a test failed first.
- **Design choice: fixtures are captured real output**, not synthetic | the parser dialect bug class only shows against real text.

---

## 8. Cross-Cutting Decisions (the ones that shape everything)

1. **Harness over model.** Every LLM call shrunk until a weak model can't fail it; verification, selection, wiring, triage, and diagnosis are code. Enforced by: the ladder, deterministic selection, mechanical integration, `--max-turns 1`.
2. **Spec is law.** Latency and interfaces are contract facts; violations are failures, not negotiations. Enforced by: the latency FSM check, static interface conformance, the conventions skill, contract amendment governance (bounded, logged, deferred to real need).
3. **Fail cheap, fail loud.** Ladder ordering by cost; severity promotion; metrics gates raising instead of scoring; fail-closed evaluation parsing.
4. **Never blame the design for the environment.** Triage before any reaction; infra retries; UNKNOWN retried once. The planner's history stays clean.
5. **Everything on disk, resumable, append-only where possible.** Four state files + state.json + budget.json; roles isolated by what they're handed from disk.
6. **Knowledge grows from experience, with a human gate.** Taxonomy from real IDs, curriculum from real failures, skills harvested (later) from real runs | never bulk-ingested.
7. **Deliberate stubs over silent gaps.** Pulse mode, LLM watchdog layer, router reordering, Tier-3 skill evals: each cut is visible in code or documented in DESIGN.md's deferred list with its re-entry condition.

---

## 9. Known Limitations (honest list)

- `xsim_run` assumes the tb top is `<module>_tb` | curriculum convention; a `--tb-top` flag is a 5-line addition if ever needed.
- The optimize-mode `_infer_contract` regex reads ANSI-style port lists; K&R-style headers would need extension.
- `parallel_candidates` is plumbed in config but the FSM runs candidates sequentially | flip after verifying your Claude tier tolerates parallel headless sessions.
- The begin/end heuristic in static_checks is intentionally noisy-tolerant; xvlog is the authority one rung later.
- Build-mode `_build_module` runs best-of-1 for module bodies (best-of-N is exercised in the optimize loop); raising it is a config change once tier-3 timings are known.
