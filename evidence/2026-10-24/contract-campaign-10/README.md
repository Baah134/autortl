# Fresh full tier0 campaign10

**2/2passed, new-cohort streak1, heldfalse.**

| Entry | BaselineLUT | BestLUT | FF | Setupns | Holdns | Calls |
|---|---:|---:|---:|---:|---:|---:|
| counter | 55 | 53 | 37 | 0.456 | 0.282 | 3 |
| mux4 | 8 | 8 | 8 | 0.579 | 0.052 | 3 |

Fresh full merge gate on965251f with1340tests. Both runtime manifests
match the committed source; all203 tested identities remained unchanged.
The planning and dedupe fixes changed runtime identity, so prior cohort streaks
are not carried over. Modelidentity remains unobserved CLIdefault; no weaker-model
or general optimization reliability claim follows.

Vivado2025.2,xc7a35tcpg236-1,100MHz,idealzero min/max I/O. Perentry:
1iteration/1candidate,16calls,20tool/30wallminutes,1infraretry. Mandatory
simulation/tool-exit/routedmetric/timing gates passed. Actual failed/no-gain
proposals remain raw; verified baseline retention is permitted by tier0criteria.
This gate is separate from the26LUT divider measurement on originalcfef8af.
