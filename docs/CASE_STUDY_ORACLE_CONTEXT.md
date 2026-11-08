# What changed when oracle generation received its contract and failed source

Three fresh AES-128 explorations exposed a module-boundary problem and then a
separate mathematical failure. All requested gpt-6-luna; actual served model
identity and price were unobserved. These are adaptive engineering trials,
not a controlled success-rate comparison or public benchmark.

| Trial | Source | CLI | Model calls | Controller | Final outcome |
|---|---|---|---:|---|---|
| AES01 |26e18f4|0.166|3|Three rejected oracles|module_failed|
| AES02 |df056cc|0.167|3|Three rejected oracles|module_failed|
| AES03 |defd87f|0.167|5|Oracle first try; RTL/unit simulation and mutation qualification passed|aes_round oracle failed|

The controller contract consumes round_out/key_next inputs supplied by
neighboring modules. The earlier references recomputed those neighbors instead.
A general prompt clarification alone did not resolve the observed next trial;
the CLI also changed, preventing attribution to that prompt change alone.

The next correction supplies bounded public IO examples, with each example
starting fresh and holding inputs for its declared step count. Repairs receive
the immediately preceding same-module source, raw-file digest and diagnostic.
Rendered text has its own hash and explicit truncation; examples are omitted
whole with counts. Three attempts, sandbox meters and acceptance checks stay
unchanged. The implementation passed104 focused checks and2087 harness plus
323 tooling tests; one native Windows symlink-privilege test skipped.

AES03's controller now reads both supplied neighbor values, without S-box or
key-schedule recomputation. Its saved source matches the first qualified hash.
The generated RTL and positive control report TEST PASSED; a comparator mutant
compiled and ran with zero process exits, producing103 data assertions. This is
finite module-level evidence. The controller succeeded first try, so its result
does not exercise or establish benefit from the previous-source repair path.

The round stage does exercise that path: both repairs receive exactly the
previous source, matching raw hash and error, with no source truncation. Both
public examples are present. Two references exceed the setup meter. The third
runs but generates a GF table with only51 distinct nonzero elements instead of
255; its S-box gives7c at53 where the public contract states ed. The verifier
rejects the resulting round outputs. No integration, routed PPA, new hold or
physical-board success follows from this run. All342 frozen inputs stayed
unchanged. The run used5 model calls and32.954 seconds of vendor tooling.

## Feature decision

Keep typed contracts, public examples, bounded matching-source context, replay
and failure classification. Keep the qualification gates and original budgets:
they stopped wrong/expensive references before an invalid design advanced.
Keep the restricted worker profile and requalify executable updates, as was
done for CLI0.167. Do not add roles, frameworks or extra attempts to manufacture
a success. Context delivery is now verified; the remaining observed problem
is generated arithmetic, not a demonstrated context-binding/qualifier bug.

Any further domain guidance needs a separate narrow need and finite test.
These results do not demonstrate general improvement over a single LLM call.
Historical board-verified AES results remain their own earlier evidence;
these new failed trials do not regrade them. No board commands were issued.

Evidence: ../evidence/2026-11-08/explore-aes-20261108-03 and
../evidence/2026-11-08/aes03-review-01. All prior failed trials remain retained.
