# Generated golden verification repairs

This archive preserves a real failed build, independent testbench qualification,
and a real zero-cycle scoreboard false positive before and after its repair.

- Counter build01 failed with missing rst in generated oracle inputs (one call).
- Counter/encoder independent testbenches: ten actual expected verdicts, two
  controls pass and eight compiling behavioral faults trigger assertions.
- Scoreboard before: registered control AND forbidden zero-cycle design pass.
- Scoreboard after: registered control passes; identical zero-cycle DUT fails
  eight minimum-transfer-age assertions under a latency1 contract.
- Fullsuite01: 725passed,3failed (legacy unmocked model fixtures). Raw output is
  retained. Fixtures were corrected; focused recovery60tests pass. Corrected full suite:743passed in203.40s (full-suite-743.txt). The separate focused-initial summary is not complete raw output.

runtime-source-before-serial-bound retains the exact 53 frozen implementation
files used by fresh counter build02 and fullsuite02. They are an intermediate
source version; later serial-latency drain-budget validation is a separate change.
Each live run preserves raw sources/TB, logs and process receipts. Archive subsets
omit compiled simulator trees and duplicated journal artifact trees; machine-local
paths may reference omitted originals. This is evidence, not a resumable run folder.

Reproduce counter/encoder qualification with scripts/check_build_tbs.py; use a fresh
output folder and explicit Vivado bin directory. check_scoreboard_latency.py retains
the investigation helper and its original machine-local repo path (adjust ROOT in a
new clone). The before TB is intentionally faulty historical evidence. Run current
code to reproduce the repaired behavior, not to recreate the old defect accidentally.

No formal equivalence, weak-model, held-tier or PPA gain claim follows from these
simulation repairs. Build02 results and streaming qualification are recorded separately.
