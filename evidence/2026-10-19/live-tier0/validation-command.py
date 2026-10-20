"""Supervised regression replay; no model calls and no autonomy claim."""
import hashlib
import json
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
from autortl import vivado
from autortl.config import RunConfig
from autortl.fsm import Orchestrator
from autortl.metrics_gate import validate
from autortl.roles import generated_rtl

output = root / 'logs' / (sys.argv[2] if len(sys.argv) > 2 else 'live_repairs_01')
output.mkdir(parents=True, exist_ok=True)
bins = Path('C:/AMDDesignTools/2025.2/Vivado/bin')
tools = {name + '_bin': str(bins / (name + '.bat')) for name in ('vivado', 'xvlog', 'xelab', 'xsim')}
cfg = RunConfig(mode='optimize', top_module='mux4',
    design_path=root / 'curriculum/tier0/mux4/mux4.v',
    testbench_path=root / 'curriculum/tier0/mux4/mux4_tb.v',
    max_llm_calls=0, max_vivado_minutes=8, max_wall_minutes=9,
    max_infra_retries=0, **tools)
results = {'kind': 'supervised_regression_replay', 'model_calls': 0}
def save():
    (output / 'results.json').write_text(json.dumps(results, indent=2))

counter = output / 'counter'
counter.mkdir(exist_ok=True)
raw = root / 'logs/curriculum/tier0_t2_rkf80/counter/iter_001/cand_standard/counter.v'
source = counter / 'counter.v'
source.write_text(generated_rtl('```verilog\n' + raw.read_text() + '\n```'))
tb = root / 'curriculum/tier0/counter/counter_tb.v'
passed, error, kind = vivado.xsim_run([source], tb, 'counter_tb', cfg, counter, timeout=120)
results['counter_timescale'] = {'passed': passed, 'error': error, 'failure_kind': kind.value,
    'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'tb_sha256': hashlib.sha256(tb.read_bytes()).hexdigest()}
save()
print('counter timescale replay:', passed, error, flush=True)
if not passed: raise SystemExit(1)

o = Orchestrator(cfg, output / 'mux4')
o._prepare_inputs()
o._journal_enabled = True
o._scope = 'supervised_baseline'
metrics = o._full_flow([cfg.design_path], cfg.testbench_path, 'mux4', o.state.run_dir)
results['mux4_io_timing'] = {'metrics': metrics.to_dict(),
    'source_sha256': hashlib.sha256(cfg.design_path.read_bytes()).hexdigest(),
    'tb_sha256': hashlib.sha256(cfg.testbench_path.read_bytes()).hexdigest()}
save()
validate(metrics, synthesis_ran=True)
if not metrics.sim_passed or metrics.synth_error or metrics.timing_met is not True:
    raise SystemExit('mux4 verification/timing did not pass')
results['passed'] = True
save()
print(json.dumps(results, indent=2), flush=True)
