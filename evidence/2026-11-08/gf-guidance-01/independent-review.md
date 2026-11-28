# Independent review: finite GF guidance V2

**Decision: approved for coordinator integration and complete regression. No concrete blocker remains in the reviewed patch.** This is approval of the bounded instruction correction, not approval of an AES result or a general model-performance claim.

Reviewed on 2026-11-08 by `/root/gf_hint_review`, against the canonical `Downloads/autortl-work` source supplied as `defd87fa49da92c54d65f81ab8ac5a6aebd3d5a8`. The original prompt snapshot matches the current canonical prompt after newline normalization. The reviewed artifact is `work/nov8-gf-guidance-stage/proposal-v2.patch`, with `receipt-v2.json`; the original unversioned artifacts describe V1 and must not be mistaken for V2.

## Exact artifact identity

Independently computed raw-byte SHA256 values match the V2 receipt:

| Artifact | SHA256 |
| --- | --- |
| `proposal-v2.patch` | `afc66a5fa51741d49721deb9b9849ca1221f9e529bc047b50545c39c0eaa2e56` |
| `autortl/prompts.py` | `a1b8fcfd88d10aa344249d8f50a45b6559ffc3f473afa3312f81877b1a25b8c3` |
| `tests/test_golden_field_guidance.py` | `4d727e91004f82cc1b45fef478fb674536c8e8e135e2537780a24556e9ea9858` |

Independently regenerated the two-file unified diff from the original prompt snapshot and final staged source/test text. It matches `proposal-v2.patch` exactly after newline normalization. No runtime implementation, acceptance rule, sandbox limit, role, contract, or design is added by this patch.

## Mathematical and leakage review

The corrected precondition is valid: a single log/antilog power walk for an entire finite field needs a generator of its multiplicative group. Its powers must cover every nonzero element before repeating. The count 255 is explicitly restricted to GF(2^8). An irreducible polynomial defines a field but does not make its residue class of x a primitive element. Every computed inverse of a nonzero element must multiply to the field identity.

The assessment and trusted arithmetic probe correctly distinguish these cases: under modulus 0x11b, 0x02 has order 51 while 0x03 has order 255; under modulus 0x11d, 0x02 has order 255. The alternate-modulus control rules out a blanket ban on 0x02. The test's all-element coverage and inverse-product checks are stronger than checking a convenient element such as one.

The public [NIST FIPS 197, sections 4.2 and 4.4](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.197-upd1.pdf) defines polynomial field multiplication and the inverse identity. The numeric generator orders above are separately derived by the small trusted probe; they are not attributed to NIST as stated results. The probe and tests share the explicit polynomial multiplication definition, so this is not evidence of two independently implemented multiplication oracles.

Production wording supplies mathematical requirements only. It does not select a numeric generator, provide implementation code, copy a reference function, inject an AES lookup table or output, or require one strategy when another valid strategy is used. Numeric generator choices remain in trusted tests and engineering evidence. Existing behavior anchors stay the contract's anchors.

## Evidence reviewed

Read the final patch, staged test source, V2 receipt, and raw test logs. The two parametrized delivery cases exercise the actual `Generator.golden_model` path for initial and repair prompts, with a renamed generic module. Six deterministic arithmetic cases cover short/full walks, two field choices, complete inverse products, and the deficient-table negative control.

- V1 baseline: **2 failed, 6 passed**; both failures are the missing initial/repair prompt instruction assertions.
- V1 focused suites: **112 passed** in 88.50 seconds. This is retained historical evidence for V1, not a full V2 result.
- Final V2 affected suite: **8 passed** in 0.92 seconds, confirmed from `v2-tests.txt`.
- The V2 receipt reports empty canonical runtime drift, zero model/vendor calls, and no board access.

I did not rerun a test suite, execute generated code, invoke a model or vendor tool, access the board, or edit canonical source. Review actions were source/log reads, deterministic hash/diff calculation, and this scratch review file. Complete software regression remains the coordinator's next validation gate.

## Experiment boundary

This is curriculum-adapted guidance prompted by an observed AES03 failure. It establishes correct instruction delivery and deterministic arithmetic controls, not improved LLM success, a held-out benchmark score, causal attribution, or hardware success. After the coordinator records the taxonomy, integrates, validates, publishes and freezes the accepted source, at most one declared fresh AES04 may use the unchanged contract, qualifiers, three-attempt limits and budgets. Retain all prior and new outcomes. Stop task-specific tuning after that experiment; this approval does not authorize AES05 or an expanding sequence of AES repairs.
