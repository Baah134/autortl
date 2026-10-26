# AutoRTL

**An AI-assisted RTL design and optimization harness with verification at every stage.**

AutoRTL turns hardware specifications into Verilog and iteratively improves
existing designs using AMD Vivado. Planner, generator, evaluator and timing
specialist roles propose changes; simulation, implementation reports and
deterministic acceptance gates decide which results survive.

The goal is a repeatable autonomous engineering loop: generate, verify, measure,
learn from failures, and retain the best correct design within a fixed budget.

## Verified progress

| Validation | Recorded result |
|---|---|
| Harness regression | **1,429 tests passed** |
| Signed stateful FIR filter | **78 → 52 LUTs · setup −0.327 → +0.169 ns · hold +0.106 ns · independent 800-cycle test passed** |
| Elastic dot product | **328 → 20 LUTs · 4 DSPs · setup +0.155 ns / hold +0.206 ns · independent 852-cycle test passed** |
| Three-module pipelined dot product | **325 → 17 LUTs · 4 DSPs · independent 685-cycle test passed** |
| Iterative divider (8-bit) | **38 → 26 LUTs · setup +0.315 ns / hold +0.129 ns · saved winner independently passed** |
| FIFO timing recovery | **Setup −0.931 → +0.108 ns · hold +0.076 ns · 22 LUTs / 13 FFs** |
| Packet-tagged FIFO | **23 LUTs / 31 FFs · setup +0.078 ns / hold +0.106 ns · saved winner independently passed** |
| Fault-qualified independent verification | **27 signed FIR faults, 18 elastic arithmetic faults and 20 divider faults detected; correct controls passed** |

Measurements use Vivado 2025.2, `xc7a35tcpg236-1`, a 10 ns clock and ideal zero
minimum/maximum I/O delays. These are benchmark constraints; board pins,
external interface timing and hardware deployment require separate validation.
See [hardware targets and validation scope](docs/TARGETS.md).

The FIR first recovered timing at 80 LUTs, then reduced that feasible design to
52 LUTs. FFs change from 66 to 67, DSP use stays zero and reported estimated
power stays 0.088 W. Its exact saved winner passed independent replay; completed
reuse and six restored integrity probes preserved its result and budget.

Dot-product area reductions trade fabric logic for four DSPs; slice FF counts
exclude DSP internal registers. Estimated power increased from 0.138 to 0.149 W
for the elastic design and from 0.157 to 0.158 W for the three-module design.
The divider's estimate increased from 0.092 to 0.103 W. FIFO timing recovery
uses more area than its failing baseline. Report these tradeoffs together.

These are bounded experiments, not formal equivalence, arbitrary-board support
or evidence that every model improves. No held curriculum tier or controlled
weak-model advantage is claimed. Unsuccessful proposals and earlier designs
remain in the [engineering evidence log](docs/PROGRESS.md).

Evidence: [signed FIR](evidence/2026-10-26/generated-signed-fir4-attempt-01/README.md),
[FIR fault qualification](evidence/2026-10-25/signed-fir4-admission-attempt-01/README.md),
[full regression](evidence/2026-10-26/signed-fir4-tests-01/README.md),
[elastic dot product](evidence/2026-10-25/generated-elastic-dot4-attempt-02/README.md),
[three-module dot product](evidence/2026-10-24/generated-dot4-attempt-01/README.md),
[divider](evidence/2026-10-23/generated-divider-attempt-01/README.md),
[FIFO](evidence/2026-10-22/generated-fifo-attempt-05/README.md) and
[packet FIFO](evidence/2026-10-22/generated-packet-attempt-01/README.md).

## The design loop

```mermaid
flowchart LR
    A[Specification and contract] --> B[Generate candidates]
    B --> C[Static checks and compilation]
    C --> D[Qualified simulation]
    D --> E[Synthesis and routing]
    E --> F[Evaluate verified metrics]
    F --> G[Retain best design]
    F --> B
```

