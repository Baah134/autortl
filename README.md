# AutoRTL v4

Start a new coordinator at [START_HERE.md](START_HERE.md). Codex, Claude,
Gemini and other user-authorized agents share the same handoff and task
ownership protocol. The canonical local clone is Downloads/autortl-work.
The completed CLI harness checkpoint is integrated into `main`. New work uses
short development branches and is integrated after review and recorded validation.

**Verified status:** 423 automated tests pass. Supervised counter and mux Vivado
checks passed. A successful autonomous optimization campaign is still pending;
the first bounded cohort and its repairs are retained in
[the evidence archive](evidence/2026-10-19/live-tier0/README.md).

**An agentic system that designs and optimises FPGA hardware code by itself.**

AutoRTL writes and improves Verilog for Xilinx FPGAs through Vivado — using a team of AI roles, a multi-rung verification ladder, and a growing library of hardware expertise. It was built around one thesis: **the system should be smart, not the model inside it.** A weak model inside a strong harness beats a strong model working alone. If AutoRTL only works well with the best AI, the design has failed.

The original project reported a 28% LUT reduction on a counter. That historical
result has not been reproduced during the current review. Current verified
results and limitations are recorded in [the progress log](docs/PROGRESS.md),
with source and tool evidence retained for new experiments.

---

## What it does

**Two modes, one machine.**

`optimize` — you give it a working (or nearly working) design, it makes it smaller, faster, or lower power, returning the best version it found with a full audit trail of every attempt.

`build` — you give it a plain-English description of what you want ("build a UART transmitter with a 16-entry FIFO buffer"). It plans the modules, writes each one, wires them together mechanically, then optimises the result.

Both modes retain the best verified Verilog, contract, plan, iteration history
and tool reports. Completed stages are journaled for recovery; an interrupted
in-flight stage may run again within the remaining budget. See
[recovery and validation](docs/RECOVERY.md) for tested behavior and current live-run coverage.

---

## How it works

### Four roles that never talk directly

The AI work is split between four isolated roles. Each sees only what it needs. When one model does everything, it starts grading its own homework. Isolation keeps the roles honest.

| Role | Job | Sees |
|---|---|---|
| **Planner** | Strategy. Turns a request into a precise blueprint. Decides what to try next. | Contract, progress diary, evaluation reports, device budget, Vivado's own QoR suggestions |
| **Generator** | Code. Writes Verilog based on one instruction. | Current code and the instruction. Nothing else |
| **Evaluator** | Grading. Checks results against the contract, line by line. | Generated code, Vivado metrics, the contract |
| **Timing Doctor** | Specialist. Fixes designs that are correct but too slow. | The failing timing path and a precise surgical instruction |

The roles communicate only through files on disk: `contract.md`, `plan.md`, `progress.md`, `designs.jsonl`. This is also how resume works — those files are the complete state.

### The verification ladder

Every candidate climbs five rungs before it can influence anything. Cheaper tests come first so bad code dies in milliseconds, not minutes.

| Rung | Check | Speed |
|---|---|---|
| 1 | Static: right module name? right ports? no banned constructs? no inferred latches? declared latency matches contract? | Instant |
| 2 | `xvlog` compile: syntax correct? | Seconds |
| 3-4 | Simulation: does it pass the testbench? (batch flow, no project creation) | Under a minute |
| 5 | Synthesis + implementation: real resource counts, real timing | Minutes |

A candidate that fails rung 1 costs milliseconds. This is what makes the rest of the system affordable.

### Correctness you can trust

For every module, the system requires a **golden model** — a tiny Python program that computes the right answer. The harness generates the Verilog testbench automatically from the golden model and runs both: if outputs disagree, the design is wrong.

Two comparison modes handle different hardware styles:
- **Fixed-latency** (FIR filters, pipelines, counters): expected outputs are delayed by the declared number of clock cycles before comparing.
- **Scoreboard** (streaming valid/ready interfaces): expected outputs are queued per accepted input and compared per output, making latency irrelevant.

