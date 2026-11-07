# Parallel release diagnoses — November6

Three scoped subagents reviewed saved AES failures, recurring UART/FIFO failures
and the public benchmark protocol while the334-file signoff input stayed frozen.
These are diagnoses and a proposed protocol, not passing new model experiments.
The UART probe uses independent Python models and saved process/assertion logs;
it does not execute generated code or invoke a simulator. Run it from the
canonical checkout with its original saved logs available. The benchmark has
no selected dataset commit/task roster or executed trials yet.

AES: the gate correctly rejected bad generated oracles; failed-source repair
context is a conditional improvement study if failure recurs. UART: pre-edge
latency0 expectations conflict with post-edge stateful oracles; clarify planner
sampling semantics and use control regressions, without forcing latency values
or weakening the independent testbench. A separate empty-data contract gap is
recorded. Next implementation remains isolated until the live gate completes.
