# Generated iterative divider attempt01

**38 -> 26 LUTs (31.58% reduction),46 -> 38FFs,setup+0.315ns,hold+0.129ns.**
Final bestiteration3, accepted objective improvement, actual DONE.
Baseline setup/hold+0.324/+0.136ns; both were timing-feasible. Estimated total
power increased0.092->0.103W and dynamic0.022->0.032W. This is an area result,
not a power improvement. Physical metrics apply only to the default8-bit top.

Fresh run fromcfef8af, no qualification reference seed. Original3iterations,
1candidate,16calls,25tool/35wallminutes,1infraretry. Actual11calls,
409.939chargedtoolseconds,560.999elapsedseconds. Vivado2025.2,
xc7a35tcpg236-1,100MHz,idealzero min/max I/O delays, not board constraints.

The first Python oracle used disallowed divmod; bounded repair passed on
attempt2. Both initial graders caught flip==to!=. Iter1 reused work registers
as outputs and won30LUT/39FF,+.315/.110ns,review7/7PASS. Iter2 repeated that
source and was correctly rejected for no gain using cached verified metrics.
Scheduled/stall replan also received a churn signal; it proposed shared
extended subtraction for borrow decision and remainder. Iter3 won26LUT/38FF,
review6/6PASS. Source review confirms eight sequential restoring steps;
blackbox simulation alone is not structural proof.

## Final verification and grader sensitivity

Exact saved winner and declared child passed the independent six-width checker.
It checks arithmetic, exact availability, busy/result boundaries, stalls,
divide-by-zero, reset phases and held-result abort. Actual DONE replay exited0;
temporary child/spec changes were rejected1,restoring251hashes,fileset andbudget
with no new model/tool charges. This is not an in-flight hard-kill guarantee.
MeasuredCRLF and savedLF source differ only line endings; full identity link
and byte-identical independent copy are recorded. Read-only review found no
blocker. Child WIDTH1 includes a negative-range part-select; actual Vivado
tests passed, with no cross-tool portability or all-parameter proof claimed.

Supplemental generated-grader measurement is separate from original admission:
passing control; 13/17 applicable named faults detected; misses: zero_divisor_remainder_zero, ready_on_retirement_edge, asynchronous_reset, reset_preserves_held_result.
Three width-only faults are equivalent at default8 and excluded, not counted
as sensitivity failures. Full raw outcomes/source hashes and elapsed costs are
retained. Independent temporal qualification caught all20faults across selected
widths. No retroactive regrading or runtime change occurred.

Keep complementary graders, deterministic promotion, context-qualified cache
and bounded replanning. One duplicate proposal cost a model call; the replan
then produced a genuinely different useful candidate. Retain this alongside
packet01's repeated replan outcome before claiming a diversity fix. The earlier
failed reset admission and corrected21/21admission remain separately archived.
Full regression1180passed; freshfulltier0 is still required before main merge.
