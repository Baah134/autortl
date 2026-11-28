# Sampling clarity and source identity traversal

This batch preserves the stopped signoff4-t6-02 attempt and addresses two
observed reliability problems, without changing design/verification budgets,
testbench comparisons or adding agent roles. The FPGA was connected but no
board, serial, JTAG, hardware-server, programming or reset action was performed.

## Changes and evidence

- The planner prompt now states the existing fixed-latency observation phases,
  distinguishes scoreboard transfer age and requires defined invalid data.
  Three earlier UART/FIFO plans had assigned phase zero to post-transition
  state. Their full diagnosis is in the preceding parallel-diagnoses archive.
- Source identity traversal prunes the exact excluded agent-worktree subtree
  before visiting it. Selection and raw-byte hashing are preserved, tested
  against the independent legacy selector. Synthetic excluded-directory scans
  decreased from eight to zero. No live speedup ratio is claimed.
- README claims distinguish handwritten board shells and parameter overrides,
  standalone FIR16 timing at150MHz from physical-board100MHz, timing progress
  from closure, and recorded results from an uncompleted public comparison.

## Verification

See software-results.json and raw harness/tooling output for the complete
software counts, real exits, skipped conditions and337 frozen input hashes.
The independent sampling review passed114 focused tests before integration.
Before/after failure logs and reviewed patches are retained separately.

Real Vivado2025.2 simulation: combinational0 passes; clocked1 passes; identical
clocked RTL/oracle/stimulus at0 fails through exactly three data assertions.
All nine compiler/elaborator/simulator exits are zero. The portable replay was
then executed successfully against these archived inputs. This establishes the
sampling behavior, not improved model success. Windows junction tests executed;
the symbolic-link test skipped because native privilege was unavailable.

From a clone with the normal Python dependencies and Vivado installed:

```powershell
python evidence/2026-11-07/reliability-01/replay_sampling_controls.py --vivado-bin C:/AMDDesignTools/2025.2/Vivado/bin --output-dir C:/Temp/autortl-sampling-new
```

The output directory must not already exist. This invokes only xvlog/xelab/xsim,
never board tools. Existing absolute run paths in raw receipts describe the
original machine; the replay resolves the archived input paths locally.

## Original interruption and limits

Tier6-02 had2022 passing software tests, then all three model dispatches were
blocked by CODEX_QUOTA. Its controller exit was1073807364; the final launch
receipt is absent and there is no design verdict. Its unchanged96-entry
archive is published separately. Original334 source inputs were verified
before edits; source changes now require a new attempt directory and identity.

No new curriculum hold, benchmark score, model-superiority claim or physical
board measurement is made here. The benchmark adapter report is a research
proposal; no scored task roster or trial exists. A PATH check found no local
Docker/Icarus tools, and wsl --list reported WSL uninstalled; no tools were
installed. The next AES plan uses current-tier exploration with original limits,
after the worker tool configuration has been restricted and validated.
