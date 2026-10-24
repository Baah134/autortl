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
| Harness regression suite | **1,340 tests passed** |
| FIFO timing recovery (8-bit, depth 3) | **Setup −0.931 → +0.108 ns · hold +0.076 ns · 22 LUTs / 13 FFs · exact saved winner independently passed** |
| Generated packet-tagged FIFO | **23 LUTs / 31 FFs · setup +0.078 ns · hold +0.106 ns · saved winner independently passed** |
| Generated iterative divider (8-bit) | **38 → 26 LUTs (31.6%) · 38 FFs · setup +0.315 ns / hold +0.129 ns · saved winner independently passed** |
| Multi-cycle divider verification | **Six widths passed; all 20 named faults detected, including stalled-result reset** |
| Packet-tagged FIFO verification | **Six configurations passed; all 19 named source mutations detected** |
| Parameterized FIFO verification | **Six configurations passed; all 13 planned faults detected** |
| Independent streaming verification | **Correct queue control passed; all eight behavior faults detected** |
| Combined-verification streaming build | **Two-entry queue · 15 LUTs / 19 FFs · independent 893-cycle test passed** |
| Generated 8-bit counter build | **Golden oracle repaired automatically; independent 700-cycle test passed · 6 LUTs / 8 FFs** |
| Generated priority encoder optimization | **6 → 5 LUTs (16.7%) · 4 FFs · exhaustive independent test passed** |
| Accepted 32-bit counter optimization | **55 → 31 LUTs (43.6%) · 37 FFs · setup slack 0.126 ns · hold slack 0.026 ns** |
| Fresh full tier 0 campaign | **2/2 passed · fresh counter 55 → 53 LUTs, mux baseline retained** |

Measurements use Vivado 2025.2, `xc7a35tcpg236-1` and a 10 ns clock,
with explicit ideal zero minimum/maximum I/O delays. These are experiment
constraints, not board timing requirements.

The 32-bit counter result passed the independent frozen testbench, actual tool-exit
checks, routed timing and final review in three model calls. Completed-run
replay retained its winner and budget without additional model or tool calls.
Counter setup slack decreased from 0.494 ns to 0.126 ns while area improved.
Additional build, weaker-model and in-flight interruption coverage remains under
validation. No held curriculum tier is claimed. Earlier unsuccessful cohorts
remain in the evidence record.

The divider result reduces area; estimated total power increased from 0.092 W
to 0.103 W under the same experiment constraints.

The packet FIFO also recovered timing from −0.946 ns with higher area than its
failing 15-LUT baseline; no overall area saving is claimed.

The FIFO trades higher area than its failing baseline (13 LUTs) for timing
closure. The loop then reduced its first feasible implementation from 24 to
22 LUTs (8.3%).

See the [FIFO recovery evidence](evidence/2026-10-22/generated-fifo-attempt-05/README.md),
[test evidence](evidence/2026-10-20/README.md),
[full-suite result](evidence/2026-10-23/proposal-fixes-tests-02/AutoRTL-proposal-fixes-full-02.txt) and
[scoreboard coverage](evidence/2026-10-23/scoreboard-example-coverage/README.md),
[divider optimization](evidence/2026-10-23/generated-divider-attempt-01/README.md),
[divider verification](evidence/2026-10-23/divider-admission-attempt-02/README.md),
[packet FIFO build](evidence/2026-10-22/generated-packet-attempt-01/README.md),
[packet FIFO admission](evidence/2026-10-22/packet-fifo-admission/README.md),
[fresh full tier 0](evidence/2026-10-23/contract-campaign-09/README.md),
[accepted optimization](evidence/2026-10-22/contract-campaign-07/README.md),
[generated-build verification](evidence/2026-10-20/generated-counter/README.md) and
[streaming build](evidence/2026-10-20/generated-streaming/README.md).

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
  are checked against explicit module specifications.
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
includes [counter8](curriculum/tier1/counter8_build/) and
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
