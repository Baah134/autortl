# Fresh full tier 0 campaign07

**2/2 passed; qualification streak 1; no held tier.** Counter improved; mux
baseline retained. All 175 tested source/test/fixture hashes remained unchanged.

| Design | Result | LUTs | FFs | Setup slack (ns) | Hold slack (ns) |
|---|---|---:|---:|---:|---:|
| Counter |Accepted objective improvement|55→31 (-43.64%)|37|0.126|0.026|
| Mux |Verified baseline retained|8|8|0.579|0.052|

The counter baseline setup/hold margins were 0.494/0.113 ns: area improved and
timing margins decreased while remaining positive. Final review: 8/8 PASS.
Actual counter DONE replay retained 80 protected hashes, file set and budget,
without new model or tool charges. Mux candidate had no strict LUT reduction
and was rejected; a correct no-gain outcome is retained.

Source 6f3fa7c; runtime identical to 85e4fb8 (1,074 tests). Both 55-file runtime
manifests match the published source; common Python/tool identity and unchanged
governance code qualify this fresh cohort. Model identity remains unobserved.
Older runtime cohorts are not counted toward this streak.

Vivado 2025.2; xc7a35tcpg236-1; 100 MHz with ideal zero min/max I/O delays.
Per entry: 1 iteration/1 candidate, 16 calls, 20 tool/30 wall minutes, 1 infra retry.
Actual costs and original budgets are in each case budget.json and
source-verification.json. No budget reset or test/constraint change occurred.

The initial launcher lacked PyYAML on its import path and failed before any
model/vendor call or entry creation. Its console is retained separately. The
successful run uses the existing dependency directory declared in requirements;
there was no code hotfix or package installation.

Raw text artifacts are copied unmodified; compiled trees/journal artifact
copies are omitted. Original absolute paths are provenance, not portable
resume instructions. Source verification links measured and saved raw hashes;
their complete text agrees after only CRLF-to-LF conversion.
