# Repository-wide evidence audit and the gaps it closed

Every result in this repository rests on SHA-256 records under evidence/.
`docs/PUBLICATION.md` requires each manifest entry to be checked against the
committed Git blobs, not the working copy. Until now that was done for seven
named archives. `tools/evidence_audit.py` checks every claim file at any
revision, and CI runs it on every push with full history.

## What is audited, and what is not

**Claim files** are the archive manifests and the source-identity records:
- tested-source manifests
- source freezes taken before test runs
- `original-source*`, `*launch-source-*`, `harness_identity` and
  `latency-runtime-source` lists
- `tested-source-identities`
- the 2026-10-19 relocation record
- the `runtime_source` freeze inside each launch plan (`*prelaunch*.json`)

There are three kinds of claim:

- **Archive entries** must match the committed file exactly.
- **Source bindings** must match the current file, or some committed version
  in the audited revision's own history, either as stored or as a Windows CRLF
  checkout. Each path is checked on its own, so the audit does not prove
  that one commit ever held all the bound versions together.
- **Digests recorded without a path** must match a file inside evidence/.
  The empty-file digest never counts.

The audit fails, unless the case is listed with its reason:
- a claim file that yields no claims
- a digest in a claim file that no claim accounts for
- a claim file that existed anywhere in the revision's history but is now
  deleted or renamed

That way an emptied, reformatted, deleted or renamed manifest cannot pass
silently.

**Not audited:**
- **Run records:** about 51,000 digests in journal entries, run state,
  results, metric caches and verification reports, written by the harness and
  its launch scripts. The harness checks its own journal hashes on resume.
- **About 1,800 digests in launch-plan maps other than `runtime_source`.**
  Their meaning varies by experiment.

Each report counts both under `outside_scope`, so the boundary is always
visible.

## Before: fef63d4

`audit-before.json` (rendered in `audit-before.txt`) audits fef63d4 with
no exceptions. It covers 172 claim files and 27,073 claims and finds **837
failures**.

| Failure | Count | Cause | Resolution |
|---|---:|---|---|
| missing | 609 | The manifests hashed run folders, but the archive copies never received some listed files: XSIM `.pb` and `.jou` files, `xsim.dir` logs and option files, reports. No commit ever held them. | 532 restored, 77 proven from a predecessor archive (below) |
| unbound | 217 | Source identities naming versions that no commit holds exactly. | 20 rebuilt, 27 proven from archived copies, 170 recorded losses |
| mismatch | 6 | `seed-binding-live-recovery-01/run` carries the validation manifest of the quota-blocked run it resumed, and the resume advanced six state files. | Proven from the predecessor |
| digest_not_found | 3 | Board manifests record bitstream digests, but bitstreams lived only in ignored build folders. | 2 archived, 1 lost |
| no_claims | 2 | A list of generated-testbench cases without digests, and a launch plan that has no `runtime_source` freeze. | Each listed with its reason |

While it was being built, the audit also flagged 1,189 bindings and 896 paths
that were really true matches. The bindings were Windows CRLF checkouts. The
paths came from manifests written on Windows, with backslashes or absolute
paths into run folders that were later renamed. The audit now recognizes
both.

## The corrections

**Restored files (532).** For every missing archive entry, `restore_uncopied.py`
found the file under logs/ whose SHA-256 equals the recorded digest, copied
it, and re-hashed the copy. Identical bytes often exist in several runs, so
it takes each manifest's files from the run folder that holds the most of
them at their recorded paths: the run the manifest was built from. All 532
came from their manifest's own run. `restored.json` lists each file and
its source. No manifest was edited or regenerated.

**Bitstreams (8).** The tested bitstreams were still in the board build
folders. They are archived in `../basys3-bitstreams-01`, checked against the
digests the board evidence recorded. The board suite's `--bit` option
programs one from a fresh clone. `../basys3-bitstream-replay-01` reran all
six harness winners on the board that way, and every result reproduced
exactly.

**Exceptions.** `make_exceptions.py` writes `tools/evidence_exceptions.json`.
Every failing claim must match one of its rules, or the script stops. Each
exception lists its claims, pinned by container, path, digest and failure
status:

| Kind | Claims | How the audit proves it |
|---|---:|---|
| superseded_state_manifest | 83 | It reads every recorded byte from `seed-binding-quota-block-01/run`, the run this manifest belongs to. Its 77 missing files are among the 532 restored. |
| uncommitted_tested_source (archived copy) | 27 | Tested versions edited before they were committed. 21 are read from the experiment's own archived `source-snapshot/`. 6 survived in Codex staging and pytest folders and are archived here under `recovered/`. |
| mixed_eol_tested_source | 20 | The tested working copy had one line ending different from the rest of the file. The audit rebuilds the exact bytes from the committed blob with that line restored and checks the digest. |
| uncommitted_tested_source (lost) | 4 | Recorded losses: two curriculum READMEs (three claims) and one test file. No commit, run folder, snapshot or staging folder holds the bytes, and no single line-ending or trailing-newline variant of a committed version reproduces them. |
| working_directory_move_record | 166 | Recorded losses from the 2026-10-19 relocation record: 120 `.git` internals, 41 cache files, 2 ignored logs, and 3 sources whose working-copy versions at the move were never committed. |
| unarchived_tested_binary | 1 | Recorded loss: the superseded v01 UART echo bitstream, overwritten by the v02 build. |

The two claim files without claims and the 8 bitstream payload digests (a
derived value, pinned by exact digest) are listed with reasons. An exception
fails the audit if its claim now passes, changes digest or fails
differently. Listing the same claim twice is an error.

## After: eebedce

`audit-after.json` audits eebedce, the commit that made these corrections,
and it passes. It covers 175 claim files and 27,117 claims:

- 18,279 archive entries match exactly.
- 8,127 bindings match the current file and 385 an earlier committed
  version. 7,501 of these match as Windows CRLF checkouts.
- 25 digests without a path match a file.
- 130 claims are proven exceptions and 171 are recorded losses.

No harness runtime, frozen source, run result or tool output was changed. The
corrections add files that the manifests already described, so no completed
FPGA run is regraded.

## History of this audit

Two independent reviews shaped it:

- **The first version (1d39729, 0957371)** read only files named
  `*manifest*` and matched exceptions by path alone. It reported 798
  failures at fef63d4.
- **The first review** found the source freezes it never read, claim files
  that passed silently, and loose exceptions. f449748 fixed those
  (817 failures).
- **The second review** found the launch-source lists and the
  `runtime_source` freezes, and that deleting a manifest still passed.
  eebedce fixed those (837 failures).

The earlier reports remain in Git history.

## Reproducing

```
python tools/evidence_audit.py --rev fef63d4   # the 837 failures
python tools/evidence_audit.py --rev HEAD      # passes
python -m pytest tools/tests -q                # the audit's own tests
```

Each revision is audited with its own `tools/evidence_exceptions.json`, and
fef63d4 had none.
