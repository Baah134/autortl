# Benchmark artifact contracts (schema 1)

`benchmark.artifacts` provides exact-byte input exports and submission seals.
It does not select tasks or candidates, execute an arm, grade Verilog, enforce
an ablation, or establish OS/filesystem/network isolation. No real dataset or
trial is registered by the synthetic tests.

## Frozen manifest

`load_manifest(path, public_root=..., private_root=...)` is a trusted-coordinator
operation only; it must never run inside generation. Generation receives only
the exported public artifact, never the private root or full frozen manifest.
The loader reads UTF-8 JSON without BOM (UTF-16, UTF-32 and UTF-8 BOM fail),
rejects duplicate JSON keys and verifies every explicitly declared public and
private file against its SHA-256. It returns a detached ordinary dictionary.
All listed object keys are required; unknown keys and schema versions fail.

```json
{
  "schema": 1,
  "identity": {
    "dataset": {"commit": "<40 lowercase hex>", "format": "synthetic"},
    "source_commit": "<40 lowercase hex>",
    "runtime": {"commit": "<40 lowercase hex>", "sha256": "<64 lowercase hex>"},
    "requested_model": "fixture-model",
    "observed_model": null
  },
  "tasks": [{
    "id": "fixture_task",
    "public_files": [{"path": "statement.txt", "sha256": "<64 lowercase hex>"}],
    "private_files": [{"path": "official_tb.v", "sha256": "<64 lowercase hex>"}]
  }],
  "cells": [{
    "task": "fixture_task", "trial": 0, "arm": "full",
    "budget": {"model_calls": 3, "tool_seconds": 5.5, "wall_seconds": 10},
    "verification_policy": "full"
  }]
}
```

Placeholder hashes above are explanatory, not valid input. Supported format
labels are `synthetic`, `verilogeval` and `rtllm`; these labels do not prove a
dataset's origin or compatibility. Commits must be full immutable SHA-1 strings;
runtime SHA-256 names the caller's frozen runtime identity, not an executable
automatically discovered by this module. Register and verify that identity in
the later experiment launcher. Requested model is required; absent observed
identity remains `null`, never an invented match.

Tasks and both file lists must be nonempty. Task IDs use ASCII letters, digits,
underscores and hyphens, beginning with a letter or digit; case aliases fail.
Cells must reference a known task and have a unique `(task, trial, arm)` triple.
Trials are nonnegative integers; arms are `single_call`, `ablation`, `full`.
Each cell explicitly records its own budget: positive integer `model_calls`
and finite positive numeric tool/wall seconds representable as finite machine
time (`math.isfinite`); oversized integers outside that range fail with
`ArtifactError`. Booleans are not numbers here.
Policies are `full` and `skip_generated_tb_mutations`. These fields record
declared budgets/policy, not evidence that execution enforced them. This module
requires `single_call` to declare one model call and policy `full`, `full` to
declare policy `full`, and `ablation` to declare `skip_generated_tb_mutations`.
It does not enforce actual dispatch/ablation behavior or reserve cells globally.

## Public input export

`export_public(manifest, public_root=..., destination=...)` validates manifest
shape again and copies only `public_files`, byte-for-byte, to
`files/<task-id>/<declared-path>`. It never reads the private root, copies a
dataset tree, adds an interface adapter or selects task files by discovery.
Call `load_manifest` first to validate both source inventories. Public export
then rechecks public bytes and does not depend on private files remaining
accessible to the generation environment.

The public receipt contains exactly `schema`, `kind="public"`, `id`, `identity`,
`tasks` and `cells`. Its tasks contain only `id` and `files`; each file contains
`path`, `sha256`, `role="public"`. No private path, byte, hash, count or
whole-manifest digest is exported. Identity/cell fields are explicitly public
experiment metadata: callers must not put secrets in model names or public
identity fields. A private neighbor in the public directory is not copied.

## Candidate and missing-output records

```python
from benchmark.artifacts import seal_candidate, record_missing

cell = {"task": "fixture_task", "trial": 0, "arm": "full"}
receipt = seal_candidate(
    manifest, cell, source_root=run_directory, destination=fresh_destination,
    files=[{"path": "child.v", "sha256": child_hash, "role": "rtl"},
           {"path": "top.sv", "sha256": top_hash, "role": "rtl"}],
    top="top", internal_status="rejected", selection_reason="latest_complete",
    termination="budget",
)
# Or, when no complete bundle exists:
missing = record_missing(manifest, cell, destination=another_fresh_destination,
                         termination="model_blocked")
```

