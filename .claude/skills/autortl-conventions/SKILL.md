---
name: autortl-conventions
description: "The law of the AutoRTL system. Always loaded into every role's system prompt. Defines the spec schema, output format rules, latency declaration, and the promote-never-demote message policy."
---
# AutoRTL Conventions (LAW — always in force)

## Output format
- Verilog goes in exactly ONE ```verilog fence. Nothing else in the fence.
- Python golden models go in exactly ONE ```python fence.
- Never wrap testbenches or reference material in ```verilog fences — those use ```text.

## Interface law
- The module name, port names, and port widths in the contract are EXACT. Never add, rename, or resize a port.
- The top-level clock is always named `clk`. The reset signal name, polarity, and kind come from the contract's reset spec.

## Latency law
- Every generated module declares its pipeline depth in a header comment: `// @latency N`.
- N must equal the contract latency. If your implementation would change latency, you still match the contract — the spec is law. Latency changes happen by contract amendment only.

## Coding rules
- Synchronous resets: `if (rst)` inside `always @(posedge clk)` (unless the contract says async).
- No `initial` blocks in synthesisable code.
- In every combinational `always @(*)` block, assign every output a default at the top of the block.
- One driver per signal: each reg is assigned from exactly one always block.

## Vivado message policy
- Message severities may be PROMOTED to ERROR (e.g. inferred latch). They are NEVER demoted or suppressed. A clean run must be genuinely clean.

## File boundaries
- LLM output lands only in .v (or .py for golden models). No LLM string is ever interpolated into TCL, shell, or paths.
