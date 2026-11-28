# Using AutoRTL

Moved from the README on November 15, 2026.

## Quick start

Requirements: Python 3.12, Vivado with the target device installed, and, for
model-driven runs, an authenticated Codex CLI or any other model endpoint
(see Bring your own model below). Roles are routed through
[`llm/routing.yaml`](../llm/routing.yaml).

```powershell
python -m pip install -r requirements.txt
```

To see one run's pipeline without Vivado or a model login, run the simulated
walkthrough. It optimizes `mux4` once with fixed stand-ins, measures nothing,
and prints where the run's journal, events and summary are:

```powershell
python scripts/demo.py
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

Check the machine first. `doctor` finds Python and its packages, the four
Vivado tools and the Codex CLI login, and prints the exact fix for anything
missing. It runs no design and sends nothing to a model:

```powershell
python run.py doctor @vivadoArgs
```

Then run the repeatable counter tool check without model calls:

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
includes [signed FIR](../curriculum/tier3/signed_fir4_build/),
[counter8](../curriculum/tier1/counter8_build/) and
[priority encoder](../curriculum/tier1/encoder8_build/) specifications with
independent top-level testbenches. Supply these using `--spec`, `--tb` and `--top`.
Add `--generate-golden` to combine generated Python/unit verification with the
independent testbench. See the
[golden verification guide](GOLDEN_VERIFICATION.md) for semantics and limits.

Choose the model with `--model` (any model alias the Codex CLI accepts, for
example `gpt-6-luna` or `gpt-5.6-luna`). Every role uses it, it is saved in the
run's `config.json`, and the curriculum records it as the requested model
identity, so runs on different models never share a cohort. Without `--model`
the CLI's own default is used and the model identity is recorded as unobserved.
The role parsers accept the fence tags and verdict layouts different models
write (`Verilog`, `v`, `py`, `Recommendation: ACCEPT`), and a planner-written
spec that fails the structural check gets its errors back for a bounded repair.

To run the roles on any OpenAI-compatible chat-completions API instead of the
Codex CLI, set `AUTORTL_OPENAI_API_KEY` in the environment and pass
`--model openai.<model>` (for example `--model openai.gpt-4o-mini`). The
endpoint defaults to `https://api.openai.com/v1`; set
`AUTORTL_OPENAI_BASE_URL` to use another provider or a local server such as
Ollama (`http://localhost:11434/v1`) or vLLM (`http://localhost:8000/v1`).
Local servers that ignore the key still need a placeholder value. The key is
read only from the environment and is never written to run files or logs.
`python run.py doctor` reports whether the key is set.

**Bring your own model.** To plug in any AI, name it in
`endpoints.local.yaml` at the repository root (Git ignores it; copy
[`llm/endpoints.example.yaml`](../llm/endpoints.example.yaml)) and pass
`--model <endpoint>.<model>`. An endpoint is either an OpenAI-compatible URL,
with an optional `api_key_env` naming the variable that holds its key, or a
command line that reads the prompt on stdin and prints the answer, such as
another vendor's CLI or your own script:

```yaml
endpoints:
  ollama:
    kind: openai
    base_url: http://localhost:11434/v1
  mine:
    kind: command
    argv: [python, my_model.py]
    model_flag: --model
```

`--model ollama.llama3.1` or `--model mine.small` then routes every role to
it. Several endpoints can be defined side by side, `doctor` checks each one,
and an endpoint's definition is part of the bench cohort, so editing it starts
a new cohort. Commands run without a shell from an empty temporary folder and
only ever receive the prompt on stdin; AutoRTL does not sandbox them, so give
them no tools they do not need.

**Antigravity models.** [`scripts/agy_bridge.py`](../scripts/agy_bridge.py)
puts the Antigravity CLI (`agy`) behind a command endpoint, so the models it
offers (`agy models`: Gemini, Claude, GPT-OSS) can run every role:

```yaml
endpoints:
  antigravity:
    kind: command
    argv: [python, C:/absolute/path/to/scripts/agy_bridge.py]
    model_flag: --model
```

then, for example, `--model antigravity.gemini-3.8-flash-low`. The bridge
sends the prompt on stdin through `agy`'s stream-json mode with `--sandbox`
and prints only the final answer; a failed result exits 1 so quota and login
errors are classified like any other CLI.

`agy` is an agent, not a plain model call. `--sandbox` restricts its terminal,
not its tools: on November 21 Flash-high web-searched the task name and ran
shell commands while planning, taking 6 minutes for one planner prompt, and
permission deny rules did not stop it. The bridge therefore refuses any reply
produced with a tool call (exit 1). Prefer the `-low` variants: on the same
planner prompt Flash-low used no tools and answered in 18 seconds.

