# Benchmark artifact foundation: acceptance before implementation

Need: the proposed public comparison cannot reproducibly grade outputs without
an explicit public-only input bundle and an immutable complete RTL bundle sealed
before grading. Existing FSM journals and winner files do not yet export a
complete bundle at every termination. Read-only review:
work/nov8-benchmark-next-review.md. This slice supplies artifact contracts only;
it must not guess candidate selection, execute arms or claim grader isolation.

Implement one small standard-library benchmark/artifacts.py module, package
initializer if needed, meaningful no-Vivado tests, and a short API document.
Versioned strict manifests bind full dataset/source commits, runtime identity,
requested/observed model, finite budgets, public/private file hashes and unique
task/trial/arm cells. Do not register real tasks or download the dataset here.
Export only explicit public files; no private paths, bytes or metadata in that
receipt. Seal only an explicitly supplied complete ordered RTL bundle, with
top, internal status, declared verification policy and selection reason; record
missing output separately. Receipt identity is independent of destination.

Reject invalid/unknown schemas, mutable revisions, malformed hashes, duplicate
cells/files, absolute/traversing paths, links/reparse escapes, source drift,
missing dependencies and overwrite. Write the final completed receipt last and
atomically; partial failure must not load as completed. Exact bytes, never
repair/rename RTL, never recursively copy dataset trees or discover candidates.
Preserve complete rejected output as rejected: sealing is not acceptance.

Tests: real two-file temp bundles, private sentinel beside public input,
byte drift, invalid paths including Windows forms, links where supported,
partial copy before receipt, deterministic identity, rejected-but-complete and
missing output. Preserve skips/limitations. Use no models, vendor tools, hardware
or simulator. Parent independently reviews, integrates only after the frozen
AES04 boundary, runs necessary tests and audits the published milestone.

This is not an end-to-end benchmark or OS/network security boundary. Candidate
selection hooks, mutation-only policy with positive control, independent grader,
actual simulator/isolation controls, per-cell failed-call accounting and
pilot/final registration remain explicit next integration work. Do not label
synthetic artifact tests as a benchmark result or claim superiority.
