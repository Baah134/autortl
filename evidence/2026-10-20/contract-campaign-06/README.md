# Fresh full tier0 campaign06

**2/2 passed; one accepted improvement; streak1; held=false.**
Tested runtime source **8098466**, with **807 passing regression tests**.
Both tasks retained the same 53-file runtime identity throughout execution.
The cohort also binds task/config/tool/Python and governance identities.
Actual CLI model identity is unobserved; this is not a model-strength comparison.

| Default design | Baseline LUTs | Winner LUTs | FFs | Setup slack | Hold slack |
|---|---:|---:|---:|---:|---:|
| 32-bit counter | 55 | **31 (43.64% lower)** | 37 | 0.126 ns | 0.026 ns |
| 4-way mux | 8 | 8 (baseline retained) | 8 | 0.579 ns | 0.052 ns |

Counter baseline setup/hold slack was0.494/0.113ns: area improved and timing
margins decreased, remaining positive. Its independent frozen test covers reset,
load priority, disabled cycles, thresholds, high bits, wrap and800 seeded random
cycles. Candidate uses the increment carry for overflow; all9 evaluator checks
passed alongside mandatory deterministic gates and actual successful exits.
Three model calls;443.859chargedtoolseconds;469.442elapsedseconds. Actual DONE
CLI replay preserved76selected protected identities, including budget and winner,
with no new model/tool calls. This is not in-flight hard-kill validation.

Mux candidate retained8LUT and was correctly rejected for no objective gain.
Three model calls;427.438chargedtoolseconds;450.888elapsedseconds. Baseline wins.

Vivado2025.2,xc7a35tcpg236-1,10ns clock; explicit ideal zero minimum/maximum I/O
delays. These are experiment constraints, not board timing requirements. One
iteration/candidate per design;16calls,20toolminutes,30wallminutes,1infra retry.
No all-parameter/formal/X-Z equivalence or held tier claim. Earlier cohorts and
failures remain separate; three matching qualifying full runs are needed to hold.

Reproduce using a fresh output directory and installed Vivado arguments:

```powershell
python -m pytest tests/ -q
python run.py bench --tier 0 --iterations 1 --best-of-n 1 --max-llm-calls 16 --max-vivado-minutes 20 --max-wall-minutes 30 --max-infra-retries 1 --output-dir runs/tier0 @vivadoArgs
```

The first local CLI launch omitted the existing dependency PYTHONPATH and stopped
at import before creating a campaign. Its traceback is retained separately;
correcting the environment started the measured cohort without source changes.
Files are archived below contract-campaign-06/tier0_rcn3ui26. Compiled vendor trees
and journal artifact copies are omitted. Original absolute paths preserve
provenance; this is an evidence archive, not a resumable experiment directory.
