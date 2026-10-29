# Tier0 campaign20: the final identity, run 1

**2/2 passed, streak 1, held false. Model: `gpt-6-luna` (requested).**

| Entry | Baseline LUT | Best LUT | FF | Setup ns | Reg-to-reg ns (advisory) | Calls | Tokens in / out |
|---|---:|---:|---:|---:|---:|---:|---:|
| counter | 55 | 55 | 37 | 0.494 | 1.672 | 3 | 114,265 / 1,591 |
| mux4 | 8 | 8 | 8 | 0.579 | none (no register-to-register path) | 4 | 136,156 / 2,622 |

The first gate on the 249-file identity (7c592d6, freeze `022ab35a…`): the
day's harness changes, the independent review's fixes, the OpenAI-compatible
and user-defined endpoints, and the clone-and-use cleanup. It ran
`tools/tier0_gate.py --model gpt-6-luna --jobs 2` with campaign14's budgets.
The full test receipt passed (1,601 harness tests). Bench 340 s with both
entries in parallel; the source, router-statistics and history prefixes were
unchanged.

- **The new advisory metric works live.** The counter's worst
  register-to-register path has +1.672 ns of slack beside its +0.494 ns
  I/O-limited WNS; mux4 has no register-to-register path, and the guarded
  report correctly wrote nothing.
- **counter:** the candidate stayed at 55 LUTs and the evaluator rejected it
  for no objective gain, as written (`Optimization objective: FAIL`). No
  improvement is claimed for this run.
- **mux4: a new role behavior.** The generator part-selected a concatenation
  directly, `{d, c, b, a}[sel * 8 +: 8]`, which Verilog-2001 does not allow
  (VRFC 10-4982, with no taxonomy hint). The bounded repair fixed it and the
  candidate verified, but it cost a model call. Recorded as
  `generator_selects_from_concatenation`; the generator rule and message
  hints are on `claude/tier2-prep`, to land after the hold series.

`role-report.md` lists each role's calls, tokens and verdicts. `run/` holds
the bench output without simulator snapshots or Vivado scratch folders;
`archive.py` built this folder and `archive-manifest.json` hashes every file.
