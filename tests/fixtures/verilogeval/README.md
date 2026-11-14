VerilogEval-format fixtures for benchmark/verilogeval.py tests.

- `sim_pass.log`, `sim_fail.log`, `compile_syntax.log`: real Icarus Verilog
  12.0 (MSYS2 ucrt64) output from the November14 grader controls on
  NVlabs/verilog-eval c498220d0a52248f8e3fdffe279075215bde2da6, task
  Prob035_count1to10 (reference, `q == 9` mutant, syntax-error candidate).
  Local paths are replaced by `<dataset>/` and `<candidate>/`. The testbench
  output is from the MIT-licensed VerilogEval dataset (NVIDIA).
- `sim_no_summary.log`, `sim_zero_samples.log`: synthetic edge cases.
- `dataset/`: a minimal invented task in spec-to-RTL layout, not upstream.
