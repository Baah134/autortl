# Phase 2 independent implementation review

Reviewed staged `autortl/roles.py`, the exact oracle-loop delta in
`autortl/fsm.py` and `tests/test_oracle_context.py` under
`work/nov8-oracle-context-stage`. No canonical edits, new test run, model/vendor
call or board access. This is code/design review; the author owns the pending
clean before/after test receipts.

**Approved: no concrete production blocker found.**

- Public examples contain original indexes, complete input/expected mappings
  and after_cycles. The prose matches actual qualification: each example
  independently calls a fresh init, repeats the same input row and checks the
  final returned output. Scoreboard step is identified as an accepted input
  transaction. Omitted examples remain contract requirements; no qualification
  examples or checks are removed.
- The 8000-character examples budget admits whole serialized records, preserves
  indexes when an earlier large record is skipped, caps inspection at64 and
  reports the total omitted count. The1000-character reserve covers current
  fixed framing/footer under validated specification limits. No partial JSON
  record is presented as complete.
- Source JSON is bounded after escaping through a binary search on prefix
  length, rather than clipping a potentially much larger escaped JSON string.
  It records full text hash, original/shown counts and an explicit truncated
  flag. The raw attempted-file hash is separately named and validated as a
  lowercase64-character digest. Framing describes source as untrusted data,
  and the public contract remains authoritative.
- FSM repair state is local to each module invocation. Only a generated-program
  rejection updates the source/hash/error trio; third generation receives
  second generation's rejection. The digest is the same read_bytes hash written
  into the attempt log. The accompanying text is the original returned source,
  so its separate UTF8 digest can differ from the Windows-written file's raw
  digest. The prompt explicitly distinguishes these identities rather than
  claiming the raw hash covers rendered text.
- Source storage/hash operations and provider calls remain outside the generated
  program rejection catch. GoldenTimeoutError keeps its prior infrastructure
  branch. The original example-only dispute predicate, attempt bound, sandbox,
  budget and supplied-spec authority are unchanged.
- Completed model replies remain journaled and replayed. The loop reconstructs
  failed sources from those replies before qualifying them again; module-local
  state prevents another child/spec invocation inheriting that rejection trio.
  The replay test forbids fresh backend generation and retains normal qualifier
  execution. Runtime-identity rules still prohibit resuming AES02 on changed
  implementation files.

The tests meaningfully cover actual rendered prompt content, complete-record
omission, escaped source bounds, per-attempt raw-file binding, two distinct
rejections, module isolation, journal replay and provider/storage propagation.
On Windows the BAD2 multiline source additionally exercises the distinction
between the returned LF text and write_text's raw CRLF bytes. Top-level helper,
module-local input and timeout behavior remain covered by the preexisting
focused suites; no duplicate full-suite run was performed here.

No hidden reference is supplied: the prompt test deliberately puts a sentinel
into module.golden_model and confirms it is absent. The only source supplied
for repair is the model's own immediately failed artifact. No handwritten AES
diagnostic oracle, integration checker or private reference enters the change.

Limits: this validates context construction and preservation of existing flow.
It does not establish that an LLM will repair the oracle, that a source prefix
is sufficient when truncation occurs, or that a successful future AES trial is
a controlled model-superiority result. A fresh bounded AES03 is the next
behavioral measurement after root's full regression/publication checks.
