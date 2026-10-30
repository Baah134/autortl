# Tier0 campaign22: stopped by host sleep (no verdict)

The third gate on the final 249-file identity (freeze `022ab35a…`). Its full
test receipt passed (1,601 tests) and the bench launched at 16:39 EDT. The
Windows System log then shows the laptop entering sleep (Kernel-Power 42) at
16:44:13 and resuming only at 20:17, with the system clock jumping from
20:44 to 00:17 UTC. The gate process did not survive: it wrote no launch
result, neither entry wrote a run summary, and the bench never reached the
curriculum history, so the tier0 streak on this identity stays at 2.

This is infrastructure (taxonomy `host_standby_stalls_tools`), not a design
or harness result. The third gate is rerun as contract-campaign-23.

Kept here: the freeze, test receipt, prelaunch plan and console.
