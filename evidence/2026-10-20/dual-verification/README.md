# Combined generated and independent verification

## Observed acceptance gap

The generated103-transaction payload scoreboard passed both the correct two-entry
control and a capacity-one fault. The exact same capacity-one RTL bytes, SHA256
aa1a363cb764ee46972dacfdd97597a16fbad96c6bfc0e04954fb4e23a5243dc, then
failed the independently qualified queue test's capacity/readiness assertions.
This is an actual generated-grader coverage gap, not a successful mutant check.
Raw TBs, DUTs, logs, receipts and both verdicts are retained. The independent case
also compiles the mechanical wrapper; its child RTL hash is exactly unchanged.

## Harness change

`build --generate-golden --tb <independent-top-tb>` runs generated Python/example/
unit-TB verification and an adapted independent TB for a single-child design.
Both checks rerun after each child repair; failing independent diagnostics and
TB text reach the child RTL repair worker. Logs/manifests use separate workdirs.
Both testbenches must independently detect sabotage. The unchanged original top
TB then gates baseline, candidate verification, and source-bound physical reuse.

Legacy --tb alone keeps the trusted-only path. No--tb remains generated-only with
its documented coverage limits. Multi-module builds use generated per-child TBs
and a supplied top integration TB; arbitrary top TBs cannot be renamed into per-
child authorities. The stronger per-child dual check is for a single-child wrapper.
The flag is typed, saved, resume-frozen and included in curriculum cohort identity.
Old schema1 configs default this new field to false; older required fields stay
mandatory. The skid curriculum entry enables combined verification explicitly.

## Tests

- Configuration/CLI/curriculum focused suite:90passed in17.16s.
- Combined flow + existing build/recovery suite:22passed in561.52s. A desktop/tool
  interruption occurred during this run; this duration is not a performance claim.
- Initial flow focus:20passed,2failed in28.15s. Fixtures incorrectly expected no
  bounded infrastructure retries and failed to mock the candidate's one repair.
  Fixed mocks/expectations; production retry/verification gates were unchanged.
  The unmocked worker start failed sandbox access; no useful model response was
  obtained and this is not model-driven design evidence. Complete log retained.
- Full combined-mode regression suite: **774 passed in178.95s** (full-suite-774.txt).
- Live combined streaming build is recorded separately; initial qualification blocked.

Compiled trees/duplicate journal artifacts are omitted. Absolute paths refer to
historical local runs. The helper retains its original local ROOT; adjust it for
another clone. The archive is evidence, not a resumable execution directory.
