# Fresh full tier0 campaign11

**2/2passed, new-cohort streak1, heldfalse.**

| Entry | BaselineLUT | BestLUT | FF | Setupns | Holdns | Calls |
|---|---:|---:|---:|---:|---:|---:|
| counter | 55 | 55 | 37 | 0.494 | 0.113 | 3 |
| mux4 | 8 | 8 | 8 | 0.579 | 0.052 | 4 |

Fresh full merge gate on3d7813defd3bfef7caea2381506bbc9e2ca8065b with1366tests. Both runtime manifests
match the committed source; all211 tested identities remained unchanged.
The mechanical wrapper timescale fix changed runtime identity, so prior cohort streaks
are not carried over. Modelidentity remains unobserved CLIdefault; no weaker-model
or general optimization reliability claim follows.

Vivado2025.2,xc7a35tcpg236-1,100MHz,idealzero min/max I/O. Perentry:
1iteration/1candidate,16calls,20tool/30wallminutes,1infraretry. Mandatory
simulation/tool-exit/routedmetric/timing gates passed. Actual failed/no-gain
proposals remain raw; verified baseline retention is permitted by tier0criteria.
This gate is separate from the26LUT divider measurement on originalcfef8af.
