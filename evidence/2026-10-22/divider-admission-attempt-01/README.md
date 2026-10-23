# Divider admission attempt01 — rejected

The supervised divider control passed all six widths. Full Python regression
passed1175tests in188.39seconds; focused integration102passed5.51seconds.
All192 frozen source identities matched at completion and before archiving.

Real qualification produced20/21 expected verdicts: correct control passed,
19faults caused behavioral assertions, but reset_preserves_held_result passed.
No model generation is admitted from this checkpoint.

The independent TB reset a held result with out_ready=1. The mutant ignored
reset while valid, but normal retirement cleared valid on the same edge,
hiding the missing reset flush. reset_result coverage counted the scenario
without distinguishing a stalled result. This is a concrete verification gap,
not infrastructure or a successful mutant detection.

Before correction, retain every original source, raw verdict, hash and test
log here. The planned correction keeps the simultaneous-reset/transfer case
and adds a distinct held-result/out_ready=0 reset abort with mandatory coverage.
The original mutant and behavior contract stay unchanged. Requalification and
full regression are required; this failed run must never be retroactively
promoted. Selected widths are8wrapper+children1,2,4,13,16, not full-domain proof.
