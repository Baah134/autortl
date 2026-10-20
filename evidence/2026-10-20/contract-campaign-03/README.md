# Fixed-contract tier0 campaign03

Runtime 1243e2e. Original result **1/2**, not a qualifying or held tier.
Counter baseline: 55 LUTs/37 FFs, WNS 0.494 ns, WHS 0.113 ns.
Planner and generator used two calls, without contract negotiation. Candidate
simulation passed, but saving its charged tool budget hit Windows WinError5
while atomically replacing budget.json. The old budget file remained intact;
its last persisted tool total may omit the interrupted charge. No exact
accounting recovery is claimed, and no candidate physical result was promoted.

Mux completed planning, generation, simulation, implementation and evaluation
with three model calls. Candidate used 8 LUTs, matching the baseline, so it was
rejected for promotion and the verified baseline was retained. Final retained
mux: 8 LUTs/8 FFs, WNS 0.579 ns, WHS 0.052 ns.

Both entries used Vivado2025.2, xc7a35tcpg236-1, 10 ns and ideal zero I/O delays;
one iteration/candidate, 16 model calls, 12 tool minutes and 18 wall minutes.
Raw failure, retained reports, source/TB identities, contracts and journals are
preserved. Duplicated journal artifact copies and compiled simulator files are
omitted. Subsequent runtime fixes require a new experiment directory.
