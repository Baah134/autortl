# Out-of-context port timing, corrected hold exclusion — November 14, 2026

Supersedes the final template in ooc-port-timing-01. Excluding all input hold
(ooc-port-timing-01's final template) removed every hold path of a purely
combinational design, so pilot-05's Prob036_ringer arm B baseline had WHS -999
and was stopped by the metrics gate. The corrected guard excludes only
input-to-register hold, and only when registers exist.

Live, Vivado 2025.2, xc7a35tcpg236-1, 10 ns, out_of_context, VerilogEval
c498220 references renamed TopModule (`final_template.json`):

| Design | Kind | WNS / WHS (ns) | Timing met | Gate |
|---|---|---|---|---|
| Prob036_ringer | combinational | 7.905 / 0.840 | yes | pass |
| Prob031_dff | single register | 7.006 / 1.061 | yes | pass |
| Prob038_count15 | register-to-register | 8.363 / 0.238 | yes | pass (identical to pilot-04) |

All three kinds were rerun together this time; the earlier check had not
rerun the combinational case after the hold exclusion was added.
