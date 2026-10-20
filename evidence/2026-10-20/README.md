# Verification evidence — 2026-10-20

- harness-tests.txt: full regression suite, 436 passed in 118.53 seconds.
- counter32-reference/: independent cycle reference across all outputs and
  over 880 checked edges, including 800 deterministic random/control cycles.
  Original RTL passes; combinational flags, truncated comparisons, disabled
  overflow clear and asynchronous reset mutants all fail actual assertions.
  No compilation or infrastructure error counts as mutant detection.
- Source/testbench hashes, raw logs, verdicts and archive manifest are retained.

These are supervised verification results. The fresh model-driven tier0
campaign is running separately; no optimization gain or held tier is claimed.
