"""Qualify uart_tx_tb.v before it may grade harness output.

The testbench must PASS on reference.v and FAIL on every mutant in
mutants.json. Each mutant changes exactly one place in the reference (the
`find` text must occur once). Every run's sources and simulator log are kept.

    python qualify_tb.py <out-dir> [--tb FILE ... --top NAME] [--exempt MUTANT ...]

--tb and --top qualify another testbench (default uart_tx_tb.v, top
uart_tx_tb); every --tb file is compiled. A mutant named by --exempt is one
that testbench cannot distinguish by design (for example `parameter_ignored`
for a check that runs only at DIV=868); it is run and reported, expected to
pass, and named in the results.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
TB = HERE.parent / "uart_tx_tb.v"


def simulate(sources, work, vivado, tbs=(TB,), top="uart_tx_tb"):
    """Compile and run the testbench; return (verdict line, passed)."""
    work.mkdir(parents=True)
    tool = lambda name: str(next(p for p in (vivado / f"{name}.bat", vivado / name) if p.exists()))
    log = work / "sim.log"
    with log.open("w", encoding="utf-8", errors="replace") as out:
        for cmd in ([tool("xvlog"), *[s.as_posix() for s in sources], *[t.as_posix() for t in tbs]],
                    [tool("xelab"), top, "-s", "tb_snap", "--debug", "off"],
                    [tool("xsim"), "tb_snap", "-runall"]):
            if subprocess.run(cmd, cwd=work, stdout=out, stderr=subprocess.STDOUT).returncode:
                break
    text = log.read_text(encoding="utf-8", errors="replace")
    verdicts = [line.strip() for line in text.splitlines() if line.strip().startswith(("TEST PASSED", "TEST FAILED"))]
    verdict = verdicts[-1] if verdicts else "NO VERDICT (compile or elaboration failed)"
    return verdict, verdict == "TEST PASSED"


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("out", type=Path)
    parser.add_argument("--vivado", type=Path, default=Path("C:/AMDDesignTools/2025.2/Vivado/bin"))
    parser.add_argument("--tb", type=Path, action="append")
    parser.add_argument("--top", default="uart_tx_tb")
    parser.add_argument("--exempt", action="append", default=[])
    args = parser.parse_args(argv)
    tbs = [t.resolve() for t in args.tb] if args.tb else [TB]
    if args.out.exists() and any(args.out.iterdir()):
        raise SystemExit(f"{args.out} must be new or empty")
    reference = (HERE / "reference.v").read_text(encoding="utf-8")
    results = {"testbench": {t.name: hashlib.sha256(t.read_bytes()).hexdigest() for t in tbs},
               "top": args.top, "exempt": sorted(args.exempt),
               "reference_sha256": hashlib.sha256(reference.encode()).hexdigest(), "runs": []}
    cases = [{"name": "reference", "why": "control", "source": reference, "expect_pass": True}]
    for mutant in json.loads((HERE / "mutants.json").read_text(encoding="utf-8")):
        if reference.count(mutant["find"]) != 1:
            raise SystemExit(f"mutant {mutant['name']}: find text occurs {reference.count(mutant['find'])} times")
        cases.append({"name": mutant["name"], "why": mutant["why"], "expect_pass": mutant["name"] in args.exempt,
                      "source": reference.replace(mutant["find"], mutant["replace"])})
    ok = True
    for case in cases:
        work = args.out / case["name"]
        src = work / "src" / "uart_tx.v"
        src.parent.mkdir(parents=True)
        src.write_text(case["source"], encoding="utf-8", newline="\n")
        verdict, passed = simulate([src], work / "sim", args.vivado, tbs, args.top)
        good = passed == case["expect_pass"] and not verdict.startswith("NO VERDICT")
        ok &= good
        results["runs"].append({"case": case["name"], "why": case["why"], "expect_pass": case["expect_pass"],
                                "verdict": verdict, "as_required": good,
                                "source_sha256": hashlib.sha256(src.read_bytes()).hexdigest()})
        print(f"{case['name']:28} {'ok ' if good else 'BAD'} {verdict}", flush=True)
    results["qualified"] = ok
    (args.out / "qualification.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("QUALIFIED" if ok else "NOT QUALIFIED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
