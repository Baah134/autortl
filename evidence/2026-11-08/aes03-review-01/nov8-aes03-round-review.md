# AES03 round-oracle review — November 8

Read-only review of completed `logs/explore-aes-20261108-03` on the published
context repair. No canonical edit, new model call, vendor job, programming,
hardware server, JTAG or serial operation by this worker. The analysis below
does not execute any generated Python program. Small independent arithmetic
checks only transcribe the saved power-table recurrence.

## Actual outcome

The controller's first oracle qualified with SHA256
`31bcce019523f4b0528095f9ebb4ccb7c41415e03eb16e1ce0239d3346928ef2`.
Its scope remains specification examples/generated stimulus; this is not proof
of the complete AES design. The run then exhausted all three permitted
`aes_round` oracle attempts, before any round RTL was generated:

| Attempt | Recorded source SHA256 | Actual rejection |
|---|---|---|
| 1 | `0c575b130f50cae719d027cd7073a9580eafc3088213c4229989f7b04c13fff6` | Setup instruction budget exhausted |
| 2 | `13fd19a279e2687b7fb9f7f61ebecfb2c1a95cfadb660fe1eb3a33e888a942b0` | Setup instruction budget exhausted |
| 3 | `cc84f7fddd41a80a9cf89b0ea1a83dd48fdc3b0fcbb02dda62aa5a905a47336c` | Both public round examples mismatch |

The entry summary is `module_failed`, module `aes_round`. The child failed;
outer launcher0 does not mean success. Recorded duration119.704s, five model
calls, 32.9543 vendor seconds, no source drift or board access, and no curriculum
verdict. The budget record reports58,802 input /26,752 cached-input /3,527 output
tokens and zero calls without token usage. These are one-run observations.

## Repair context was present and correctly bound

The journal retains the actual role-call arguments. For attempts2 and3:

- `previous_source` equals the immediately preceding same-module completed
  model result, character for character.
- `previous_source_sha256` equals that preceding attempt's raw-file receipt.
- `feedback` equals that preceding attempt's actual rejection diagnostic.
- Re-rendering with the run-matching role implementation produces complete,
  **untruncated** previous-source JSON (2,806 and2,786 characters).

All three journaled source texts reproduce their recorded raw digests with the
Windows CRLF file encoding. Raw-file and provided UTF8 text identities are
separate as intended. Both public round examples render in full; zero are
omitted under the example context bound. Current role/FSM/worker files match the
run's runtime hashes for this reconstruction.

This establishes correct harness-side argument construction and bounded
context formatting. The original CLI stdin/server receipt is not retained, so
it does not independently prove remote receipt or model attention. There is no
evidence of missing/truncated context in the application path inspected here.

## Attempts1/2: generated-program resource failures

Attempt1 builds the S-box by trying inverse candidates1..255 for every nonzero
byte and running an eight-iteration field multiplication for each candidate.
This is expensive repeated work during init. The actual metered setup rejects
it. No evidence indicates that this rejection came from an OS timeout or tool
infrastructure problem.

Attempt2 changes to `gf_power(value,254)` with square-and-multiply and an
eight-iteration `gf_multiply` helper. It is a genuine attempted repair of the
previous expensive construction, but this particular implementation still
exceeds the unchanged2,000,000-event setup meter. This does not establish that
every square-and-multiply implementation must fail, or that a larger budget
is justified. The setup limit and worker implementation match the frozen run.

## Attempt3: concrete mathematical error

The third program replaces expensive inverse computation with log/power tables.
Its recurrence starts at1 and repeatedly left-shifts, reducing with283 when
bit8 is set. The independent check of exactly that recurrence visits only
**51 distinct nonzero values**, returning to1 at index51. Repeating it for255
iterations therefore leaves **204 nonzero-byte log entries unfilled**.

The program then looks up every nonzero byte using those incomplete logs. The
public behavior itself states `S(00)=63`, `S(01)=7c`, `S(53)=ed`. Transcribing
only the saved recurrence and affine expression gives:

| Public input | Contract S-box value | Saved recurrence gives |
|---|---|---|
| `00` | `63` | `63` |
| `01` | `7c` | `7c` |
| `53` | `ed` | **`7c`** |

Thus the source violates a value already present in its supplied public
contract, independently of hidden grading data. Its ShiftRows indexing,
MixColumns coefficient expressions and byte packing match the written contract
on inspection; the incomplete S-box is sufficient to invalidate this oracle.
No corrected AES implementation or replacement generator is supplied here.

## Keep/revise assessment

Keep the public-example and matched-source context mechanism: this run confirms
that it supplies the intended data and identities without truncation. Keep the
three-attempt ceiling, setup/step meters and rejection gates: they correctly
prevented acceptance of expensive or mathematically wrong programs. Do not
relax them, inject a corrected AES algorithm or add a new agent role merely to
convert this failure into a headline success.

The controller's first-attempt progress is encouraging execution evidence, not
a causal/general success-rate claim from a single adaptive trial. The remaining
round failures are generated-program resource and mathematical failures, not an
observed context-pairing or qualifier bug. If pursuing another change, first
declare a separate general need/controlled test; avoid an AES-specific answer
patch. The complete AES system, routed timing and new hardware behavior remain
unproven in this attempt.

Reproducible local analysis: `work/nov8_aes03_round_probe.py`; sanitized results
and extracted source copies are under `work/nov8-aes03-round-probe/`. The script
only parses JSON/AST literals, verifies hashes, formats existing role context
and performs the independent small recurrence calculation. It invokes no model,
simulator or generated oracle. Canonical artifacts remain unchanged.
