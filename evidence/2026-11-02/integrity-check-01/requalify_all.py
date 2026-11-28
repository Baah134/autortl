"""Re-qualify every curriculum testbench in xsim before sign-off.

Tier2/3 entries: materialize_cases() folders, each simulated in place.
Tier3 uart_fifo and tiers 4-6: their own qualify_tier4-based qualifier.
Writes a JSON summary; prints one line per entry.
"""
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
VIVADO = Path("C:/AMDDesignTools/2025.2/Vivado/bin")
sys.path.insert(0, str(REPO))
OUT.mkdir(parents=True, exist_ok=False)
PREVIOUS = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8")) if len(sys.argv) > 3 else {}


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


q4 = load(REPO / "curriculum/tier4/qualify_tier4.py", "q4")
summary = {}
entries = sorted(p for p in (REPO / "curriculum").glob("tier*/*") if (p / "qualification").is_dir())
for entry in entries:
    tag = f"{entry.parent.name}/{entry.name}"
    if tag in PREVIOUS:
        summary[tag] = PREVIOUS[tag]
        print(f"{tag:45s} {'QUALIFIED' if summary[tag]['qualified'] else 'NOT QUALIFIED'}  (carried over)", flush=True)
        continue
    work = OUT / entry.parent.name / entry.name
    if (entry / "qualification/cases.py").exists():
        cases = load(entry / "qualification/cases.py", "cases_" + entry.name)
        prepared = work / "cases"
        work.mkdir(parents=True)
        cases.materialize_cases(prepared)
        manifest = json.loads((prepared / "manifest.json").read_text(encoding="utf-8"))
        rows, ok = [], True
        for case in manifest["cases"]:
            folder = prepared / case["name"]
            sources = sorted(str(p) for p in folder.glob("*.v"))
            log = folder / "sim.log"
            with log.open("w", encoding="utf-8", errors="replace") as f:
                for cmd in ([str(VIVADO / "xvlog.bat"), *sources],
                            [str(VIVADO / "xelab.bat"), manifest.get("top") or Path(re.search(r"(?m)^tb:\s*(\S+)", (entry / "meta.yaml").read_text(encoding="utf-8"))[1]).stem, "-s", "snap", "--debug", "off"],
                            [str(VIVADO / "xsim.bat"), "snap", "-runall"]):
                    if subprocess.run(cmd, cwd=folder, stdout=f, stderr=subprocess.STDOUT).returncode:
                        break
            verdict, passed, detected = q4.judge(log.read_text(encoding="utf-8", errors="replace"))
            good = passed if case["name"] == "reference" else (not passed and verdict.startswith("TEST FAILED"))
            ok = ok and good
            rows.append({"case": case["name"], "verdict": verdict, "as_required": good, "fail_lines": detected})
        summary[tag] = {"qualified": ok, "cases": rows}
    else:
        result = subprocess.run([sys.executable, str(entry.parent / f"qualify_{entry.parent.name}.py")
                                 if (entry.parent / f"qualify_{entry.parent.name}.py").exists()
                                 else str(REPO / "curriculum/tier4/qualify_tier4.py"),
                                 str(entry), str(work)], capture_output=True, text=True, cwd=REPO)
        lines = [l for l in result.stdout.splitlines() if l.strip()]
        summary[tag] = {"qualified": result.returncode == 0 and any(l.strip() == "QUALIFIED" for l in lines),
                        "console": lines[-14:]}
        rows = summary[tag]["console"]
    n_cases = len(summary[tag].get("cases", [])) or sum(1 for l in summary[tag].get("console", []) if "TEST" in l)
    print(f"{tag:45s} {'QUALIFIED' if summary[tag]['qualified'] else 'NOT QUALIFIED'}  ({n_cases} cases)", flush=True)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
print("ALL QUALIFIED" if all(v["qualified"] for v in summary.values()) else "SOME NOT QUALIFIED")
