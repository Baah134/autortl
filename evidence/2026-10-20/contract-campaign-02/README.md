# Frozen tier0 campaign02

Runtime 61854c0; same two independent designs and explicit 10 ns/ideal zero I/O
constraints, Vivado 2025.2/xc7a35tcpg236-1, 1 iteration/1 candidate, 16 model calls,
12 tool minutes/18 wall minutes budgets per design.

Original result 0/2; no tier held. Counter baseline: 55 LUTs/37 FFs, WNS 0.494 ns/WHS 0.113 ns.
Six model calls spent on contract proposal/review/refinement; three reviews
still rejected wording of existing mandatory checks. No candidate generated.
Mux baseline: 8 LUTs/8 FFs, WNS 0.579 ns/WHS 0.052 ns. First planner call returned a typed
CODEX_QUOTA failure. model_blocked summary retained best_iteration 0,
redacted bounded diagnostics and exact budget. No RTL rejection or repair.

This reproduces the contract-negotiation overhead and validates live quota
classification/checkpointing. Both original failures remain in the denominator.
Subsequent fixes/runs must use a new directory and immutable runtime identity.
Duplicated journal/artifacts copies and compiled simulator files are omitted;
actual retained source/reports/context and journal result records are archived.
