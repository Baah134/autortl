"""Replay the archived sampling controls in XSIM; never connects to hardware."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True,
                        help='A new directory, never an earlier run directory')
    parser.add_argument('--vivado-bin', type=Path, required=True,
                        help='Vivado bin directory containing xvlog/xelab/xsim')
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    root = next(p for p in here.parents if (p / 'autortl/vivado.py').is_file())
    sys.path.insert(0, str(root))
    from autortl.config import RunConfig
    from autortl.vivado import xsim_run

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=False)
    cfg = RunConfig(mode='build', **{
        name + '_bin': str(args.vivado_bin.resolve() / (name + ('.bat' if sys.platform == 'win32' else '')))
        for name in ('xvlog', 'xelab', 'xsim')})
    rows = []
    for name, expected in [('combinational0', True), ('clocked1', True), ('clocked0_mismatch', False)]:
        target = out / name
        target.mkdir()
        for filename in ('accumulated_cell.v', 'accumulated_cell_tb.v', 'golden.py', 'stimulus.json'):
            shutil.copyfile(here / 'controls' / name / filename, target / filename)
        passed, error, _ = xsim_run([target / 'accumulated_cell.v'], target / 'accumulated_cell_tb.v',
                                    'accumulated_cell_tb', cfg, target, timeout=180)
        records = [json.loads(line) for line in (target / 'tool_exit_records.log').read_text().splitlines()]
        log = (target / 'sim_log.txt').read_text()
        assertions = [s.strip() for s in re.findall(r'^FAIL index=\d+ signal=total\s*$', log, re.MULTILINE)]
        wanted = [] if expected else ['FAIL index=1 signal=total', 'FAIL index=2 signal=total', 'FAIL index=3 signal=total']
        valid = (passed is expected and len(records) == 3
                 and [r.get('tool') for r in records] == ['xvlog', 'xelab', 'xsim']
                 and all(r.get('status') == 'exited' and r.get('returncode') == 0
                         and r.get('driver_returncode') == 0 for r in records)
                 and assertions == wanted and 'watchdog timeout' not in log
                 and ('TEST PASSED' in log if expected else 'TEST FAILED: 3 errors' in log)
                 and ('TEST FAILED' not in log if expected else 'TEST PASSED' not in log))
        rows.append({'name': name, 'expected_pass': expected, 'observed_pass': passed,
                     'control_met': valid, 'error': error, 'assertions': assertions,
                     'tool_exit_records': records})
        (out / 'replay-results.json').write_text(json.dumps({
            'board_access': False, 'results': rows,
            'driver_sha256': hashlib.sha256((root / 'autortl/vivado.py').read_bytes()).hexdigest()
        }, indent=2) + '\n')
        print(json.dumps({'name': name, 'control_met': valid}), flush=True)
        if not valid:
            return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