Resume an interrupted experiment using its saved configuration:

```powershell
python run.py resume --run runs/mux-trial
```

Use a fresh output directory for each new experiment. Resume checks the saved
inputs and execution environment; see [recovery behavior](RECOVERY.md).

The same steps in bash (Linux or Git Bash). On Linux the tools have no
`.bat` suffix; in Git Bash, add it as in the PowerShell example:

```bash
vivado_bin=/path/to/Vivado/bin
vivado_args=(--vivado "$vivado_bin/vivado" --xvlog "$vivado_bin/xvlog"
             --xelab "$vivado_bin/xelab" --xsim "$vivado_bin/xsim")

python run.py doctor "${vivado_args[@]}"

python scripts/check_counter_cli.py --bin-dir "$vivado_bin" --output runs/counter-check

python run.py optimize --design curriculum/tier0/mux4/mux4.v \
  --tb curriculum/tier0/mux4/mux4_tb.v --top mux4 \
  --iterations 1 --best-of-n 1 --max-llm-calls 16 \
  --max-vivado-minutes 20 --max-wall-minutes 30 \
  --output-dir runs/mux-trial "${vivado_args[@]}"
```

## Development and evaluation


Continuous integration
([`.github/workflows/tests.yml`](../.github/workflows/tests.yml)) runs the full
harness suite on Windows, the mailbox and board-suite tests on Windows and
Ubuntu, and the evidence audit. None of these need Vivado, a model login or a
board.

```powershell
python -m pytest tests/ -q
python -m pytest coordination hardware/basys3/harness_winners/tests hardware/basys3/fmax/tests tools/tests -q
python tools/evidence_audit.py --rev HEAD
python run.py bench --tier 0 --iterations 1 --best-of-n 1 `
  --max-llm-calls 16 --max-vivado-minutes 20 --max-wall-minutes 30 `
  --output-dir runs/tier0 @vivadoArgs
```

Add `--jobs 4` to run up to four entries at once as separate processes; the
cohort and promotion rules do not change. Each run's `budget.json` records the
model tokens it used, and `python tools/role_report.py <campaign>` summarizes
every role's calls, tokens, verdicts and repairs.

`python tools/run_view.py <run-or-campaign> [--out FILE]` writes the same
records as one static HTML page (default `<dir>/run-view.html`): a summary
table across entries, then per run the role calls, the stage timeline from
`events.jsonl`, each iteration's metrics against the baseline with the
evaluator's report, the repairs, and the winning RTL as a diff against the
baseline. It uses only the standard library, loads no external resources and
escapes all text read from run files.

`python tools/replay_run.py --run <run> --out <parent>` replays a recorded run
from its journal with every model and Vivado entry point replaced by one that
refuses, then compares the files the harness rebuilds with the recorded ones
(exit 0: same; 1: a difference, a missing file or a call the journal does not
hold). Use it as the acceptance test for refactors that must not change
behaviour: replay recorded runs on the old and the new code. It runs in about
half a minute per run and needs neither Codex nor Vivado. Give it the original
run directory, not an archived copy (archives sanitize paths, so their journal
fails its own hash check), and an `--out` shorter than the run's path: the
replay directory is padded to the recorded path's length so the fixed-length
report previews the harness keeps are cut at the same character. Set
`PYTHONPATH` to another checkout (for example a `git archive` of an older
commit) to replay on that code.

What replays: on November 28, every sampled run recorded on harness code
from October 30 onward that did not stop on a budget (13 runs: done,
baseline_failed and module_failed) rebuilt byte-identical files on the code
that recorded it, and the release re-hold run did so on both the release and
the current code. Three kinds of run do not replay. A run that stopped on a
wall-clock or Vivado-time budget ends in a refused call, because replay does
not reproduce elapsed time. Runs from before October 30 fail their own
checks, because their journals did not yet keep every piece of evidence
those checks re-read. And files that other scripts added to a run directory
afterwards (study results, proofs) are reported as missing.

Curriculum promotion requires three consecutive qualifying full runs with the
same experiment cohort. Subset runs cannot promote a tier, and regressions in
previously passing entries of a held cohort block qualification.

Start with the [guided code tour](WALKTHROUGH.md), which follows one run
through the code with file and line references. Then read the
[architecture](DESIGN.md), [recovery and validation guide](RECOVERY.md),
[research and adoption decisions](RESEARCH.md),
and [engineering evidence log](PROGRESS.md).
