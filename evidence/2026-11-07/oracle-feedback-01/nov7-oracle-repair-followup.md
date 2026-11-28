# Oracle repair follow-up — November 7

Read-only review of canonical 26e18f4 and completed
`logs/explore-aes-20261107-01/aes128_core_build`. No canonical edit, model call,
vendor job, server connection or board operation by this worker. An isolated
prompt-only proposal follows the coordinator's phase decision.

## Actual failure and prompt context

`aes_ctrl` consumed all three permitted oracle attempts, with no RTL build:

1. Example1 disagreed on `ct` and `rk`.
2. The replacement exceeded the unchanged setup instruction budget.
3. The replacement was rejected as `unsupported golden call: sub_word`.

The final source defines `sub_word`, `xtime`, `aes_round` and `next_key` inside
`step`. `golden_worker.validate_source` collects callable user names only from
top-level definitions. Its rejection matches existing sandbox behavior. The
prompt's former “Helper functions are allowed” did not state this constraint.
The final source's raw SHA256 is
`5f96b618f12b0e835dd1d8902b125a1ad28e2ba298b4283d3331192af308fc47`.

The public contract already supplies `round_out` and `key_next` as input ports.
The controller's busy-edge transition consumes those values. Reimplementing
AES rounds/key scheduling inside this controller models another module's work
instead of accepting arbitrary input values. The specification includes three
examples with these neighbor inputs; qualification correctly rejects deviations.

`Generator.golden_model` currently includes behavior, ports, parameters,
comparison mode, latency and reset, but **omits ModuleSpec.examples**. In this
case its initial prompt contains none of the large expected `ct`/`rk` values.
Small expected0/1 values appear incidentally and do not establish example
delivery. This is confirmed by source inspection and a real prompt capture.

Repair calls receive the most recent diagnostic, bounded at1800 characters in
the role, but receive **no failed Python source**. `fsm._build_module` passes
only `feedback=` on attempts2/3; the role has no source parameter. It asks to
repair a specific failure without identifying the program that failed. The
same general context limitation was observed in November6's `aes_round` chain.
It remains a candidate mechanism, not measured proof of causation.

Pure probe: `nov7_oracle_prompt_probe.py` captures three actual role prompts
with the model client mocked and performs AST validation only. Its JSON result
shows each retry receives its matching error but neither previous-source
sentinel, and that top-level helper guidance is missing. No generated Python
was executed. The initial probe's `IOExample.outputs` typo was corrected to the
actual `expected` field; no failed model/vendor result is concealed by that fix.

## Smallest justified Phase1

The coordinator chose a prompt-only trial before adding repair-state context:

- Model this module's state and behavior; declared inputs are authoritative
  external values, including neighbor results. Consume them when the contract
  uses them. Do not recompute neighboring functions or invent upstream state.
  Legitimately unused inputs remain allowed.
- Define helpers at module top level and pass state/tables as explicit args.

Only `autortl/prompts.py` and a new instruction/control test are proposed in
`work/nov7-oracle-feedback-stage`. Attempts, metering, sandbox checks, examples,
acceptance and production roles/FSM stay unchanged. This targets the actual
controller-boundary mistake and final sandbox syntax rejection at lower
complexity than anchoring repair on an incorrect complete AES implementation.

The new test verifies the instructions reach the actual retry planner call,
executes handwritten renamed-controller examples through the existing metered
GoldenModel with arbitrary neighbor values, and proves top-level helpers work
while nested helper calls remain rejected. These are instruction/contract
controls, not evidence the LLM will now succeed. A fresh AES trial with the same
metadata budgets is the separate measurement; preserve the completed failed
attempt rather than resuming or regrading it.

## Conditional broader correction

If Phase1 still fails for omitted example semantics or repair amnesia, add
bounded public-contract examples and immediately preceding source+diagnostic.
Do not provide hidden integration tests or qualification reference RTL.

Serialize examples with original indexes, inputs, expected values and
after_cycles. Explain that each example starts from fresh init state and holds
its inputs constant for its cycle count; do not materialize thousands of rows.
Cap total characters and explicitly mark omitted examples instead of silently
cutting JSON. The current public contract's examples are legitimate model input,
but their omission does not justify altering acceptance examples.

For repair, retain the immediately preceding source text, raw failed-file
digest and matching latest error in the module-local loop. Bound rendered source
characters and label truncation and digest scope. Windows CRLF means the raw
file digest can differ from UTF8 text normalized for a prompt; do not label a
normalized-text digest as the recorded failed-file hash. Clearly delimit source
as untrusted program data. Preserve initial-call behavior, exactly three attempts,
provider/storage/timeout propagation, journal replay and budget charges.

Tests should assert example delivery and bounded omissions; distinct neighbor
inputs across renamed modules; exact latest source/error pairing on successive
repairs; no cross-module or fresh-run stale context; no extra model calls on
journal replay; unchanged exhaustion/infrastructure behavior. Existing relevant
suites are test_golden_prompt, test_golden_recovery, test_golden_hardening,
test_golden_reset_protocol, test_spec_dispute and test_role_conformance.

No broader role/FSM patch or sandbox relaxation is implemented in this phase.
