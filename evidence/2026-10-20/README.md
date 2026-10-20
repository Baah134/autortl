# Verification evidence - 2026-10-20

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
campaigns remain in the record. No held tier or accepted gain is claimed here.
