"""Scratch: OOC-synthesise official references with the harness flow; print metrics JSON.

usage: python synth_refs.py <code_root> <out_dir> <workers> <top> <ref_file>... (name=path pairs)
"""
import json
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

code, out, workers, top = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
pairs = [a.split("=", 1) for a in sys.argv[5:]]
sys.path.insert(0, str(code))
from autortl import vivado  # noqa: E402
from autortl.config import RunConfig  # noqa: E402

cfg = RunConfig(mode="build", implementation="out_of_context",
                vivado_bin="C:/AMDDesignTools/2025.2/Vivado/bin/vivado.bat")


def one(pair):
    name, src = pair
    top_name = top
    if ":" in name and not name[1:2] == ":":
        name, top_name = name.split(":", 1)
    work = out / name
    if (work / "metrics.json").exists():
        return json.loads((work / "metrics.json").read_text())
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    srcs = []
    for s in src.split(","):
        dst = work / Path(s).name
        shutil.copyfile(s, dst)
        srcs.append(dst)
    ok, err, kind = vivado.run_synthesis(srcs, top_name, cfg, work, timeout=1800)
    rec = {"name": name, "ok": ok, "err": err[:500], "kind": str(kind)}
    if ok:
        m = vivado.full_metrics(work)
        rec.update(lut=m.lut_used, ff=m.ff_used, dsp=m.dsp_used, bram=m.bram_used,
                   wns=m.wns_ns, whs=m.whs_ns, met=m.timing_met)
    (work / "metrics.json").write_text(json.dumps(rec))
    return rec


with ThreadPoolExecutor(workers) as pool:
    for rec in pool.map(one, pairs):
        print(json.dumps(rec), flush=True)
