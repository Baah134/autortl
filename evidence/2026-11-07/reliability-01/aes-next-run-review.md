# Fresh AES exploration: one software-only job

Read-only review completed against the current canonical checkout after root's
integration. This review launched no model, vendor, programming or board job and
changed no canonical file. It did not repeat root's software regression.

The accepted next experiment is one fresh `aes128_core_build` exploration,
after the integrated source passes tests and is committed. It is current tier6,
not a lower-tier re-hold, a new final sign-off pass, a benchmark, or a board test.
Preserve signoff4-t6-02 as infrastructure-blocked; do not resume it under changed
source, reuse its directory or reset its spent budgets.

## Verified entry and exact invocation

Canonical working directory:
`C:/Users/prince.baah/Downloads/autortl-work`.

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONPATH = 'C:/Users/prince.baah/Documents/Codex/2026-10-15/hey/work/review_deps'
$env:AUTORTL_CODEX_BIN = 'C:/Users/prince.baah/AppData/Local/OpenAI/Codex/bin/a159911ff70742e9/codex.exe'
& 'C:/Users/prince.baah/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' tools/explore.py --tier 6 --entries aes128_core_build --name explore-aes-20261107-01 --jobs 1 --model gpt-6-luna --python 'C:/Users/prince.baah/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' --vivado-bin 'C:/AMDDesignTools/2025.2/Vivado/bin' *> 'logs/explore-aes-20261107-01.console.txt'
$aesExplorationExit = $LASTEXITCODE
```

Root should launch through its existing supervised process wrapper so the actual
parent/child PIDs, start/exit, command and transcript are retained. The example
is the exact workload; it does not authorize a second launcher. Do not pre-create
`logs/explore-aes-20261107-01`: explore refuses an existing base. Both proposed
base and outer console were absent at this inspection; recheck immediately
before launch and use a new declared name if another coordinator has used them.
The selected Codex executable and Vivado batch executable exist; run-time
readiness and quota have not been established by their existence.

`tools/explore.py:36-77` derives the child command from the original metadata:

| Setting | Unchanged value |
|---|---|
| Entry / mode / top | aes128_core_build / build / aes128_core |
| Input contract | curriculum/tier6/aes128_core_build/design_spec.json |
| Independent integration TB | curriculum/tier6/aes128_core_build/aes128_core_tb.v |
| Unit oracle generation | --generate-golden |
| Iterations / candidates | 4 / 1 |
| Model calls / infrastructure retries | 30 / 1 |
| Total tool / total wall budget | 150 / 240 minutes |
| Per-synthesis/implementation deadline | 45 minutes, still capped by remaining budgets |
| Objective | minimize_luts |
| Part / target | xc7a35tcpg236-1 / 100MHz (10ns) |
| Implementation | out_of_context |
| Requested model | gpt-6-luna, all roles via current codex route |
| Parallel entries | 1 |

No extra model "smoke test" is needed: the first real generation call can report
quota/auth/network failure within the original budget. Do not silently substitute
a model/provider or increase limits if it fails. Requested model identity and
any observed model metadata remain separate; retain unknown fields as unknown.

## What this command can reach

The deterministic path is `tools/explore.py` → preflight `run.py doctor` → one
`run.py build` → `Orchestrator` → generated-oracle qualification, static checks,
`xvlog`/`xelab`/`xsim` and fixed-template batch Vivado implementation.

- `autortl/doctor.py:70-102` checks file resolution, `xvlog --version`, Codex
  `--version` and `login status`. It does not connect to hardware or test model
  quota. Readiness must explicitly show the **selected Codex** executable/login
  available: another configured optional backend can otherwise make missing
  Codex nonfatal in this generic doctor.
- `autortl/vivado.py:183-229` runs compile/elaboration and `xsim -runall` in
  per-run working directories. The trusted AES TB has no `$system`, file-open,
  foreign-language, include or memory-file directive matched by this review.
  Model RTL passes `static_checks.check`; its safety check rejects system tasks
  beyond `$signed`, `$unsigned`, `$clog2`, `$bits`, and rejects directives other
  than timescale. Oracle Python is interpreted in the restricted golden worker.
- `autortl/vivado.py:278-304` chooses the fixed OOC template: read source,
  create a 10ns clock, OOC synthesis, optimization, placement, routing and reports.
  Those are offline implementation calculations. The template does **not**
  generate a bitstream, open/connect a hardware manager, launch hw_server,
  program a device, read back a device, access JTAG or open a serial port.
  The timing XDC has no package-pin/IOSTANDARD programming constraints and OOC
  inserts no chip-top I/O buffers. Timing covers internal clocked paths only.
- `autortl/vivado.py:327-350` invokes `vivado -mode batch -source <fixed-script>`;
  Doctor variations are the fixed `-retiming` and `phys_opt_design`/`-hold_fix`
  choices. Source text is never interpolated as a new TCL command. No hardware
  module or `hardware/basys3` script is imported by this reviewed path.

There is one explicit limit to the isolation claim: the current Codex adapter
(`llm/backends/codex_cli.py:175-199`) requests "Do not use tools or change files"
and uses `exec --sandbox read-only --ephemeral --json`, a temporary cwd and
`shell=False`. It does not disable inherited MCP/tool configuration or reject
tool events. Names-only inspection of local config found `mcp_servers.node_repl`.
Therefore this is a review of the actual deterministic software commands, **not
proof that every possible worker capability is physically disconnected from
the board**. Do not tell the user the backend enforces a no-tools boundary.
Root must keep all workers away from hardware commands, and treat any unexpected
tool/device/programming action as a reason to stop that owned worker. A stricter
tool-disable control would require a separately tested adapter change and fresh
source identity; do not add unverified CLI flags to this frozen experiment.

## Ownership, source freeze and evidence

Process inventory at this review showed Python11972 and its pytest child15452;
there was no Vivado/xvlog/xelab/xsim/hw_server and no identified
run.py build/optimize/bench/resume, signoff, gate or exploration process. This is
a point-in-time observation, not a future lock. Wait for root's tests, query
ownership and actual processes again before launch. One coordinator owns the
queue and only one entry is launched; do not spawn another tool campaign from a
subagent. Leave unfamiliar processes and any user's GUI sessions untouched.

After tests and commit, before launch root should retain a fresh manifest with:

1. Exact commit and dirty/index state; source hashes from current
   `tier0_gate.identities()`, plus tools/explore.py and tools/tier0_gate.py
   explicitly (tools lies outside that selection).
2. AES metadata, typed spec and independent TB hashes; current routing.yaml,
   Python identity, verified executable/tool versions or hashes, actual argv,
   budgets, part/clock/OOC mode, launch time and owned PID tree. Never include
   credentials or the private coordinator token.
3. Original bytes/prefix lengths for curriculum/results.jsonl and
   llm/router_stats.jsonl. Exploration must not add a curriculum verdict;
   expected router records append. Freeze source/configuration throughout the
   run; do not edit model prompts or helper/runtime inputs mid-experiment.

FSM `autortl/fsm.py:246-303` independently writes runtime.json, copies spec/TB to
inputs/, binds hashes in inputs.json and saves the actual config.json. Preserve
these with state/journal, budget.json, all child oracles/TBs/candidates, raw tool
outputs and exits, console, routed timing/utilization reports and run_summary.
After completion verify source/input hashes and ledger prefixes and archive
everything needed for the result under a fresh evidence directory with manifest.
Failures stay in the same archive and denominator.

Expected output files:

- logs/explore-aes-20261107-01.console.txt (outer launcher/doctor/results);
- logs/explore-aes-20261107-01/aes128_core_build.console.txt (build transcript);
- logs/explore-aes-20261107-01/explore.json (one entry only);
- logs/explore-aes-20261107-01/aes128_core_build/ (full runtime evidence).

`tools/explore.py` returns zero after collecting entries even if its child failed.
Do not use that outer exit alone as success. Inspect the sole entry's actual
exit/status/failure kind, run_summary, assertions, real process receipts and
metrics. DONE requires the generated-oracle and independent integration paths
to have completed; timing closure must be checked separately against routed OOC
setup/hold at 100MHz. Any claimed LUT improvement must identify verified baseline
and winner on identical constraints, not merely compare unrelated archives.

## Stop conditions

- Preflight failure, missing selected Codex login, source/ownership drift,
  existing output, or an owned competing implementation job: **do not launch**.
- CODEX_QUOTA or CODEX_AUTH: accept the first genuine call's recorded block,
  archive it as infrastructure and stop this experiment queue. Client code
  already propagates those without a same-backend retry. Doctor passing does
  not establish quota recovery; the previous retry-after text is not proof.
- Network/timeout/tool failure: allow only existing configured bounded retry
  behavior; retain the real infra outcome. No budget enlargement, new provider,
  or immediate repeated fresh run to wash away the failure.
- Source/input integrity failure, missing exit evidence or unexpected hardware
  action: stop only this owned tree through its normal cancellation path and
  preserve receipts. Never taskkill by image name or stop unfamiliar GUI/jobs.
- Generated oracle/RTL/spec failure: preserve exact errors/candidates under
  original limits, diagnose the first actionable failure, and finish the run
  as failed if repairs are exhausted. Do not weaken the verification contract.
- Completion or budget exhaustion: archive once, verify source hashes, review
  evidence before another implementation decision. This single exploration
  cannot establish a tier hold, general model superiority or new board proof.
