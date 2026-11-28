# One finite field-guidance experiment — acceptance before implementation

The remaining AES03 failure is a generated arithmetic error, not a context or
qualifier bug. Existing prompt advice recommends a log/antilog table but omits
the prerequisite that its generator span the nonzero field. Independent
polynomial-convolution controls verify that this depends on the modulus:
under0x11b,02has order51/03order255; under0x11d,02has order255.
Do not put these generator constants or a repaired algorithm/table into the
production prompt. NIST field/inverse definitions and independently derived
orders are distinguished in the retained assessment/probe.

Clarify only the existing advice with primitive-generator and complete-coverage
invariants (all nonzero elements;255 for GF(2^8)), plus nonzero inverse products
equal1 using field multiplication. Do not ban an element universally. No code,
lookup table, AES output, new role, configuration, sandbox or budget relaxation.
This is a development change on a known curriculum task, not an untouched test.

Before/after actual-role prompt delivery; independent arithmetic countercontrols;
existing golden/context/recovery focus; independent review; full software suites;
publish/freeze/audit; then AT MOST ONE fresh AES04 with unchanged original
contract, independent TB, current qualifiedCLI/model request and budgets.
Preserve all outcomes. Stop task-specific AES prompt tuning after this declared
trial regardless of outcome; assess limitations and move to release/benchmark
work. Do not automatically launch AES05 or inject a reference to rescue it.
No board operation or hardware result is part of this experiment.
