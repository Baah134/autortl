# Frozen tier0 campaign04

Runtime2318e42. Original cohort **2/2 mandatory gates passed**, first qualifying
cohort, **not a held tier**. Both designs completed with three model calls each;
no checkpoint contention failure recurred. No candidate was promoted.

Counter baseline55LUT/37FF, WNS0.494ns/WHS0.113ns. Candidate53LUT/37FF,
WNS0.456ns/WHS0.282ns passed simulation and routing. Evaluator rejected it
because actual subprocess exit codes were not included in its evidence. This
is a measured candidate, not an accepted autonomous improvement.

Mux baseline8LUT/8FF, WNS0.579ns/WHS0.052ns retained. Candidate8LUT,
WNS0.579ns/WHS0.057ns had no objective gain. Evaluation also exposed a
metadata problem: unannotated source latency defaulted to zero despite its
registered behavior. A later fix must distinguish unknown from declared latency.

Vivado2025.2, xc7a35tcpg236-1,10ns, explicit ideal zero I/O assumptions.
One iteration/candidate,16model calls,12toolminutes,18wallminutes per design.
Actual sources, reports, evaluator decisions, budgets and frozen runtime
manifests are retained. Compiled files and duplicated journal artifact trees
are omitted. New implementations require fresh runs; never regrade this record.
