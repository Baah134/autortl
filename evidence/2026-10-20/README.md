# Verification evidence - 2026-10-20

- `harness-audit-tests.txt`: repaired harness full suite, **468 passed in134.47s**.
- `harness-tests.txt`: checkpoint4091 full suite, 436 passed in118.53s.
- `counter32-reference/`: independent all-output cycle reference, over880
  checked edges and800 deterministic random/control cycles. Original passes;
  four mutants fail actual assertions (flags, highbits, overflow and reset).
- `contract-campaign-01/`: original tier0 cohort0/2 after worker exit1,
  plus separate recovery summaries. Counter resumed only evaluator,7->8 model
  calls and unchanged267.641s physical time; candidate53LUT vsbaseline55 was
  rejected by evaluator due missing timing-report identity in context.
- Mux recovered DONE with8LUT baseline retained. Neither run promoted a candidate.
- `worker-diagnostic.json`: separate minimal worker call succeeded; original
  exit1 causes remain unknown.

Raw reports, source/TB hashes and manifests preserve evidence. Follow-up repair
validation is recorded separately. No held tier or accepted gain is claimed.
