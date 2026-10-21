# FIFO02: sleep interruption and exhausted budget

Source49599b5, matching55 runtime file identities. Full939regressiontests passed
before this trial. Two configured iterations, one candidate,16calls,20toolminutes,
30wallminutes,oneinfraretry. Vivado2025.2,xc7a35tcpg236-1,10ns idealzeroIO.

Oracle syntax was rejected then repaired through the existing bounded retry.
Generated child RTL passed payload and independent six-configuration tests;
both graders qualified. The same readiness mutation was missed by the payload
grader and asserted under the independent matrix. All misses remain recorded.

The PC slept/hibernated while baseline Vivado was active. On return the vendor
receipt recorded status timed_out, drivercode124, actual returncode0. It remains
unsuccessful regardless of report files or process exit0. The harness then
returned budget_exhausted, without optimization, promotion or a saved winner.
Three modelcalls;18741.826 charged toolseconds;18775.798382759094 elapsedseconds.
These include the interrupted interval and are not an active-compute performance
measurement. No budget was refunded/reset and this run will not be resumed.

Windows System event107 at2026-10-21 06:03:31 America/New_York reports resume;
event42 at06:03:23 reports Hibernate from Sleep - Fixed Timeout. Tool execution
continued briefly after wake before its timeout/budget outcome was recorded.
FIFO03 is a separate experiment on the same source, not a continuation of02.

No accepted physical result is claimed. Compiled trees and journal artifact
copies are omitted; original paths are provenance. Not directly resumable.
