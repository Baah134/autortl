# Verification evidence - 2026-10-20

- `contract-campaign-05/`: **2/2 mandatory gates**, one accepted counter
  improvement55to53LUT (3.6%), FF37, WNS0.456ns/WHS0.282ns; mux8LUT
  baseline retained. Three model calls each; actual DONE replay preserves
  counter budget/summary/winner hashes.203archived files verified. First
  runtime-bound qualifying cohort, not a held tier.
- `process-exit-tests.txt`: **655 passed in207.64seconds**, covering actual
  exit/driver distinction, immutable verification inputs/replay, receipt/log
  integrity, unknown latency and frozen-runtime cohort identity. Runtime file
  identities are in process-exit-runtime.json. Initial648pass/7fixture-failure
  log is retained in process-exit-tests-initial.txt.
- `contract-campaign-04/`: **2/2 mandatory gates passed** at2318e42; no
  candidate promoted. Counter53vs55LUT rejected for omitted process exit proof;
  mux8LUT had no gain. First qualifying cohort, not a held tier.
- `interface-atomic-tests.txt`: **554 tests passed in 148.80 seconds**, including
  structural interface drift and real Windows sharing-lock recovery.
- `signed-interface/`: four actual signed/symbolic controls and mutants matched
  expected verdicts; wrappers, generated TBs and parameter overrides exercised.
- `contract-campaign-03/`: original result **1/2**; mux completed with three
  model calls and baseline retained; counter hit a Windows checkpoint error
  after passing candidate simulation. No counter candidate was promoted.
- `fixed-contract-tests.txt`: fixed contracts/skills checkpoint, **497 tests
  passed in 100.04 seconds**. Initial fixture-only failure is retained separately.
- `harness-tests.txt`: checkpoint 4091a4b, 436 tests passed in 118.53 seconds.
- `harness-audit-tests.txt`: checkpoint 61854c0, 468 tests passed in 134.47 seconds.
- `counter32-reference/`: original passes an independent all-output reference;
  four flag, high-bit, overflow and reset mutants trigger actual assertions.
- `contract-campaign-01/`: original cohort 0/2 after worker exits; separate
  recovery records preserve completed physical work. Neither recovery promoted
  a candidate. Counter measured 53 LUTs versus baseline 55, but was rejected
  because the evaluator context omitted timing report identity.
- `contract-campaign-02/`: original cohort 0/2 at 61854c0. Counter negotiation
  consumed six calls and blocked generation. Mux saved a typed quota failure
  with its verified baseline and spent budget intact.
- `physical-hold-fix/`: supervised installed-tool command check passes routing:
  18 LUTs, 8 FFs, setup slack 0.579 ns, hold slack 0.059 ns. The area cost makes
  this a targeted repair option rather than a universal optimization.
- `fifo-reference/`: six live cases at two depths matched expected results;
  passing controls and explicit data/full-flag mutation failures. Digital
  transaction checks do not establish physical CDC or metastability safety.
- `worker-diagnostic.json`: earlier minimal worker call succeeded; original
  exit-code-1 causes remain unknown.

Raw reports, source/testbench hashes and manifests preserve evidence. All failed
campaigns remain in the record. One bounded accepted counter gain is recorded;
no held tier or weaker-model performance is claimed.