- **Fixed contracts:** optimization requirements come from immutable harness
  facts. Interfaces, reset behavior and cycle latency
  are checked against explicit module specifications. Plans are bound to the exact editable RTL.
- **Verification before scoring:** testbench qualification requires a passing
  control and detection of an injected fault. Scoreboard stimulus includes eligible
  specification payload examples alongside corners and seeded random cases.
  Missing or ambiguous evidence fails.
- **Measured candidate selection:** configurable best-of-N generation and source
  deduplication preserve exact candidate identity and use verified results. Timing feasibility precedes objective
  scoring; timing recovery is recorded separately from resource savings.
- **Recoverable execution:** atomic checkpoints, frozen inputs and stage journals
  support replay; source, configuration and report drift invalidate reuse.
- **Bounded experiments:** model-call, tool-time and wall-time budgets constrain
  work. Infrastructure failures receive bounded retries without RTL mutation.
- **Traceable feedback:** sources, constraints, hashes and reports connect results
  to exact experiments. Routed path details and unsuccessful trial evidence
  inform subsequent planning; rejected measurements remain separate from winners.

## Quick start

Requirements: Python 3.12, Vivado with the target device installed, and an
authenticated Codex CLI for model-driven runs. Current runtime roles use the
configured Codex model through [`llm/routing.yaml`](llm/routing.yaml).

```powershell
python -m pip install -r requirements.txt
```

Set the Vivado installation path. The following examples use PowerShell:

```powershell
$vivadoBin = "C:/path/to/Vivado/bin"
$vivadoArgs = @(
  "--vivado", "$vivadoBin/vivado.bat",
  "--xvlog", "$vivadoBin/xvlog.bat",
  "--xelab", "$vivadoBin/xelab.bat",
  "--xsim", "$vivadoBin/xsim.bat"
)
```

First, run the repeatable counter tool check without model calls:

```powershell
python scripts/check_counter_cli.py --bin-dir $vivadoBin --output runs/counter-check
```

Optimize an existing design with a testbench and bounded resources:

```powershell
python run.py optimize --design curriculum/tier0/mux4/mux4.v `
  --tb curriculum/tier0/mux4/mux4_tb.v --top mux4 `
  --iterations 1 --best-of-n 1 --max-llm-calls 16 `
  --max-vivado-minutes 20 --max-wall-minutes 30 `
  --output-dir runs/mux-trial @vivadoArgs
```

`build` accepts a typed JSON specification or a prose request. The repository
includes [signed FIR](curriculum/tier3/signed_fir4_build/),
[counter8](curriculum/tier1/counter8_build/) and
[priority encoder](curriculum/tier1/encoder8_build/) specifications with
independent top-level testbenches. Supply these using `--spec`, `--tb` and `--top`.
Add `--generate-golden` to combine generated Python/unit verification with the
independent testbench, including child repair and optimization gates. See the
[golden verification guide](docs/GOLDEN_VERIFICATION.md) for semantics and limits.

Resume an interrupted experiment using its saved configuration:

```powershell
python run.py resume --run runs/mux-trial
```

Use a fresh output directory for each new experiment. Resume checks the saved
inputs and execution environment; see [recovery behavior](docs/RECOVERY.md).

## Development and evaluation

```powershell
python -m pytest tests/ -q
python run.py bench --tier 0 --iterations 1 --best-of-n 1 `
  --max-llm-calls 16 --max-vivado-minutes 20 --max-wall-minutes 30 `
  --output-dir runs/tier0 @vivadoArgs
```

Curriculum promotion requires three consecutive qualifying full runs with the
same experiment cohort. Subset runs cannot promote a tier, and regressions in
previously passing entries of a held cohort block qualification.

Read the [architecture](docs/DESIGN.md), [recovery and validation guide](docs/RECOVERY.md),
[research and adoption decisions](docs/RESEARCH.md),
and [engineering evidence log](docs/PROGRESS.md) for implementation details,
tested guarantees and remaining work.
