"""Final sign-off: hold curriculum tiers bottom-up with the gate, archiving each campaign.

For each requested tier, in ascending order, run tools/tier0_gate.py campaigns
named signoff-t<tier>-<n> until the tier's latest full-tier history record is
held (three consecutive qualifying campaigns on one cohort, decided by the
curriculum runner), or until --max-campaigns campaigns have produced a verdict.
An infrastructure no-verdict (gate exit 3, no history record) is retried and
never counts toward that cap (signoff_cap_counts_infra_no_verdicts); after
--max-no-verdicts of them the tier ends with no verdict (exit 3), never as
"not held". Lower tiers are held
first because the gate refuses a tier while a higher tier is held
(stale_held_record_blocks_lower_gates). Every campaign, verdict or not, is
copied to evidence/<date>/<name>/ with a role report and a SHA-256 manifest.
Re-running skips campaigns already archived, so an interrupted pass resumes.

    python tools/signoff.py --tiers 0 1 2 3 4 5 6 --model gpt-6-luna --date 2026-11-02
"""
from __future__ import annotations
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from autortl.fileio import file_sha256

ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "curriculum" / "results.jsonl"
SKIP_DIRS = {"xsim.dir", ".Xil"}
JOBS = {0: 2, 1: 3}  # every other tier: 2 (heavy Vivado runs share one laptop)


def full_records(tier, history=None):
    """Every full-tier history record of tier, oldest first."""
    history = HISTORY if history is None else history  # looked up at call time
    if not history.exists():
        return []
    records = [json.loads(line) for line in history.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [r for r in records if r.get("tier") == tier and r.get("full_tier") is True]


def latest_full_record(tier, history=None):
    """The tier's latest full-tier history record, or None."""
    full = full_records(tier, history)
    return full[-1] if full else None


VERDICT_MARK = "signoff-verdict.json"


def archived_had_verdict(dest) -> bool:
    """Whether an archived campaign recorded a verdict; archives older than the mark count as verdicts."""
    mark = dest / VERDICT_MARK
    if not mark.is_file():
        return True
    return bool(json.loads(mark.read_text(encoding="utf-8")).get("verdict"))


def archive(name, dest, root=ROOT, python=sys.executable, verdict=None):
    """Copy one gate campaign's logs into dest with a role report and manifest."""
    logs = root / "logs"
    dest.mkdir(parents=True, exist_ok=False)
    if verdict is not None:
        (dest / VERDICT_MARK).write_text(json.dumps({"verdict": bool(verdict)}) + "\n",
                                         encoding="utf-8", newline="\n")
    run = logs / name
    if run.is_dir():
        for path in sorted(run.rglob("*")):
            rel = path.relative_to(run)
            if path.is_file() and not any(part in SKIP_DIRS for part in rel.parts):
                target = dest / "run" / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
    for path in sorted(logs.glob(name + "-*.json")) + sorted(logs.glob(name + ".console.txt")):
        shutil.copyfile(path, dest / path.name)
    if (root / "curriculum" / "results.jsonl").exists():
        shutil.copyfile(root / "curriculum" / "results.jsonl", dest / f"history-at-{name}.jsonl")
    if (dest / "run").is_dir():
        report = subprocess.run([python, str(root / "tools" / "role_report.py"), str(dest / "run")],
                                capture_output=True, text=True, encoding="utf-8", errors="replace")
        (dest / "role-report.md").write_text(report.stdout or report.stderr, encoding="utf-8", newline="\n")
    files = {p.relative_to(dest).as_posix(): file_sha256(p)
             for p in sorted(dest.rglob("*")) if p.is_file() and p.name != "archive-manifest.json"}
    (dest / "archive-manifest.json").write_text(json.dumps({"files": files}, indent=2) + "\n",
                                                encoding="utf-8", newline="\n")
    return len(files)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tiers", type=int, nargs="+", required=True)
    parser.add_argument("--model", default=None)
    parser.add_argument("--date", required=True, help="evidence/<date>/ folder for the archives")
    parser.add_argument("--max-campaigns", type=int, default=6,
                        help="campaigns with a verdict per tier; infrastructure no-verdicts do not count")
    parser.add_argument("--max-no-verdicts", type=int, default=12,
                        help="infrastructure no-verdicts per tier before it ends with no verdict")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--prefix", default="signoff",
                        help="campaign name prefix; a new pass on changed code uses a new prefix")
    args = parser.parse_args(argv)
    if sorted(args.tiers) != args.tiers:
        parser.error("--tiers must be ascending: lower tiers are held first")
    summary = []
    for tier in args.tiers:
        held = False
        verdicts = no_verdicts = n = 0
        while verdicts < args.max_campaigns:
            n += 1
            name = f"{args.prefix}-t{tier}-{n:02d}"
            dest = ROOT / "evidence" / args.date / name
            if dest.exists():
                if archived_had_verdict(dest):
                    verdicts += 1
                else:
                    no_verdicts += 1
                record = latest_full_record(tier)
                held = bool(record and record.get("held"))
                print(f"[signoff] {name}: already archived; tier {tier} held={held}", flush=True)
                if held:
                    break
                continue
            cmd = [args.python, str(ROOT / "tools" / "tier0_gate.py"), "--name", name, "--tier", str(tier),
                   "--jobs", str(JOBS.get(tier, 2)), "--python", args.python]
            if args.model:
                cmd += ["--model", args.model]
            console = ROOT / "logs" / f"{name}.console.txt"
            before = len(full_records(tier))
            print(f"[signoff] {name}: running", flush=True)
            with console.open("w", encoding="utf-8", errors="replace") as out:
                code = subprocess.run(cmd, cwd=ROOT, stdout=out, stderr=subprocess.STDOUT).returncode
            # Trust only a verdict this campaign recorded: a gate that refused to run or
            # an infrastructure no-verdict adds no record (a stale one must not count).
            recorded = len(full_records(tier)) > before
            files = archive(name, dest, python=args.python, verdict=recorded)
            if not recorded:
                print("[signoff] " + json.dumps({"tier": tier, "campaign": name, "gate_exit": code,
                                                 "archived_files": files, "verdict": None}), flush=True)
                if code not in (0, 3):  # 3 = infrastructure no-verdict; anything else is a refusal
                    print(f"[signoff] {name}: the gate recorded no verdict (exit {code}); stopping", flush=True)
                    return 2
                no_verdicts += 1
                if no_verdicts >= args.max_no_verdicts:
                    print(f"[signoff] tier {tier}: {no_verdicts} infrastructure no-verdicts; the tier has "
                          f"no verdict (not 'not held'); stopping", flush=True)
                    return 3
                continue
            verdicts += 1
            record = latest_full_record(tier)
            held = bool(record and record.get("held"))
            row = {"tier": tier, "campaign": name, "gate_exit": code, "archived_files": files,
                   "latest_qualified": record.get("qualified") if record else None, "held": held}
            summary.append(row)
            print("[signoff] " + json.dumps(row), flush=True)
            if held:
                break
        if not held:
            print(f"[signoff] tier {tier} not held after {args.max_campaigns} campaigns with a verdict; "
                  f"stopping", flush=True)
            return 1
    print("[signoff] all requested tiers held", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
