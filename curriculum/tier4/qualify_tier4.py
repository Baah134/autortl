"""Qualify a tier4 entry's independent testbench against its reference and mutants.

The testbench must PASS on qualification/reference.v and FAIL every mutant in
qualification/mutants.json with a raw assertion (a line starting ``FAIL`` plus a
``TEST FAILED`` verdict). A watchdog, a missing verdict or a compile error is not
a detection. Each mutant replaces one ``find`` text that occurs exactly once.

    python curriculum/tier4/qualify_tier4.py <entry-dir> <out-dir> [--vivado BIN]

Every run keeps its source and simulator log under <out-dir>. This script is
the only part of the fixture that launches tools; importing it launches none.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
import subprocess
import sys

DEFAULT_VIVADO = Path("C:/AMDDesignTools/2025.2/Vivado/bin")


def _meta_value(text, key):
    match = re.search(rf"(?m)^{key}:\s*(\S+)\s*$", text)
    if match is None:
        raise ValueError(f"meta.yaml has no {key}")
    return match.group(1)


def load_entry(entry):
    """Return the testbench path, its top module, the reference and every case."""
    entry = Path(entry).resolve()
    meta = (entry / "meta.yaml").read_text(encoding="utf-8")
    top, tb_name = _meta_value(meta, "top"), _meta_value(meta, "tb")
    tb = entry / tb_name
    reference = (entry / "qualification" / "reference.v").read_text(encoding="utf-8")
    mutants = json.loads((entry / "qualification" / "mutants.json").read_text(encoding="utf-8"))
    cases = [{"name": "reference", "why": "control", "source": reference, "expect_pass": True}]
    for mutant in mutants:
        count = reference.count(mutant["find"])
        if count != 1:
            raise ValueError(f"mutant {mutant['name']}: find text occurs {count} times")
        cases.append({"name": mutant["name"], "why": mutant["why"], "expect_pass": False,
                      "source": reference.replace(mutant["find"], mutant["replace"], 1)})
    if len({case["source"] for case in cases}) != len(cases):
        raise ValueError("duplicate case sources")
    return tb, top + "_tb", cases


def judge(log_text):
    """Return (verdict, passed, assertion_detected) from raw simulator output."""
    verdicts = [line.strip() for line in log_text.splitlines()
                if line.strip().startswith(("TEST PASSED", "TEST FAILED"))]
    verdict = verdicts[-1] if verdicts else "NO VERDICT (compile or elaboration failed)"
    passed = verdict == "TEST PASSED"
    detected = (verdict.startswith("TEST FAILED")
                and re.search(r"(?m)^\s*FAIL(?:\s|:)\s*\S", log_text) is not None
                and re.search(r"\b(?:watchdog|timeout|timed\s+out)\b", log_text, re.I) is None)
    return verdict, passed, detected


def simulate(source, tb, top, work, vivado):
    work.mkdir(parents=True)
    tool = lambda name: str(next(p for p in (vivado / f"{name}.bat", vivado / name) if p.exists()))
    log = work / "sim.log"
    with log.open("w", encoding="utf-8", errors="replace") as out:
        for cmd in ([tool("xvlog"), source.as_posix(), tb.as_posix()],
                    [tool("xelab"), top, "-s", "tb_snap", "--debug", "off"],
                    [tool("xsim"), "tb_snap", "-runall"]):
            if subprocess.run(cmd, cwd=work, stdout=out, stderr=subprocess.STDOUT).returncode:
                break
    return judge(log.read_text(encoding="utf-8", errors="replace"))


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("entry", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--vivado", type=Path, default=DEFAULT_VIVADO)
    args = parser.parse_args(argv)
    if args.out.exists() and any(args.out.iterdir()):
        raise SystemExit(f"{args.out} must be new or empty")
    tb, top, cases = load_entry(args.entry)
    results = {"entry": str(args.entry), "top": top,
               "testbench_sha256": hashlib.sha256(tb.read_bytes()).hexdigest(), "runs": []}
    ok = True
    for case in cases:
        work = args.out / case["name"]
        src = work / "src" / "design.v"
        src.parent.mkdir(parents=True)
        src.write_text(case["source"], encoding="utf-8", newline="\n")
        verdict, passed, detected = simulate(src, tb, top, work / "sim", args.vivado)
        good = passed if case["expect_pass"] else detected
        ok &= good
        results["runs"].append({"case": case["name"], "why": case["why"], "expect_pass": case["expect_pass"],
                                "verdict": verdict, "assertion_detected": detected, "as_required": good,
                                "source_sha256": hashlib.sha256(src.read_bytes()).hexdigest()})
        print(f"{case['name']:30} {'ok ' if good else 'BAD'} {verdict}", flush=True)
    results["qualified"] = ok
    (args.out / "qualification.json").write_text(json.dumps(results, indent=2) + "\n",
                                                 encoding="utf-8", newline="\n")
    print("QUALIFIED" if ok else "NOT QUALIFIED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
