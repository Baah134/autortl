"""Scratch: every RTLLM reference against its own testbench with Icarus; prints JSON lines.

usage: python -I rtllm_sweep.py <rtllm_root> <work_root> <iverilog> <vvp>
"""
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

root, work_root, iverilog, vvp = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], sys.argv[4]
PASS = re.compile(r"Your Design Passed", re.I)
FAIL = re.compile(r"(Failed|Error|mismatch)", re.I)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


for ref in sorted(root.glob("*/**/verified_*.v")):
    d = ref.parent
    if any(part.startswith("_") or part == ".git" for part in d.relative_to(root).parts):
        continue
    make = (d / "makefile").read_text(errors="replace")
    m = re.search(r"TEST_DESIGN\s*=\s*(\S+)", make)
    top = m.group(1) if m else None
    text = ref.read_text(errors="replace")
    modules = re.findall(r"^\s*module\s+([A-Za-z_][A-Za-z0-9_]*)", text, re.M)
    renamed = None
    if top and top not in modules:
        cands = [x for x in modules if x.startswith("verified_")]
        if len(cands) == 1:
            renamed = cands[0]
            text = re.sub(r"\bmodule\s+" + cands[0] + r"\b", "module " + top, text)
    work = work_root / d.relative_to(root).as_posix().replace("/", "__").replace(" ", "_")
    shutil.rmtree(work, ignore_errors=True)
    shutil.copytree(d, work)
    (work / f"{top}.v").write_text(text)
    rec = {"design": d.relative_to(root).as_posix(), "top": top, "renamed_from": renamed,
           "modules": modules, "ref": ref.name, "ref_sha256": sha(ref),
           "testbench_sha256": sha(d / "testbench.v"),
           "description_sha256": sha(d / "design_description.txt") if (d / "design_description.txt").exists() else None,
           "clock_ports": sorted(set(re.findall(r"input\s+(?:wire\s+)?(\w*clk\w*)", text)))}
    c = subprocess.run([iverilog, "-g2012", "-o", "sim.vvp", "testbench.v", f"{top}.v"], cwd=work,
                       capture_output=True, text=True, timeout=120)
    rec["compile_exit"] = c.returncode
    if c.returncode == 0:
        try:
            r = subprocess.run([vvp, "-n", "sim.vvp"], cwd=work, capture_output=True, text=True, timeout=120)
            out = r.stdout + r.stderr
            rec["sim_exit"] = r.returncode
        except subprocess.TimeoutExpired:
            out, rec["sim_exit"] = "TIMEOUT", None
        rec["passed"] = bool(PASS.search(out))
        rec["tail"] = out.strip().splitlines()[-2:] if out.strip() else []
    else:
        rec["passed"] = False
        rec["tail"] = c.stderr.strip().splitlines()[:3]
    print(json.dumps(rec), flush=True)
