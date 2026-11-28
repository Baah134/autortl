"""Real Icarus controls for benchmark.verilogeval.grade on pinned VerilogEval tasks.

usage: python grader_controls.py <repo> <dataset_dir> <out_dir> <iverilog> <vvp>
"""
import json
import sys
from pathlib import Path

repo, dataset, out, iverilog, vvp = sys.argv[1:6]
sys.path.insert(0, repo)
from benchmark import verilogeval as ve  # noqa: E402

MUTANTS = {  # one behavioral fault per task: (text in reference, replacement)
    "Prob001_zero": ("1'b0", "1'b1"),
    "Prob027_fadd": ("a+b+cin", "a+b"),
    "Prob035_count1to10": ("q == 10", "q == 9"),
    "Prob107_fsm1s": ("state <= B;", "state <= A;"),
}
HANG = "\n  initial begin : control_hang\n    while (1) begin end\n  end\n"
EXPECT = {"reference": ("pass", "."), "broken": ("fail", "R"),
          "syntax": ("compile_error", "S"), "hang": ("timeout", "T")}

out = Path(out)
out.mkdir(parents=True, exist_ok=False)
rows = []
for task_id, (old, new) in MUTANTS.items():
    task = ve.load_task(dataset, task_id)
    ref = task.ref.read_text(encoding="utf-8").replace("module RefModule", "module TopModule")
    assert old in ref, (task_id, old)
    sources = {"reference": ref, "broken": ref.replace(old, new, 1),
               "syntax": ref.replace("endmodule", "", 1) + "\nthis is not verilog;\n",
               "hang": ref.replace("endmodule", HANG + "endmodule", 1)}
    for kind, text in sources.items():
        cdir = out / task_id / kind
        cdir.mkdir(parents=True)
        cand = cdir / "TopModule.sv"
        cand.write_text(text, encoding="utf-8")
        verdict = ve.grade([cand], task, cdir / "grade", iverilog=iverilog, vvp=vvp)
        expected = EXPECT[kind]
        ok = (verdict["status"], verdict["upstream_code"]) == expected
        if kind == "broken":  # any nonpass upstream code with a strict fail is a detection
            ok = verdict["status"] == "fail" and not verdict["upstream_pass"]
        rows.append({"task": task_id, "control": kind, "status": verdict["status"],
                     "upstream_code": verdict["upstream_code"], "mismatches": verdict["mismatches"],
                     "samples": verdict["samples"], "agree": verdict["agree"], "expected": expected,
                     "as_expected": ok,
                     "compile_exit": verdict["compile"]["exit"],
                     "sim_exit": (verdict["simulate"] or {}).get("exit"),
                     "sim_seconds": (verdict["simulate"] or {}).get("seconds")})
        print(f"{task_id:22} {kind:9} {verdict['status']:14} {verdict['upstream_code']} "
              f"mm={verdict['mismatches']} n={verdict['samples']} {'OK' if ok else 'UNEXPECTED'}")
(out / "controls.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
print("all as expected" if all(r["as_expected"] for r in rows) else "SOME CONTROLS UNEXPECTED")
