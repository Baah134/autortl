

## November7 — module-local oracle clarification, plan before implementation

The completed AES01 attempt spent3modelcalls and stopped before RTL generation.
Restricted-worker probes reproduce all three failures; each oracle ignored two
provided neighbor-result inputs. A handwritten controller-only diagnostic passes
the same three examples without cryptographic tables. It is not generated-design
success and must not be provided as production reference code.

Phase1: clarify generic module-local behavior and top-level helper syntax in the
shared oracle prompt. Do not require every input to be read statically: unused
ports can be legitimate. Keep the validator, expected outputs, attempts and
instruction/allocation budgets unchanged. Before/after prompt-delivery tests;
renamed-controller controls with independently supplied neighbor values; real
restricted-worker top-level helper compatibility. Full software regression then
one NEW AES02 exploration with the original metadata budgets and frozen inputs.
AES01 remains failed and is never resumed/regraded. No board operation.

Public contract examples and bounded failed-source feedback are independently
identified improvement candidates. Keep their proposal isolated until the simpler
clarification is measured; more context might anchor the wrong whole-AES model.
No new role, framework, model escalation or extra retry is justified.

Research rechecked: Anthropic Building effective agents,2024-12-19,
https://www.anthropic.com/research/building-effective-agents . Its simple-pattern
and explicit-feedback guidance supports this choice; it does not establish that
AutoRTL's proposed clarification improves model success. The fresh run must.
