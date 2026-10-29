# Model matrix 01: the same tier0 bench on four models

The same harness identity (git 8c5bce9), the same tier0 entries (counter,
mux4) and the same budgets as the tier0 gate (1 iteration, best-of-1, 16
model calls, 20 tool and 30 wall minutes per entry), with every role pinned
to one model through `--model`. Benches ran one after another with
`--jobs 2`. This is an exploratory comparison, not a hold gate: there is no
test receipt. Vivado 2025.2, xc7a35tcpg236-1, 100 MHz, ideal zero I/O delay.

| Model | Tier0 | Counter candidate | Counter verdict as recorded | Verdict with the fixed parser | Tokens in / out (counter) | Wall s |
|---|---|---:|---|---|---:|---:|
| gpt-6-luna | 2/2 | 53 LUT, verified | ACCEPT (55 → 53) | ACCEPT | 115,750 / 1,833 | 580 |
| gpt-5.6-luna | 2/2 | 55 LUT, verified | REJECT (no gain) | REJECT | 112,642 / 4,765 | 431 |
| gpt-6.1-sol | 2/2 | 53 LUT, verified | **REJECT** | **ACCEPT** | 118,100 / 1,951 | 413 |
| gpt-6-astra | 2/2 | 53 LUT, verified | **REJECT** | **ACCEPT** | 116,693 / 1,643 | 378 |

mux4 kept its 8-LUT baseline on every model (no smaller candidate), which
tier0 permits, and every evaluator correctly recommended REJECT there.

## The finding: a formatting difference discarded verified gains

gpt-6.1-sol and gpt-6-astra each produced a 53-LUT counter that passed every
deterministic gate, and each evaluator wrote ACCEPT with every criterion
passing (11 of 11 and 10 of 10). Both put a blank line between
`## Recommendation` and `ACCEPT`. The parser on this identity did not allow
that blank line, read REJECT, and the verified improvement was thrown away.

The independent review of the day's changes had already predicted exactly
this (taxonomy `evaluator_verdict_conflict_or_blank_line`), and the fix was
on a branch when this matrix ran. Re-parsing these eight archived
evaluations with the fixed parser gives ACCEPT for luna, sol and astra on
the counter and REJECT everywhere else, which matches what each evaluator
wrote. So with the fix, three of four models improve the counter and the
fourth honestly finds no gain.

The gates were never at risk: the parser can only add a veto, so the bug
lost improvements; it never let a bad design through.

## Files

`run/<model>/` holds each bench's output (simulator snapshots and Vivado
scratch folders left out) and console; `role-report-<model>.md` summarizes
each role's calls, tokens and verdicts (tools/role_report.py);
`run/run.sh` is the exact script; `archive-manifest.json` hashes every file.
