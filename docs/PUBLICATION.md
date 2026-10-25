# Evidence publication checks

## Development publication taxonomy

| Failure | Meaning | Required correction |
|---|---|---|
| ignored_manifest_artifact | A file exists and matches its archive manifest locally, but a broad Git ignore rule omitted its committed blob. Observed with eleven XSIM .jou journals. | Explicitly permit the archive file type under evidence, preserve the failed audit, and verify every manifest entry against committed Git blob bytes. Keep live run journals ignored. |

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
   regenerate a manifest to hide an omission.
6. Correct packaging omissions and rerun the complete committed-blob check;
   record the verified commit in the handoff. Documentation/package-only changes
   do not regrade completed FPGA runs or change their frozen runtime identities.

The checked-in publication-check evidence contains the actual failed audit,
missing-path list, before/after ignore rules, path-policy checks and committed-blob audit
helper used to close this observed failure.
