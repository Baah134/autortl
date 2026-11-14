"""Reference control for every task: RefModule renamed to TopModule must pass.

usage: python reference_sweep.py <repo> <dataset_dir> <out_dir> <iverilog> <vvp>
"""
import json
import sys
import time
from pathlib import Path

repo, dataset, out, iverilog, vvp = sys.argv[1:6]
sys.path.insert(0, repo)
from benchmark import verilogeval as ve  # noqa: E402

out = Path(out)
out.mkdir(parents=True, exist_ok=False)
rows, t0 = [], time.monotonic()
for task_id in ve.list_tasks(dataset):
    task = ve.load_task(dataset, task_id)
    cdir = out / task_id
    cdir.mkdir()
    cand = cdir / "TopModule.sv"
    cand.write_text(task.ref.read_text(encoding="utf-8").replace("RefModule", "TopModule"), encoding="utf-8")
    v = ve.grade([cand], task, cdir / "grade", iverilog=iverilog, vvp=vvp)
    rows.append({"task": task_id, "status": v["status"], "upstream_code": v["upstream_code"],
                 "agree": v["agree"], "mismatches": v["mismatches"], "samples": v["samples"],
                 "sim_seconds": (v["simulate"] or {}).get("seconds")})
    if v["status"] != "pass" or not v["upstream_pass"]:
        print("NOT PASS", rows[-1])
(out / "reference_sweep.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
ok = sum(r["status"] == "pass" and r["upstream_code"] == "." for r in rows)
print(f"{ok}/{len(rows)} references pass both strict and upstream in {time.monotonic() - t0:.0f}s; "
      f"disagreements: {sum(not r['agree'] for r in rows)}")