The caller supplies the complete ordered RTL list and exact hashes. No glob,
mtime, hidden grader outcome or simulator result is used to select output.
Files are copied under `rtl/` with their relative names and order preserved;
there is no repair, rename or source conversion. Only explicitly declared
`role="rtl"` `.v`/`.sv` files are supported; a declared testbench or executable
dependency is rejected. This does **not** identify testbench behavior concealed
in a file declared as RTL, find undeclared includes/dependencies, or prove that
the design elaborates. The caller owns completeness and selection; later
static checks and an independent restricted grader own semantic/safety checks.

Candidate receipt fields are exactly `schema`, `kind="candidate"`, `id`,
`identity`, `cell`, `files`, `top`, `internal_status`, `selection_reason`,
`termination`. `cell` includes its registered budget and policy. Top uses a
simple ASCII Verilog identifier (escaped identifiers are unsupported). Internal
status is `accepted`, `rejected` or `unverified`; reason is `accepted_incumbent`
or `latest_complete`. The former requires declared internal `accepted` status.
Sealing rejected output preserves it as rejected and does not qualify it.

Terminations are `done`, `budget`, `model_blocked`, `failed`, `interrupted`.
Missing records have exactly `schema`, `kind="missing"`, `id`, `identity`,
`cell`, `reason="no_complete_candidate"`, `termination`; they contain no files
or top. An empty file list is never a completed candidate. These artifacts do
not provide token/cost accounting, an external verdict or a curriculum hold.

## Filesystem, identity and completion

Paths use portable relative slash spelling. Absolute, drive-relative, UNC,
traversing, ADS, Win32 reserved-device/trim aliases, case collisions, duplicate
files and file/directory collisions fail. Existing roots and their ancestors
must be ordinary directories; source components, roots and destination parents
cannot be links or Windows reparse points. Sources must be regular files.
Existing destination directories are never reused or overwritten, including
incomplete failed attempts. The destination's parent must already exist.

Every source is checked before copy and rechecked after all copies; destination
hashes are verified before receipt publication. `receipt.pending` is flushed
and synced, then atomically renamed to `receipt.json` last. Failure preserves
partial files for diagnosis; without a valid final receipt they cannot load as
completed. This is atomic final-record publication, not a crash-durable
transaction across arbitrary filesystems or protection from malicious concurrent
filesystem mutation. Keep source/destination trees under trusted exclusive
ownership; Windows link-race resistance is not an OS security boundary.

`load_artifact(destination, expected_id=trusted_id)` requires a separately
retained expected ID, the strict final receipt, every listed exact file hash
and the file inventory, rejecting links, extra files and traversal errors
(including an unreadable extra subtree). Retain the returned
export/seal ID in trusted experiment/publication storage outside this mutable
artifact; never obtain `expected_id` by trusting the receipt being checked.
Empty directories carry no identity. `id` is SHA-256 of sorted-key compact
ASCII JSON for all receipt fields except `id`; file and task/cell list order is
significant. IDs contain no output directory, timestamps or private manifest
digest. Equivalent receipts at separate destinations therefore have identical
IDs. An ID is an integrity checksum, not a signature: replacing RTL and
recomputing the receipt is rejected against the original external ID, while
replacement of that external trust anchor as well is outside this module's
guarantees. Protect publication/source-freeze records and execution environments.

The no-Vivado test suite covers public/private sentinel separation, two-file
RTL order, missing/changed dependencies, failure before atomic receipt, source
drift, rejected and missing output, malformed manifests and Windows path/reparse
controls. Native symlink privilege failures are explicit skips; the Windows
junction fixture creates link and target under one temporary root and removes
only the junction with nonrecursive `os.rmdir`, preserving its target.

Next integration work remains explicit: capture/select bundles at all FSM
terminations; persist and enforce the mutation-only ablation after positive
control; isolate/qualify the independent grader; account for every attempted
backend call; qualify real tools and denied-access sentinels; then register
disjoint pilot/final tasks. Artifact tests establish none of those outcomes.
