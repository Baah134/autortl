---
name: vivado-messages
description: "Use when diagnosing Vivado synthesis, simulation, or timing failures by message ID like [Synth 8-327]. Maps official message IDs to meaning and repair."
---
# Vivado Message ID Playbook

Every Vivado message has a stable ID: `[Facility Sub-ID]`. The taxonomy
(data/taxonomy.yaml) is the machine view; this is the model-facing view.
For unknown IDs, Vivado itself explains: `help -message {Synth 8-327}`.

## High-frequency IDs and repairs
- **[Synth 8-327] inferred latch** → add default assignments at the top of the combinational block; complete every if with else. PROMOTED TO ERROR in our flow.
- **[Synth 8-3352] multi-driven net** → one driver per signal; merge the duplicate always blocks. PROMOTED TO ERROR.
- **[Synth 8-6859] width mismatch** → regenerate port connections exactly from the contract table.
- **[Synth 8-693] unconnected port** → connect every contract port; tie unused inputs low.
- **[XSIM 43-3225] elaboration failed** → interface mismatch with the testbench: match name/ports/widths exactly.
- **[XSIM 43-4100] module not found** → module name must equal contract name, case sensitive.
- **[Timing 38-282] no clock on paths** → the clock port must be named `clk` so the auto-XDC binds.
- **[Vivado 12-4473] sim step failed** → wrapper only; the true cause is in compile.log/elaborate.log — read those IDs.

## Rules
- Diagnose by ID first; only read raw prose when no ID matches.
- New IDs seen in runs get logged to unknown_message_ids.log and curated into the taxonomy after the run.
