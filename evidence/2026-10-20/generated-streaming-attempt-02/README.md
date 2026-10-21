# Second combined streaming trial: battery-sleep budget interruption

Generated RTL passed the generated payload TB and independent893-cycle queue TB.
The payload TB's primary readiness mutation passed; this miss remains in its
qualification.json. The next fixed stuck-zero probe produced real assertions.
The independent TB detected the original readiness mutation. Both qualification
reports preserve source/TB/raw-log identities and ordered outcomes.

Windows System events confirm battery-triggered sleep from23:48:54UTC onOct20
through00:57:19UTC onOct21. The frozen tool/wall budgets expired; the run ended
budget_exhausted with no best/physical measurement. Two model calls and4441.221
charged tool seconds include system suspension; they are not CPU-time measures.
No design rejection or gain is claimed. No budgets were reset and the run was not
resumed under modified runtime. The following trial starts fresh on AC power.

Raw sources/TBs, qualification misses/detections, tool receipts, journal metadata,
config/runtime and budgets are retained. Compiled trees and duplicate artifacts
are omitted. The small infrastructure-interruption record reflects queried
Windows power events; it is separate from design verification. Historical paths
refer to local execution, not a portable resume directory.
