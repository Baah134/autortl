# Verifier case study review

Proposal: `docs/CASE_STUDY_VERIFIER.md` (570 whitespace-delimited words, including
the table and links). It is reader-facing and includes eight repository-relative
links resolved from the final `docs/` location. No coordinator paths/messages are
in the proposed public document. Root owns canonical integration.

`verify_case_study.py` reads retained data only; it runs no generated Python,
simulator, model, hardware tool or test suite. It checks the document limit,
every link, measured counts, all fault identities, raw assertion/pass framing,
source equality, tool-exit receipts and associated tool-log digests. Result:
`linkcheck-and-source-map.json`. That JSON also pins the proposed document,
linked evidence and historical/current source hashes.

## Claim-to-evidence/source mapping

| Claim in document | Primary evidence read and checked |
|---|---|
| Generated grader originally18/27, nine missed, zero ungraded; reference passed | `evidence/2026-10-26/signed-fir4-generated-audit-01/audit/result.json`: counts, results and control_passed; all28 raw case logs/exits |
| Corrected22/27, five missed; four gained faults | `evidence/2026-10-26/fir4-driver-comparison-01/comparison/result.json`: counts, detected_names, missed_names, audit; actual four-name set difference checked |
| Independent27/27 plus passing reference | `evidence/2026-10-25/signed-fir4-admission-attempt-01/admission/result.json`:28 admitted/executed;27 assertion_proof true faults and passing reference |
| Same reference/fault implementations | Byte hashes of `children.v` for all28 cases match across original generated, corrected generated and independent admission archives |
| Six signed extrema expose12-bit truncation | `fir4-signed-boundary-comparison-01/comparison/result.json`:104→110 payloads; ranges−1703..1539 and−2169..2166; same_golden_reference_mutant; successful old/new reference controls and changed fault verdict |
| Fixed driver scheduling mechanisms | `fir4-driver-comparison-01/stage-review/tbgen.patch` and the exact staged source snapshot; current maintained source `autortl/tbgen.py` linked for navigation, historical patch used for attribution |
| Same oracle and signed-only arrays during scheduling comparison | Actual golden.py bytes match original generated design, signed comparison and driver comparison. Signed-only/corrected stimulus.json bytes match exactly |
| Five legal controls and intentionally faulty producer probe | Corrected comparison's controls/probe; prolonged_block longest_block16/producer_errors0; probe producer_errors9; actual zero tool exits/log digests verified |
| Actual simulator success, not compiler kills |90 case/control/probe sets of retained xvlog/xelab/xsim zero exit receipts and matching raw output digests; detected/missed/reference raw verdict framing checked |
| Five remaining misses and their meaning | corrected missed_names plus named edits in `signed-fir4-admission-attempt-01/fixture/qualification/cases.py`; synchronous reset behavior in its reference.v; typed-policy boundary explained without inventing reset rules |
| Historical1450 regression passes | `evidence/2026-10-26/fir4-coverage-tests-01/result.json` exit0/passed1450/source_unchanged, linked archive README |

The document separates the two interventions: signed payloads change104→110;
the subsequent scheduling comparison keeps those110 payload/expectation arrays
unchanged. It does not claim the original18/27 and final22/27 used identical
traffic. The independent checker is specific to this FIR contract; its27/27 is
not extrapolated to every design. No formal equivalence, new FPGA/PPA result,
current fresh simulation or model-strength gain is claimed.

No canonical files, running test inputs, Git index or FPGA state were modified.
