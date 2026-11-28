# AES controller oracle failure: boundary confusion before RTL generation

Read-only diagnosis of `logs/explore-aes-20261107-01` on source commit
`26e18f441195177b99fb712d62e47fce3d57ef9a`. No canonical edits, provider calls,
vendor jobs, hardware-server/JTAG/serial operations or board access occurred in
this review. Generated Python was executed only through the existing
`GoldenModel` restricted worker, never imported or executed directly.

## Actual outcome

The outer launch finished in110.796s, with launcher exit0, child exit1 and
`run_summary.json` status `module_failed`, module `aes_ctrl`. The explore
launcher exit alone is not success evidence. All340 frozen source inputs
remained unchanged. There is no curriculum verdict or new optimization result.

The three attempted controller oracles failed differently:

| Attempt | Source SHA256 | Qualification result |
|---|---|---|
| 1 | d66550208f1c0192be253957bc5254c9a9859e9e3de282f3e67f96ec2efcced4 | Example1 ct/rk mismatch |
| 2 | 6fe3b833c7b1afe80fd82b8fe3c4a19f49665d1fb9fb542eefca392551adcc1a | Setup instruction budget exhausted |
| 3 | 5f96b618f12b0e835dd1d8902b125a1ad28e2ba298b4283d3331192af308fc47 | Unsupported call sub_word |

The first failure was not AES mathematical correctness as the controller's
contract is concerned: the controller must consume its **input** ports
`round_out` and `key_next` at the specified edge. Both are deliberately driven
independent values in the module's examples. The final oracle instead builds
an S-box and recomputes the neighboring AES-round and key-schedule modules.
All three retained sources have **zero direct reads** of either input port.
The first therefore produces different ct/rk values than the independently
driven example requires. This is a genuine wrong oracle correctly rejected by
qualification. It is not an invalid specification that should be relaxed.

Attempt2's unnecessary cryptographic table construction exhausted the existing
setup instruction budget. Increasing the budget would conceal the module
boundary problem. Attempt3 moves helper definitions inside `step`; source
validation rejects `sub_word` before executing it.

## Sandbox/prompt mismatch

`autortl/golden_worker.py:179` recognizes callable helper names only among
top-level `FunctionDef` nodes. `ast.walk` later visits every call and rejects
names not in that set or the builtin allowlist (`:219`). Nested functions can
appear in the allowed AST vocabulary, but their names are not callable under
this policy. `GOLDEN_MODEL` currently says only "Helper functions are allowed,"
without the top-level restriction. Thus this is an unclear instruction about
the supported language, not a reason to expand the sandbox's callable set.

Separately, retry feedback in `fsm.py:818` contains the diagnostic only, and
`Generator.golden_model` appends1800characters at `roles.py:174`; the previous
failed source is not included. All three attempts regenerated a full AES
implementation despite the narrow controller interface. This repeats the
previous AES diagnosis's source-less-repair concern, but a prompt clarification
is the simpler initial correction and should be tested before widening flows.

## Independent restricted-worker probe

Artifacts: `work/nov7-aes-oracle-probe/` and
`work/nov7_aes_oracle_probe.py`. Journal completion records retain all three
sources; their hashes match the original rejection logs. The probe extracts
the sources, counts the two actual input-access syntaxes, and reproduces each
qualification result with `GoldenModel` plus `qualify_against_examples`.
No general Python execution of generated code occurs in the diagnostic process.

A separate handwritten **controller-only** control models the same state
transitions and reads supplied `round_out`/`key_next`, without any AES table or
helper. It passes all three frozen module examples with the existing budgets.
That control is diagnostic evidence only: do not feed it into production
generation or claim the model generated it. It does not prove RTL correctness
or general model improvement.

## Smallest justified permanent correction

1. Teach module boundary semantics in the shared golden prompt: declared inputs
   are independently driven values, including values supplied by neighbors.
   Model this module only; do not replace an input with a recomputation of a
   neighboring module merely because context describes that neighbor.
2. Say helpers must be top-level and must take required state/data as arguments.
   Keep the validator and existing operation/allocation/instruction budgets.
   A more actionable nested-helper diagnostic is optional, not required to
   accept this generated source.
3. Test a synthetic renamed controller with arbitrary neighbor values, plus
   prompt delivery and top-level helper compatibility. Do not impose a blanket
   static requirement to read every input: legitimately unused inputs exist.
4. Freeze that minimal correction and use a fresh bounded experiment. Preserve
   this failure unchanged. Measure model recovery rather than counting the
   handwritten control as a successful generated design.

If the bounded clarification trial still loses useful source context during
repair, add a separate bounded, hash-bound previous-source/error mechanism and
measure it against the current same-budget loop. This diagnosis does not
justify new roles, a provider/model upgrade, reference-code injection, more
attempts, higher sandbox budgets or weakened example expectations.
