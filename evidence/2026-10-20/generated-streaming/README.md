# Combined-verification streaming build

Runtime source: **afcc080**. Completed `logs/build-golden-skid-03` using generated
Python/payload verification and the independently qualified temporal testbench.
The design is an eight-bit, two-entry elastic queue with combinational ready.
It does not provide registered-ready timing isolation.

- Verified baseline retained: **15 LUTs / 19 FFs**, setup slack **0.302 ns**,
  hold slack **0.138 ns**, Vivado 2025.2, xc7a35tcpg236-1, 10 ns clock,
  ideal zero minimum/maximum I/O delays. Five model calls; 384.843 charged tool
  seconds; 435.038 elapsed seconds. No area improvement is claimed.
- Generated grader passed its control, missed the readiness fault and detected
  stuck-zero. Independent grader passed its control and detected readiness.
  The reports retain those misses; qualification is a minimum sensitivity check.
- The independent queue control checks 893 cycles, including capacity, ordering,
  full/empty, backpressure, simultaneous transfers and occupied reset. Its
  qualification control plus eight behavioral faults had 9/9 expected verdicts
  in the separate streaming-qualification archive.
- Exact saved winner plus declared child passed the original independent TB
  again in a fresh directory. DONE CLI replay returned the same winner and
  all 42 selected protected file identities, including budgets, remained equal.
- Candidate had no LUT improvement and duplicated a companion module. The model
  judge rejected it. Its compiler warning exposed a deterministic guard gap;
  the later qualification-proof archive demonstrates the exact candidate now
  fails compilation before elaboration. Do not attribute that later fix to afcc080.

Previous attempts are preserved separately: attempt01 blocked on qualification,
attempt02 exhausted its frozen budget during battery sleep. Neither is a
successful physical result. This archive omits compiled simulator trees and
journal artifact copies and is not a directly resumable run directory. Original
absolute paths are provenance, not portable commands.

Reproduce with a fresh output path and your own Vivado arguments:

```powershell
python run.py build --spec curriculum/tier2/skid_buffer_build/design_spec.json --tb curriculum/tier2/skid_buffer_build/skid_buffer_tb.v --generate-golden --top skid_buffer --iterations 1 --best-of-n 1 --max-llm-calls 16 --max-vivado-minutes 20 --max-wall-minutes 30 --max-infra-retries 1 --output-dir runs/streaming @vivadoArgs
python scripts/check_generated_build.py --run runs/streaming --tb curriculum/tier2/skid_buffer_build/skid_buffer_tb.v --output runs/streaming-independent
python run.py resume --run runs/streaming
```

Use source afcc080 to reproduce that historical harness, or current source for
its strengthened compiler/evidence guards. Model answers and physical results
may differ; no repeated or weaker-model performance claim follows.
