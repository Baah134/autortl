#!/bin/bash
# Tier0 bench per model, same identity and budgets as the tier0 gate, no test receipt.
cd /c/Users/prince.baah/Downloads/autortl-work
export PYTHONPATH="C:/Users/prince.baah/Documents/Codex/2026-10-15/hey/work/review_deps"
export AUTORTL_CODEX_BIN="C:/Users/prince.baah/AppData/Local/OpenAI/Codex/bin/2993767bd1dfb009/codex.exe"
PY=/c/Users/prince.baah/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe
V=C:/AMDDesignTools/2025.2/Vivado/bin
git rev-parse HEAD > logs/model-matrix-01/git_commit.txt
for m in gpt-6-luna gpt-5.6-luna gpt-6.1-sol gpt-6-astra; do
  start=$(date +%s)
  "$PY" run.py bench --tier 0 --iterations 1 --best-of-n 1 --max-llm-calls 16 --max-vivado-minutes 20 \
    --max-wall-minutes 30 --max-infra-retries 1 --target-part xc7a35tcpg236-1 --target-freq-mhz 100 \
    --model "$m" --jobs 2 --output-dir "logs/model-matrix-01/$m" \
    --vivado $V/vivado.bat --xvlog $V/xvlog.bat --xelab $V/xelab.bat --xsim $V/xsim.bat > "logs/model-matrix-01/$m.console.txt" 2>&1
  echo "$m exit=$? seconds=$(( $(date +%s) - start ))" >> logs/model-matrix-01/summary.txt
done
