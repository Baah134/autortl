# Repository-wide evidence audit and the gaps it closed

Every result in this repository rests on SHA-256 records under evidence/.
`docs/PUBLICATION.md` requires each manifest entry to be checked against the
committed Git blobs, not the working copy. Until now that was done for seven
named archives. `tools/evidence_audit.py` checks every claim file at any
revision, and CI runs it on every push with full history.

## What is audited, and what is not

**Claim files** are the archive manifests and the source-identity records:
tested-source manifests, source freezes taken before test runs,
`original-source*.json`, `tested-source-identities.json` and the 2026-10-19
relocation record. There are three kinds of claim:

- **Archive entries** must match the committed file exactly.
- **Source bindings** must match the current file, or some committed version
  in the audited revision's own history. A Windows CRLF checkout of that
  version also counts. Each path is checked on its own, so the audit does not
  prove that one commit ever held all the bound versions together.
- **Digests recorded without a path** must match a file inside evidence/.
  The empty-file digest never counts as a match.

A claim file that yields no claims fails, unless it is listed with a reason.
So does a digest in a claim file that no claim accounts for. That way an
emptied, reformatted or partly unreadable manifest cannot pass silently.

**Run records** are not audited: journal entries, run state, results,
metric caches and verification reports, which together hold about 58,000
digests. The harness writes them and checks its own journal hashes on resume.
Each report counts them under `outside_scope`, so the boundary is always
visible.

## Before: fef63d4

`audit-before.json` (rendered in `audit-before.txt`) audits fef63d4 with
no exceptions. It covers 150 claim files and 23,194 claims, with **817
failures**.

| Failure | Count | Cause | Resolution |
|---|---:|---|---|
| missing | 609 | The manifests hashed run folders, but the archive copies never received some of the listed files: XSIM `.pb` and `.jou` files, `xsim.dir` logs and option files, reports. No commit ever held them. | 532 restored. 77 proven from a predecessor archive. |
| unbound | 198 | Source identities naming versions that no commit holds exactly. | 22 rebuilt, 6 recovered, 170 recorded losses |
| mismatch | 6 | `seed-binding-live-recovery-01/run` carries the validation manifest of the quota-blocked run it resumed, and the resume advanced six state files. | Proven from the predecessor |
| digest_not_found | 3 | Board manifests record bitstream digests, but the bitstreams lived only in ignored build folders. | 2 archived, 1 lost |
| no_claims | 1 | A list of generated-testbench cases with no digests. | Listed with its reason |

While it was being built, the audit also flagged 1,189 bindings and 896 paths
that are true matches, not failures. The bindings are Windows CRLF checkouts.
The paths come from manifests written on Windows, with backslashes or with
absolute paths into run folders that were later renamed. The audit now
handles both cases.

## The corrections

**Restored files (532).** `restore_uncopied.py` handled every missing archive
entry. It found the file under logs/ whose SHA-256 equals the recorded
digest, copied it, and re-hashed the copy. Identical bytes often exist in
several runs, so it takes each manifest's files from the run folder that
holds the most of them at their recorded paths, which is the run the manifest
was built from. All 532 came from their manifest's own run. `restored.json`
lists each file with its source. No manifest was edited or regenerated.

**Bitstreams (8).** The tested bitstreams were still in the board build
folders. They are archived in `../basys3-bitstreams-01`, and its manifest
checks each one against the digest the board evidence recorded. The board
suite's `--bit` option programs an archived bitstream from a fresh clone.
`../basys3-bitstream-replay-01` reran all six harness winners on the board
that way, and every result reproduced exactly.

**Exceptions.** `tools/evidence_exceptions.json` is written by
`make_exceptions.py`. Every failing claim must match one of its rules, or the
script stops. Each exception lists its claims, pinned by container, path,
digest and failure status:

| Kind | Claims | How the audit proves it |
|---|---:|---|
| superseded_state_manifest | 83 | It reads every recorded byte from `seed-binding-quota-block-01/run`, the run this manifest belongs to. That run's 77 missing files are among the 532 restored. |
| mixed_eol_tested_source | 22 | The tested working copies had one line ending different from the rest of the file. The audit rebuilds the exact bytes from the committed blob with that line ending restored, and checks the digest. |
| uncommitted_tested_source (recovered) | 6 | These versions were edited before their first commit. Exact copies survived in Codex staging and pytest folders; they are archived under `recovered/` and read from there. |
| uncommitted_tested_source (lost) | 4 | Recorded losses: two curriculum READMEs (three claims) and one test file. No commit, run folder or staging folder holds the bytes, and no single line-ending or trailing-newline variant of a committed version reproduces them. |
| working_directory_move_record | 166 | Recorded losses from the 2026-10-19 relocation record: 120 `.git` internals, 41 cache files, 2 ignored logs, and 3 sources whose working-copy versions at the move were never committed. The exception lists all 166 claims. |
| unarchived_tested_binary | 1 | Recorded loss: the superseded v01 UART echo bitstream, overwritten by the v02 build. |

The claim file without claims, and the 8 bitstream payload digests (a derived
value, not a file), are listed with their reasons. An exception whose claim
now passes, changes digest or fails differently stops matching and fails
the audit. Listing the same claim twice is an error.

## After: f449748

`audit-after.json` audits f449748, the commit that made these corrections,
and it passes. It covers 153 claim files and 23,238 claims:

- 18,279 archive entries match exactly.
- 4,392 bindings match the current file and 260 match an earlier committed
  version. 4,076 of these match as Windows CRLF checkouts.
- 25 digests without a path match a file.
- 111 claims are proven exceptions and 171 are recorded losses.

No harness runtime, frozen source, run result or tool output was changed. The
corrections add files that the manifests already described, so no completed
FPGA run is regraded.

## History of this audit

The first version (1d39729 and 0957371) audited only files named
`*manifest*`. At fef63d4 it reported 798 failures, and it matched exceptions
by path alone. Its reports are in Git history at 0957371. An independent
review then found the gaps described above, and this version closes them.

## Reproducing

```
python tools/evidence_audit.py --rev fef63d4   # the 817 failures
python tools/evidence_audit.py --rev HEAD      # passes
python -m pytest tools/tests -q                # the audit's own tests
```

Each revision is audited with its own `tools/evidence_exceptions.json`, and
fef63d4 had none.
