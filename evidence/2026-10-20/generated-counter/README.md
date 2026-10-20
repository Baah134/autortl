# Generated counter build

Fresh typed counter8 build, deliberately without --tb, completed its generated
Python oracle, example checks, generated module TB, injected-fault qualification,
mechanical top integration, synthesis/routing and one optimization iteration.
The exact saved winner plus declared child then passed the independently qualified
700-cycle counter TB (wrap, enable hold, reset priority and pre-edge stability).

- First Python reference had invalid syntax. Its retained source and failure hash
  are in the stage journal/golden_attempt_1.log; actual diagnostic repair produced
  a qualified second reference. No manual RTL seed or oracle answer was supplied.
- Baseline retained:6LUTs,8FFs,setup0.424ns,hold0.226ns. Candidate also6LUTs,
  correctly rejected for no objective gain. No optimization improvement claimed.
- Six model calls,300.515chargedtoolseconds. Vivado2025.2,xc7a35tcpg236-1,
  10ns,explicit ideal zero minimum/maximum I/O constraints. CLI model unspecified.
- Runtime is the intermediate reset/minimum-latency source retained in
  ../golden-verification/runtime-source-before-serial-bound; compare runtime.json.
  Later general serial-latency drain-bound changes do not retroactively change
  this run's identity. Source bytes were frozen throughout this completed build.

Raw process receipts, exact RTL/TB, generated Python/stimuli, routed reports,
review decisions, budgets, manifests and journal metadata are retained. Compiled
artifacts/duplicated journal artifact trees are omitted. Absolute local paths
are historical references; this archive is not a resumable execution directory.
No held tier, weak-model reliability or formal equivalence claim follows.

Reproduce with python run.py build --spec curriculum/tier1/counter8_build/design_spec.json
--top counter8 --iterations 1 --best-of-n 1 and explicit bins/budgets (see config.json). Then run scripts/check_generated_build.py with that run
and curriculum/tier1/counter8_build/counter8_tb.v in a fresh output directory.
