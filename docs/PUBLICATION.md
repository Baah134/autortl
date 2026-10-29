# Evidence publication checks

## Development publication taxonomy

| Failure | Meaning | Required correction |
|---|---|---|
| ignored_manifest_artifact | A file exists and matches its archive manifest locally, but a broad Git ignore rule omitted its committed blob. Observed with eleven XSIM .jou journals. | Explicitly permit the archive file type under evidence, preserve the failed audit, and verify every manifest entry against committed Git blob bytes. Keep live run journals ignored. |
| uncopied_manifest_artifact | A manifest hashed a run folder, but the archive copy never received some of the listed files, so neither the working copy nor Git has them. Observed with 609 entries in 21 archives from 2026-10-20 to 2026-10-26: XSIM .pb and .jou files, xsim.dir logs and option files, and, in two seed-binding runs, reports and journals. No commit has ever held them; byte-identical copies remained in the ignored logs/ run folders. | Restore the exact bytes from the run folder the manifest was built from, accepting a file only when its SHA-256 equals the recorded digest. Never edit or regenerate the manifest. Record the restore and the failing audit before it. |
| superseded_state_manifest | An archive carries a manifest copied from the state before a resume, and the resume then advanced the files it names. Observed in seed-binding-live-recovery-01: six state files. | Leave both archives unchanged. Prove the recorded bytes from the predecessor archive that still holds them, in tools/evidence_exceptions.json. |
| unarchived_tested_binary | A manifest records the digest of a binary that was tested but not committed, such as a programmed bitstream. Observed with three Basys 3 bitstreams. | Archive the exact tested file in a new evidence folder with its own manifest. If the bytes are gone, record the loss and its reason explicitly. |
| mixed_eol_tested_source | A source-identity manifest hashed a Windows working copy whose lines mixed CRLF and LF, while Git stores the file normalized. No commit then holds the tested bytes. Observed in 22 claims across 21 source identities and freezes, almost all one file, tests/test_module_latency_gates.py. | Prove the tested bytes by rebuilding them from the committed blob with the recorded line endings restored. |
| uncommitted_tested_source | A source-identity manifest hashed a version of a file that was never committed and is not reconstructable. Observed in 10 claims: 6 recovered from Codex staging or pytest folders, 4 lost. | Keep the manifest. Recover the bytes from any local copy whose digest matches, or record the loss. |
| silent_claim_file | A claim file yields no claims, or holds digests that no claim accounts for, so an emptied or reformatted manifest would pass unchecked. Found by review of the first audit version. | Fail both cases. List a claim file without digests, or a digest that is a measured value rather than a file, with its reason. |

A source-identity manifest records repository files as they were when
something was tested, so later edits are expected. Such a claim passes when
the current file or any committed version of it in the audited revision's
history matches, either as stored or as a Windows `core.autocrlf` checkout.
Each path is checked on its own; the audit does not show that one commit held
all bound versions together.

## Repository-wide audit

`python tools/evidence_audit.py` checks every SHA-256 claim in every claim
file under evidence/ against the committed blobs of HEAD. Claim files are the
manifests and the source-identity records (tested-source manifests, source
freezes, original-source and tested-source-identity lists). `--rev` picks
another revision, and `--worktree` checks an uncommitted archive. CI runs
it with full history on every push.

Run records (journals, state, results, caches, verification reports) are out
of scope. Each report counts their digests under `outside_scope`.

An exception in `tools/evidence_exceptions.json` pins each claim it covers
by container, path, digest and failure status. It must be proven by bytes the
audit can read, or it records a loss with its reason. An exception that no
longer matches fails the audit.

This is a development publication failure, separate from runtime design/tool
triage. A working-copy hash pass alone does not establish a complete published
archive. The original audit failure and affected paths must remain recorded.

## Publication procedure

1. Freeze and validate source, inputs, configuration, tool receipts and measured
   reports. Retain failures and resource/power tradeoffs with successful results.
2. Create the archive manifest from copied bytes and verify every local entry.
3. Inspect ignored files before staging. Vendor .log and .jou files under
   evidence are archived proof; live logs/runs remain ignored.
4. Commit and push the reviewed milestone without force. Verify remote heads.
5. Read every manifest path from the selected commit with git cat-file --batch
   and compare SHA256 of the raw blob with its recorded digest. Missing blobs,
   malformed entries and any mismatch fail publication. Do not delete or
   regenerate a manifest to hide an omission. `python tools/evidence_audit.py
   --worktree` checks a new archive before it is committed, and
   `python tools/evidence_audit.py --rev <commit>` checks the commit.
6. Correct packaging omissions and rerun the complete committed-blob check;
   record the verified commit in the handoff. Documentation/package-only changes
   do not regrade completed FPGA runs or change their frozen runtime identities.

The checked-in publication-check evidence contains the actual failed audit,
missing-path list, before/after ignore rules, path-policy checks and committed-blob audit
helper used to close this observed failure.