Before the testbench grades anything, it must prove it can catch bugs. The harness sabotages a copy of the design (flips a comparison, adds one where it shouldn't) and requires the testbench to **fail** it. A testbench that passes broken code is itself broken.

### Best-of-4 with forced diversity

For each attempt, the generator writes four versions pushed in different directions on purpose:

- One standard version
- Two shaped by the objective (for smallest area: narrow the arithmetic, share hardware; for top speed: pipeline it, use DSP blocks)
- One wildcard told to ignore the obvious structure entirely

Four tries from the same prompt tend to be four copies of the same mistake. Forced variety means architectural failures are independent. Duplicates are detected by code fingerprint and run only once. The winner is picked by deterministic sorting: most verification rungs passed, then best score on the objective, then shortest code. No AI picks the winner.

### The Timing Doctor

When a design is correct but too slow, the Doctor takes over with a strict escalation:

1. **Tool knobs first** — Vivado's own retiming and physical optimisation. Zero code changes, zero AI calls.
2. **Surgery second** — the harness reads the failing path, diagnoses the cause (too many logic levels -> pipeline; too high fanout -> replicate the source), and gives the Doctor a precise instruction. The result re-enters the ladder like any other candidate.
3. **Replan last** — a large deficit usually means the architecture is wrong. The planner starts fresh.

### The error dictionary

Every Vivado message carries an official ID like `[Synth 8-327]`. The system keeps a dictionary mapping IDs to plain-English meaning and a specific repair instruction written for the generator. When a build fails, the model receives the diagnosis, not a 2,000-line log dump. Unknown IDs are queried from Vivado's own built-in documentation and logged for post-run curation.

The dictionary also **promotes** dangerous-but-silenced conditions (inferred latches, multi-driven nets) to hard errors so they fail loudly at compile instead of surfacing as mysteries three rungs later. Promotion only, never demotion — the system is never allowed to silence warnings to make a run look clean.

### Vivado's own advisor in the loop

After synthesis, the system runs `report_methodology` and `report_qor_suggestions` and feeds the output to the **planner** as evidence. The planner reads Vivado telling it "there's an unsafe CDC crossing" or "pipeline this multiplier" — the tool that judges the result directly advising the agent that writes for it. Advisory only; methodology violations never block a candidate.

### Skills: the system's memory

The folder `.claude/skills/` holds eight guidebooks with verified code snippets — accumulated hardware knowledge written as short imperative rules the generator can follow.

| Skill | What it teaches |
|---|---|
| `autortl-conventions` | Law: output format, interface rules, latency declaration, promote-never-demote. Every AI call, always |
| `verilog-idioms` | Two-process FSM, latch avoidance, reset discipline, valid/ready handshakes |
| `vivado-driving` | Forward-slash paths on Windows, the batch fast path, stale-cache traps |
| `xilinx-inference` | Coding patterns for DSP48 and BRAM inference |
| `timing-closure` | Reading failing paths, when to pipeline, when to replicate |
| `cdc` | Clock domain crossings — simulation lies about metastability, only correct structure helps |
| `testbench-craft` | Writing tests that actually catch bugs |
| `fpga-methodology` | Planning rules from AMD UG949: pipeline budgeting, resource fit, control planning |

Skills load on demand based on the design's typed metadata (protocol, clock domains, behavior keywords). They grow over time: every repeated failure pattern is a candidate for a new entry.

### Device-aware planning

The planner receives the physical limits of the target device before writing any plan: DSP count, BRAM tiles, LUTs, logic-level budget at the target frequency. No contract can be negotiated that exceeds what the chip physically has.

---

## Architecture

```
autortl_v4/
+-- run.py                      CLI: optimize | build | resume | bench
+-- autortl/                    the harness (23 modules)
|   +-- spec.py                 typed design schema (the blueprint law)
|   +-- linter.py               contract linter + stub elaboration + mechanical wiring
|   +-- static_checks.py        ladder rung 1 (milliseconds)
|   +-- vivado.py               xvlog | xsim | synthesis | advisor digest
|   +-- golden.py               Python oracle framework
|   +-- tbgen.py                testbench autogeneration (fixed-latency + scoreboard)
|   +-- tbqual.py               oracle qualification by bug injection
|   +-- bestofn.py              objective-weighted mutations + dedupe + selection
|   +-- timing_doctor.py        timing triage and escalation
|   +-- taxonomy.py             error + methodology dictionary
|   +-- triage.py               infra vs design failure classification
|   +-- metrics_gate.py         parsed metrics sanity gates
|   +-- cache.py                code-hash and contract-hash caches
|   +-- budget.py               LLM call and Vivado time accounting with degradation
|   +-- watchdog.py             deterministic pathology signals (stagnation, churn)
|   +-- device.py               device budget loader
|   +-- skill_loader.py         harness-side skill injection
|   +-- roles.py                Planner | Generator | Evaluator | TimingDoctor
|   +-- fsm.py                  the orchestrator (resumable state machine)
|   +-- ...
+-- llm/
|   +-- routing.yaml            model policy (edit chains per role, no code changes)
|   +-- client.py               one public function: ask(role, prompt, ...)
|   +-- backends/               Codex CLI (active); historical adapters retained
+-- data/
|   +-- taxonomy.yaml           error + methodology dictionary
|   +-- parts.yaml              physical budgets per target device
+-- .claude/skills/             8 SKILL.md guidebooks + verified snippets
+-- curriculum/                 tiered benchmark designs (6 tiers, easy to brutal)
+-- tests/                      91 automated checks on the harness
+-- docs/
    +-- DESIGN.md               architecture spec (single source of truth)
    +-- DOCUMENTATION.md        file-by-file implementation record with design rationale
```

---

## Results (on the included counter design)

| | Baseline | Best found | Change |
|---|---|---|---|
| LUTs | 67 | **48** | -28% |
| FFs | 37 | 37 | — |
| WNS | +4.433 ns | +4.092 ns | timing met |
| Iterations to best | — | 2 | — |

The system discovered that all three comparison thresholds (100, 500, 1000) fit within 10 bits, narrowed the comparators from 32-bit to 10-bit, and let Vivado synthesise cheaper logic. This was not prompted — the planner inferred the opportunity from the Vivado report and the reflection on the previous iteration.

---

## Getting started

**Requirements:** Python 3.11+, Vivado 2024.x or 2025.x, Git, and an authenticated Codex CLI.

```bash
pip install -r requirements.txt
python -m pytest tests/ -q
```

**Codex-only workers:** run `codex login status` to check the existing login.
If needed, authenticate with `codex login`. All four roles use `codex.default`
in `llm/routing.yaml`; the configured Codex model is retained. There are no
external-provider fallbacks. Optionally set `AUTORTL_CODEX_BIN` to the CLI path.
See [Codex operation](docs/CODEX_WORKERS.md) for the bounded verification trial.

**Optimize an existing design:**
```bash
python run.py optimize \
  --design counter.v --tb counter_tb.v --top counter \
  --objective minimize_luts \
  --vivado "C:/AMDDesignTools/2025.2/Vivado/bin/vivado.bat" \
  --xvlog  "C:/AMDDesignTools/2025.2/Vivado/bin/xvlog.bat" \
  --xelab  "C:/AMDDesignTools/2025.2/Vivado/bin/xelab.bat" \
  --xsim   "C:/AMDDesignTools/2025.2/Vivado/bin/xsim.bat"
```

**Build from a description:**
```bash
python run.py build --spec curriculum/tier1/debouncer_build/spec.md
```

**Resume a stopped run:**
```bash
python run.py resume --run logs/run_v4_20260713_120531/
```

**Run the test curriculum:**
```bash
python run.py bench --tier 0      # smoke (counter + mux)
python run.py bench --tier 1      # PWM + debouncer build
python run.py bench --tier 2      # FIR at 150 MHz
```

---

## The test curriculum

Designs are organised in six tiers, easy to brutal. A tier is considered held when three consecutive runs pass at least 80% of its entries. Regressions on held tiers block harness changes.

| Tier | Contents | Stresses |
|---|---|---|
| 0 | Counter (the v3 regression bar: 48 LUTs), 4-to-1 mux | Plumbing smoke test |
| 1 | PWM generator, debouncer (build mode from prose spec) | Golden models, generated testbenches |
| 2 | 8-tap FIR at 150 MHz | DSP48 inference, pipelining, Timing Doctor |
| 3 | UART TX + FIFO (build mode, two modules + mechanical wiring) | Multi-module decomposition, scoreboard testbench |
| 4 | RTLLM v2 + VerilogEval problems (to populate) | **Direct comparison with CRADLE's published 48% LUT / 40% FF reductions** |
| 5 | AES round, async FIFO CDC exam, RISC-V slice (to populate) | Caching, replanning, budget behaviour under load |

---

## Key design decisions

**The harness is the intelligence, not the model.** Every decision that can be made deterministically is. The AI fills in only what creativity requires. Wiring, selection, correctness grading, bug qualification — all plain code.

**Infra failures never touch the design.** Vivado file locks, license hiccups, and network timeouts are classified and retried. Correct code is never "fixed" because a file was locked.

**Spec is law.** Module interfaces and latency are contract fields. Generated code that violates them is rejected at rung 1 before it wastes Vivado time.

**Promote, never demote.** Vivado severity levels can be raised (inferred latches become errors). They are never lowered. A clean run must be genuinely clean.

**91 tests test the harness, not the designs.** Every parser, gate, cache, and classifier has coverage. Two real bugs were found and fixed by the test suite during development — the only reason to trust a harness this complex is that it proves its own correctness.

---

## How it compares to published work

| System | Targets | Toolchain | Agentic structure |
|---|---|---|---|
| **CRADLE** (2024) | Verilog optimisation | Yosys (open source) | Single agent, no verification ladder |
| **VFlow** (2025) | Verilog generation | Iverilog/Yosys | Multi-agent with workflow, no Vivado |
| **MCP4EDA** (2025) | EDA tool orchestration | Various | Tool integration, not design generation |
| **AutoRTL v4** | Both generation and optimisation | **Vivado (proprietary, industry standard)** | 4 isolated roles, 5-rung ladder, best-of-4, Timing Doctor, contract negotiation, skills library |

Key differentiators: Vivado-native (the tool industry actually uses), role isolation (generator never grades itself), the verification ladder (fail in ms not minutes), testbench qualification (the oracle proves it catches bugs), and skills as a model-independent knowledge system that grows from run history.

---

## Background

Final-year Electrical and Electronics Engineering capstone at Ashesi University. The project explores whether agentic AI systems can match or exceed published results on RTL optimisation benchmarks, using the same proprietary toolchain working engineers use.

The approach draws from published work on agentic hardware design (CRADLE, VFlow, MCP4EDA) and from Andrej Karpathy's field notes on long-running agent loops — specifically the insight that the loop is the unit of leverage, not the prompt.

---

## License

MIT
