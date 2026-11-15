"""Tool-qualification control: official references of the final tasks through the harness synthesis flow.

usage: python synth_sweep.py <repo> <dataset_dir> <selection.json> <out_dir> <vivado.bat> [workers]
No model output is involved. Each reference (RefModule renamed TopModule) is synthesized
out of context with autortl.vivado.run_synthesis and checked by the unchanged metrics gate.
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

repo, dataset, selection, out, vivado_bin = sys.argv[1:6]
workers = int(sys.argv[6]) if len(sys.argv) > 6 else 3
sys.path.insert(0, repo)
from autortl import vivado  # noqa: E402
from autortl.config import RunConfig  # noqa: E402
from autortl.metrics_gate import validate  # noqa: E402
from autortl.report_parser import parse_all  # noqa: E402

tasks = [s["task"] for s in json.loads(Path(selection).read_text(encoding="utf-8"))["selected"]]
root = Path(out)
root.mkdir(parents=True, exist_ok=False)


def one(task):
    w = root / task
    w.mkdir()
    src = w / "TopModule.sv"
    src.write_text((Path(dataset) / f"{task}_ref.sv").read_text(encoding="utf-8").replace("RefModule", "TopModule"),
                   encoding="utf-8")
    cfg = RunConfig(mode="optimize", top_module="TopModule", implementation="out_of_context", vivado_bin=vivado_bin)
    try:
        ok, err, kind = vivado.run_synthesis([src], "TopModule", cfg, w)
        m = parse_all(w)
        try:
            validate(m, True)
            gate = "pass"
        except Exception as exc:  # noqa: BLE001
            gate = str(exc)
        marker = (w / "no_timing_paths.txt").read_text().strip() if (w / "no_timing_paths.txt").exists() else None
        row = {"task": task, "synth_ok": ok, "kind": kind.value, "error": err[:300], "wns_ns": m.wns_ns,
               "whs_ns": m.whs_ns, "timing_met": m.timing_met, "lut_used": m.lut_used, "ff_used": m.ff_used,
               "marker": marker, "gate": gate}
    except Exception as exc:  # noqa: BLE001
        row = {"task": task, "synth_ok": False, "kind": "exception", "error": repr(exc)[:300], "gate": "n/a"}
    print(f"{task:30} ok={row['synth_ok']!s:5} gate={row['gate'][:30]:30} wns={row.get('wns_ns')} lut={row.get('lut_used')} "
          f"ff={row.get('ff_used')} marker={row.get('marker')} {row['error'][:70]!r}", flush=True)
    return row


with ThreadPoolExecutor(workers) as pool:
    rows = list(pool.map(one, tasks))
(root / "synth_sweep.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
good = sum(r["synth_ok"] and r["gate"] == "pass" for r in rows)
print(f"{good}/{len(rows)} references synthesize and pass the metrics gate")
