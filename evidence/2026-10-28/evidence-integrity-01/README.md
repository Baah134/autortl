# Repository-wide evidence audit and the gaps it closed

Every result in this repository rests on SHA-256 manifests under evidence/.
`docs/PUBLICATION.md` requires each manifest entry to be checked against the
committed Git blobs, not the working copy, but until now that was done for
seven named archives. `tools/evidence_audit.py` now checks every manifest
at any revision, and CI runs it on every push with full history.

## Before: fef63d4

`audit-before.json` (rendered in `audit-before.txt`) is the audit of fef63d4
with no exceptions: 135 manifests, 20,026 claims, **798 failures**.

| Failure | Claims | Cause | Resolution |
|---|---:|---|---|
| missing | 609 | The manifests hashed run folders, but the archive copies never received some listed files: XSIM `.pb` and `.jou` files, `xsim.dir` logs and option files, reports. No commit ever held them. | 532 restored, 77 proven from a predecessor (below) |
| mismatch | 6 | `seed-binding-live-recovery-01/run` carries the validation manifest of the quota-blocked run it resumed. The resume advanced six state files. | Proven from the predecessor |
| digest_not_found | 3 | Board manifests record bitstream digests, but bitstreams lived only in ignored build folders. | 2 archived, 1 lost |
| unbound | 180 | Source-identity manifests name file versions that no commit holds exactly. | 8 rebuilt, 1 recovered, 171 recorded losses |

The audit itself first reported 896 unsafe paths and 1,189 unbound sources.
Those turned out to be manifests written on Windows (backslash separators,
absolute paths of the run folder that was later renamed) and harness sources
hashed as Windows CRLF checkouts. They are true matches, and the audit now
recognizes them, so they do not appear above.

## The corrections

**Restored files (532).** `restore_uncopied.py` took each missing archive
entry, found the file under logs/ whose SHA-256 equals the recorded digest,
copied it, and re-hashed the copy. Every one of the 532 also matched by path
(`logs/<run>/<path>`), not only by bytes. `restored.json` lists each file
and its source. No manifest was edited or regenerated.

**Bitstreams (8).** The tested bitstreams were still in the board build
folders. They are archived in `../basys3-bitstreams-01` with a manifest
that checks each full-file digest against the board evidence. For the six
harness winners it also checks the configuration payload against the
payload that was programmed and tested. The board suite's new `--bit` option
programs and tests an archived bitstream from a fresh clone, no synthesis
needed.

**Exceptions (264 claims).** `tools/evidence_exceptions.json` covers the rest.
Each exception names exact claims, and the audit must prove it from bytes it
can read:

| Kind | Claims | Proof |
|---|---:|---|
| superseded_state_manifest | 83 | Every recorded byte is read from `seed-binding-quota-block-01/run`, whose own manifest it is. Its 77 missing files are among the 532 restored. |
| mixed_eol_tested_source | 8 | The tested working copies mixed CRLF and LF lines; the audit rebuilds the exact bytes from the committed blob with the recorded line endings and checks the digest. |
| uncommitted_tested_source | 1 | A testbench edited before its first commit. An exact copy survived in a Codex pytest staging folder; it is archived under `recovered/` and read from there. |
| uncommitted_tested_source | 4 | Recorded losses: two curriculum READMEs (three claims) and one test file, all edited before their first commit. No commit, run folder or staging folder holds the bytes, and no line-ending or trailing-newline variant of the committed version reproduces them. |
| working_directory_move_record | 167 | Recorded losses: `.git` internals, caches, router statistics and uncommitted edits in the 2026-10-19 relocation record. That record describes the folder at the move; its 149 committed entries are checked normally. |
| unarchived_tested_binary | 1 | Recorded loss: the superseded v01 UART echo bitstream, overwritten by the v02 build. |

An exception for a claim that passes is stale and fails the audit, and a `*`
exception must match its exact count. So the list can neither hide a new
failure nor outlive the one it explains.

## After

`audit-after.json` is the audit of 1d39729, the commit that made these
corrections. It passed: 136 manifests, 20,034 claims, 0 failures. 18,243 archive
entries match exactly. 1,353 source bindings match the current file and 149 a
committed earlier version. 25 digests without a path match a file. 92 claims
are proven exceptions and 172 are recorded losses. The commit adding this
README, the after-audit and this folder's `manifest.json` is audited in CI
like any other.

No harness runtime, frozen source, run result or tool output was changed. The
corrections add files that the manifests already described, so no completed
FPGA run is regraded.

## Reproducing

```
python tools/evidence_audit.py --rev fef63d4   # the 798 failures
python tools/evidence_audit.py --rev HEAD      # passes
python -m pytest tools/tests -q                # the audit's own tests
```

Each revision is audited with its own `tools/evidence_exceptions.json`, so
fef63d4, which had none, reproduces `audit-before.json` exactly.
