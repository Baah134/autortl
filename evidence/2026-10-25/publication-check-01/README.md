# Committed evidence publication gap and permanent correction

The initial ab0269a milestone passed all RTL/runtime gates, but its postpush
Git-blob audit failed: eleven locally present XSIM .jou journals were omitted
by Git ignore rules. All local archive hashes were valid. The original failure,
missing paths and before/after rules are retained; no historical manifest was
deleted or regenerated to conceal the omission.

The permanent rule permits .jou only under evidence, matching the existing .log
exception. Four actual Git checks establish archived journals/logs are included
while live journals/logs remain ignored. Runtime/test/spec/TB bytes and all 220
tested source identities are unchanged; the 1,415 tests, elastic run and full
tier0 gate are not regraded or repeated for this packaging-only correction.

verify_committed_archives.py audits all seven named new archive manifests against
raw committed blobs. ROOT identifies the canonical checkout; adjust that path
when running the audit on another clone. The development publication taxonomy
and permanent procedure are in docs/PUBLICATION.md. A successful audit after
the correction is required before the final publication checkpoint.
