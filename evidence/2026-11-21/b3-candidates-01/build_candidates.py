"""Compose the B3 candidate lists from the measurement outputs (no tools run here).

usage: python build_candidates.py --final02 <summary.json> --ve-dataset <dir> --ve-synth <dir>
                                  --rtllm <clone> --rtllm-sweep <jsonl> --rtllm-synth <dir> --out <dir>

Inputs: final-02's graded rows; the VerilogEval reference synthesis folders
written by synth_refs.py (one metrics.json each); the RTLLM clone; the RTLLM
reference sweep (rtllm_sweep.py); the RTLLM synthesis folders. Outputs
verilogeval_candidates.json and rtllm_survey.json with names, hashes, licences
and metrics only, never third-party source text or local paths.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

MIN_LUT = 20                 # ROADMAP B3: "at least 20 LUTs after synthesis"
RTLLM_MAX = 12               # ROADMAP B3: "8 to 12 larger public designs"
RTLLM_MIN = 8
# The makefile's TEST_DESIGN names a module the reference does not define; the
# testbench instantiates the reference's own module name, which is synthesised.
SYNTH_TOP = {"Arithmetic/Other/fixed_point_substractor":
             ("fixed_point_subtractor", "makefile TEST_DESIGN is misspelt; testbench and reference use this name")}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clock_inputs(text: str) -> list[str]:
    """Input ports whose name contains 'clk' in any case, from every input declaration."""
    names = set()
    for decl in re.findall(r"\binput\b([^;)\n]*)", text):
        names.update(n for n in re.findall(r"[A-Za-z_]\w*", decl)
                     if "clk" in n.lower() and n not in ("wire", "reg", "logic", "signed"))
    return sorted(names)


def metrics(folder: Path) -> dict | None:
    path = folder / "metrics.json"
    if not path.is_file():
        return None
    m = json.loads(path.read_text())
    out = {k: m.get(k) for k in ("ok", "lut", "ff", "dsp", "bram", "wns", "whs", "met")}
    if m.get("wns") == -999.0:  # Vivado reported NA slack (no clocked register; e.g. inferred latches)
        out["wns"] = out["whs"] = out["met"] = None
        out["note"] = "timing NA in the routed report"
    if not m.get("ok"):
        first = ((m.get("err") or "").splitlines() or [""])[0]
        out["err"] = re.sub(r"\s*\[[A-Za-z]:[\\/][^\]]*\]", "", first)[:160]  # drop local file paths
    return out


def verilogeval(args) -> dict:
    rows = json.loads(Path(args.final02).read_text())
    passes = {}
    for r in rows:
        passes.setdefault(r["task"], {"single_call": 0, "ablation": 0, "full": 0})[r["arm"]] += bool(r["upstream_pass"])
    tasks = []
    for task in sorted(passes):
        p = passes[task]
        both = p["single_call"] > 0 and p["full"] > 0
        entry = {"task": task, "final02_passes": p, "a_and_c_pass": both}
        if both:
            ref = Path(args.ve_dataset) / f"{task}_ref.sv"
            entry["ref_sha256"] = sha(ref)
            entry["reference_ooc"] = metrics(Path(args.ve_synth) / task)
            m = entry["reference_ooc"]
            entry["eligible"] = bool(m and m["ok"] and m["lut"] >= MIN_LUT)
        else:
            entry["eligible"] = False
        tasks.append(entry)
    return {"source": "evidence/2026-11-21/final-02-results/summary.json", "min_lut": MIN_LUT,
            "rule": "arm A and arm C each pass at least one of three final-02 trials, and the official "
                    "reference has at least 20 LUTs after out-of-context synthesis and routing",
            "tasks": tasks, "eligible": [t["task"] for t in tasks if t["eligible"]]}


def rtllm(args) -> dict:
    root = Path(args.rtllm)
    commit = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True,
                            check=True).stdout.strip()
    licence_text = (root / "LICENSE").read_text(errors="replace")
    sweep = [json.loads(line) for line in Path(args.rtllm_sweep).read_text().splitlines() if line.strip()]
    designs = []
    for s in sweep:
        folder = s["design"].replace("/", "__").replace(" ", "_")
        m = metrics(Path(args.rtllm_synth) / folder)
        clocks = clock_inputs((root / s["design"] / s["ref"]).read_text(errors="replace"))
        clock_ok = set(clocks) <= {"clk"}
        entry = {"design": s["design"], "top": s["top"], "reference_file": s["ref"],
                 "reference_module_renamed_from": s["renamed_from"], "ref_sha256": s["ref_sha256"],
                 "testbench_sha256": s["testbench_sha256"], "description_sha256": s["description_sha256"],
                 "clock_ports": clocks, "icarus_compile_exit": s["compile_exit"],
                 "reference_passes_own_test": s["passed"], "single_clk_or_combinational": clock_ok,
                 "synthesised": m is not None, "reference_ooc": m}
        if s["design"] in SYNTH_TOP:
            entry["synthesis_top"], entry["synthesis_top_reason"] = SYNTH_TOP[s["design"]]
        entry["eligible"] = bool(s["passed"] and clock_ok and m and m["ok"] and m["lut"] >= MIN_LUT)
        entry["exclusion"] = None if entry["eligible"] else (
            "reference fails its own test under Icarus" if not s["passed"]
            else "clock port other than a single 'clk' (OOC flow times only clk)" if not clock_ok
            else "not synthesised: small or simple by inspection" if m is None
            else "reference does not synthesise in Vivado: " + (m.get("err") or "")[:120] if not m["ok"]
            else f"reference below {MIN_LUT} LUTs")
        designs.append(entry)
    ranked = sorted((d for d in designs if d["eligible"]), key=lambda d: (-d["reference_ooc"]["lut"], d["design"]))
    return {"repository": "https://github.com/hkust-zhiyao/RTLLM", "commit": commit, "version": "v2.1",
            "licence": "MIT" if licence_text.startswith("MIT License") else "unrecognised",
            "licence_sha256": sha(root / "LICENSE"),
            "per_file_licence_notices": "none found in design folders (repository MIT licence applies)",
            "simulator": "Icarus Verilog 12.0, iverilog -g2012 testbench.v <top>.v; pass = 'Your Design Passed'",
            "designs": designs, "eligible_ranked": [d["design"] for d in ranked],
            "proposed": [d["design"] for d in ranked[:RTLLM_MAX]],
            "selection_rule": f"pass own test, one clock port named clk or none, reference >= {MIN_LUT} LUTs; "
                              f"the {RTLLM_MAX} largest by reference LUTs (at least {RTLLM_MIN})"}


def main():
    p = argparse.ArgumentParser()
    for name in ("--final02", "--ve-dataset", "--ve-synth", "--rtllm", "--rtllm-sweep", "--rtllm-synth", "--out"):
        p.add_argument(name, required=True)
    args = p.parse_args()
    out = Path(args.out)
    for name, data in (("verilogeval_candidates.json", verilogeval(args)), ("rtllm_survey.json", rtllm(args))):
        (out / name).write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
