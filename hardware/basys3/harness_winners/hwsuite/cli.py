"""Command line for the harness-winners board suite.

    python -m hwsuite verify                       # winner hashes vs evidence and run state
    python -m hwsuite sim [--design NAME]          # winner must PASS, its fault must FAIL
    python -m hwsuite build --design NAME          # Vivado batch implementation + bitstream
    python -m hwsuite program --design NAME [--bit FILE]   # load the bitstream over JTAG
    python -m hwsuite hw --design NAME [--bit FILE] [--count N] [--wrong-model]
    python -m hwsuite all [--design NAME]          # verify, sim, then per design build, program, hw
    python -m hwsuite evidence --out DIR           # archive outputs + summary.json + SHA-256 manifest

Run from hardware/basys3/harness_winners. Outputs go to build/<design>/.
Vivado tools are called through option files because the Windows .bat
wrappers split arguments at '='.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from . import designs as design_table
from . import vectors

SUITE = design_table.SUITE
UART_RTL = SUITE.parent / "uart_echo" / "rtl"
DEFAULT_VIVADO = Path(os.environ.get("AUTORTL_VIVADO_BIN", "C:/AMDDesignTools/2025.2/Vivado/bin"))
SIM_COUNT, SIM_RESTART, SIM_CHUNK = 1200, 600, 32


class SuiteError(RuntimeError):
    pass


def _tool(vivado: Path, name: str) -> str:
    for candidate in (vivado / f"{name}.bat", vivado / name):
        if candidate.exists():
            return str(candidate)
    raise SuiteError(f"{name} not found in {vivado}; set AUTORTL_VIVADO_BIN or pass --vivado")


def _run(cmd, cwd: Path, log: Path) -> int:
    with log.open("w", encoding="utf-8", errors="replace") as handle:
        return subprocess.run(cmd, cwd=cwd, stdout=handle, stderr=subprocess.STDOUT).returncode


def _warnings(*logs: Path) -> list[str]:
    found = []
    for log in logs:
        for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
            if re.match(r"^(WARNING|CRITICAL WARNING|ERROR)", line):
                found.append(f"{log.name}: {line}")
    return found


def rtl_sources(design, winner_path: Path) -> list[Path]:
    return [UART_RTL / "uart_rx.v", UART_RTL / "uart_tx.v", SUITE / "rtl" / "shell_fifo.v",
            winner_path, design.adapter, SUITE / "rtl" / "stream_shell.v"]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _simulation_verdict(text: str) -> tuple[str, str]:
    """Only the frozen bench's completed data mismatches can kill a fault."""
    verdicts = [line for line in text.splitlines() if re.match(r"^(PASS|FAIL)\b", line)]
    if re.search(r"watchdog|timeout|timed\s+out", text, re.IGNORECASE):
        return "invalid_verdict", "FAIL: simulation timeout or watchdog"
    assertions = [line for line in text.splitlines() if re.fullmatch(
        r"ERROR: transaction \d+ result differs from the model", line)]
    known_assertion = r"ERROR: (transaction \d+ result differs from the model|input overflow flag set|break flag not set|(backpressure|overlap) coverage \d+ below \d+)"
    if any(re.match(r"^(WARNING|CRITICAL WARNING|ERROR|FATAL)\b", line) and
           not re.fullmatch(known_assertion, line) for line in text.splitlines()):
        return "tool_failure", "FAIL: simulator diagnostic (see xsim.txt)"
    if len(verdicts) != 1:
        return "invalid_verdict", "FAIL: missing or contradictory simulation verdict"
    verdict = verdicts[0]
    success = re.fullmatch(r"PASS: (\d+) results matched the model, with a restart at (\d+) \(stalled \d+, overlap \d+\)", verdict)
    if (success and int(success[1]) == SIM_COUNT and int(success[2]) == SIM_RESTART and
            not any(line.startswith("ERROR:") for line in text.splitlines())):
        return "passed", verdict
    failed = re.fullmatch(r"FAIL: (\d+) errors, (\d+) of (\d+) results checked", verdict)
    if (failed and 0 < int(failed[1]) <= SIM_COUNT and
            int(failed[2]) == int(failed[3]) == SIM_COUNT and assertions and
            all(0 <= int(re.search(r"transaction (\d+)", line)[1]) < SIM_COUNT for line in assertions)):
        return "behavioral_failure", verdict
    return "invalid_verdict", "FAIL: incomplete or unproved simulation result"


def _simulation_evidence(out: Path, outcome: str) -> bool:
    """Validate a new receipt, including its raw logs and input identities.

    Historical archives without receipts stay historical; they are never
    silently reclassified as a newly verified execution.
    """
    try:
        receipt = json.loads((out / "simulation.json").read_text(encoding="utf-8"))
        codes = receipt["tool_exits"]
        if (type(receipt.get("schema")) is not int or receipt["schema"] != 1 or receipt.get("outcome") != outcome or
                receipt.get("inputs_unchanged") is not True or
                set(codes) != {"xvlog", "xelab", "xsim"} or
                any(type(code) is not int or code != 0 for code in codes.values()) or
                set(receipt["log_sha256"]) != {"xvlog.txt", "xelab.txt", "xsim.txt"}):
            return False
        if any(_sha(out / name) != digest for name, digest in receipt["log_sha256"].items()):
            return False
        if not receipt["input_sha256"] or any(_sha(Path(name)) != digest for name, digest in receipt["input_sha256"].items()):
            return False
        actual, verdict = _simulation_verdict((out / "xsim.txt").read_text(encoding="utf-8", errors="replace"))
        return actual == outcome and verdict == receipt["verdict"]
    except (OSError, ValueError, TypeError, KeyError):
        return False


def simulate(design, vivado: Path, out: Path, winner_path: Path) -> tuple[bool, str]:
    """Compile and run the generic testbench; return (passed, verdict line)."""
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    stimulus, expected = vectors.build(design.name, SIM_COUNT, SIM_RESTART)
    vectors.write(out, stimulus, expected)
    paths = rtl_sources(design, winner_path) + [SUITE / "sim" / "tb_stream_shell.v"]
    inputs = {str(p.resolve()): _sha(p) for p in paths}
    sources = [p.as_posix() for p in paths]
    (out / "xvlog.opt").write_text("\n".join(sources) + "\n", encoding="ascii")
    generics = {"IN_BYTES": design.in_bytes, "OUT_BYTES": design.out_bytes,
                "N": SIM_COUNT, "RESTART_AT": SIM_RESTART, "CHUNK": SIM_CHUNK,
                "REQUIRE_OVERLAP": int(design.overlap)}
    (out / "xelab.opt").write_text("\n".join(
        ["tb_stream_shell", "-s", "snap", "-debug", "off"] +
        [f'-generic_top "{k}={v}"' for k, v in generics.items()]) + "\n", encoding="ascii")
    codes = {}

    def finish(outcome, verdict):
        unchanged = all(Path(name).is_file() and _sha(Path(name)) == digest for name, digest in inputs.items())
        if not unchanged:
            outcome, verdict = "invalid_verdict", "FAIL: simulation inputs changed"
        logs = {name: _sha(out / name) for name in ("xvlog.txt", "xelab.txt", "xsim.txt") if (out / name).is_file()}
        (out / "simulation.json").write_text(json.dumps({
            "schema": 1, "tool_exits": codes, "outcome": outcome, "verdict": verdict,
            "log_sha256": logs, "input_sha256": inputs, "inputs_unchanged": unchanged,
        }, indent=2), encoding="utf-8")
        return outcome == "passed", verdict

    for tool, options in (("xvlog", ["-f", "xvlog.opt"]), ("xelab", ["-f", "xelab.opt"])):
        try:
            codes[tool] = _run([_tool(vivado, tool), *options], out, out / f"{tool}.txt")
        except (OSError, subprocess.SubprocessError, SuiteError) as exc:
            codes[tool] = None
            return finish("tool_failure", f"FAIL: {tool} launch failed: {exc}")
        if type(codes[tool]) is not int or codes[tool] != 0:
            return finish("tool_failure", f"FAIL: {tool} exit {codes[tool]} (see {tool}.txt)")
    warnings = _warnings(out / "xvlog.txt", out / "xelab.txt")
    if warnings:
        return finish("tool_failure", "FAIL: compile warnings: " + "; ".join(warnings[:3]))
    try:
        codes["xsim"] = _run([_tool(vivado, "xsim"), "snap", "-R"], out, out / "xsim.txt")
    except (OSError, subprocess.SubprocessError, SuiteError) as exc:
        codes["xsim"] = None
        return finish("tool_failure", f"FAIL: xsim launch failed: {exc}")
    if type(codes["xsim"]) is not int or codes["xsim"] != 0:
        return finish("tool_failure", f"FAIL: xsim exit {codes['xsim']} (see xsim.txt)")
    return finish(*_simulation_verdict((out / "xsim.txt").read_text(encoding="utf-8", errors="replace")))


def cmd_verify(args, table):
    for design in _selected(args, table):
        design.verify()
        design.faulted_source()
        print(f"{design.name:18} OK  {design.sha256[:12]}  {design.winner.relative_to(design_table.REPO).as_posix()}")


def cmd_sim(args, table):
    failures = 0
    summary = {}
    for design in _selected(args, table):
        design.verify()
        out = SUITE / "build" / design.name / "sim"
        ok, verdict = simulate(design, args.vivado, out, design.winner)
        print(f"{design.name:18} winner: {verdict}")
        fault_dir = SUITE / "build" / design.name / "fault"
        fault_dir.mkdir(parents=True, exist_ok=True)
        faulted = fault_dir / f"{design.module}.v"
        faulted.write_text(design.faulted_source(), encoding="utf-8", newline="\n")
        fault_ok, fault_verdict = simulate(design, args.vivado, fault_dir / "sim", faulted)
        caught = not fault_ok and _simulation_evidence(fault_dir / "sim", "behavioral_failure")
        print(f"{design.name:18} fault {design.fault['name']}: {fault_verdict} -> {'caught' if caught else 'NOT CAUGHT'}")
        summary[design.name] = {"winner": verdict, "fault": design.fault["name"], "fault_verdict": fault_verdict,
                                "fault_caught": caught}
        failures += (not ok) + (not caught)
    (SUITE / "build").mkdir(exist_ok=True)
    (SUITE / "build" / "sim_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if failures:
        raise SuiteError(f"{failures} simulation check(s) failed")


# Vivado messages that mean the machine, not the design, failed: a locked
# scratch directory, an unavailable license. A build that fails with one of
# these (and nothing else) is retried once; the design is never changed and
# the failed attempt's logs are kept beside the retry.
INFRA_MESSAGES = ("[Designutils 20-411]", "[Common 17-345]", "[Common 17-301]")


def infra_only(log: Path) -> bool:
    """True when every ERROR/CRITICAL WARNING in the log is a known infrastructure message."""
    problems = [l for l in log.read_text(encoding="utf-8", errors="replace").splitlines()
                if re.match(r"^(ERROR|CRITICAL WARNING):", l)]
    return bool(problems) and all(any(m in l for m in INFRA_MESSAGES) for l in problems)


def cmd_build(args, table):
    for design in _selected(args, table, require_one=True):
        design.verify()
        out = SUITE / "build" / design.name / "impl"
        out.mkdir(parents=True, exist_ok=True)
        (out / "sources.txt").write_text("\n".join(p.as_posix() for p in rtl_sources(design, design.winner)) + "\n",
                                         encoding="ascii")
        cmd = [_tool(args.vivado, "vivado"), "-mode", "batch", "-nojournal", "-log", "vivado_build.log",
               "-source", (SUITE / "scripts" / "build.tcl").as_posix(), "-tclargs",
               (out / "sources.txt").as_posix(), out.as_posix(), str(design.in_bytes), str(design.out_bytes)]
        for attempt in (1, 2):
            code = _run(cmd, out, out / "vivado_console.txt")
            if code == 0 or attempt == 2 or not infra_only(out / "vivado_build.log"):
                break
            for name in ("vivado_build.log", "vivado_console.txt"):
                (out / name).replace(out / f"infra_attempt1_{name}")
            shutil.rmtree(out / ".Xil", ignore_errors=True)
            print(f"{design.name:18} build attempt 1 hit an infrastructure error only; retrying once")
        result = [l for l in (out / "vivado_console.txt").read_text(errors="replace").splitlines() if l.startswith("RESULT")]
        print(f"{design.name:18} build exit {code}: " + " | ".join(result))
        warnings = [w for w in _warnings(out / "vivado_build.log")]
        if code or warnings:
            raise SuiteError(f"{design.name}: build failed or warned: " + "; ".join(warnings[:3]))


def _bitstream(args, design) -> Path:
    """The bitstream to program or identify: --bit if given, else this design's build.

    --bit lets a fresh clone program an archived bitstream (evidence/2026-10-28/
    basys3-bitstreams-01) and rerun the board check without synthesis. A
    Model comparison alone cannot identify functionally equivalent images;
    hardware checks also require this suite's successful programming receipt.
    """
    return Path(args.bit) if getattr(args, "bit", None) else SUITE / "build" / design.name / "impl" / "stream_shell.bit"


def cmd_program(args, table):
    for design in _selected(args, table, require_one=True):
        out = SUITE / "build" / design.name / "impl"
        bit = _bitstream(args, design)
        if not bit.is_file():
            raise SuiteError(f"{design.name}: build first or pass --bit ({bit} missing)")
        from . import reports
        before_file = _sha(bit)
        before_payload = reports.bitstream_payload_sha256(bit)
        out.mkdir(parents=True, exist_ok=True)
        cmd = [_tool(args.vivado, "vivado"), "-mode", "batch", "-nojournal", "-log", "program.log",
               "-source", (SUITE / "scripts" / "program.tcl").as_posix(), "-tclargs", bit.as_posix()]
        _programmed().unlink(missing_ok=True)       # the board's old image is gone either way
        console = out / "program_console.txt"
        try:
            code = _run(cmd, out, console)
        except (OSError, subprocess.SubprocessError) as exc:
            raise SuiteError(f"{design.name}: programming launch failed: {exc}") from exc
        ok = _programming_console_ok(console)
        print(f"{design.name:18} program exit {code}: {'programmed' if ok else 'FAILED'}")
        if type(code) is not int or code != 0 or not ok:
            raise SuiteError(f"{design.name}: programming failed")
        if not bit.is_file() or _sha(bit) != before_file:
            raise SuiteError(f"{design.name}: bitstream changed while programming; image is unverified")
        _programmed().parent.mkdir(parents=True, exist_ok=True)
        _programmed().write_text(json.dumps({"schema": 1, "design": design.name, "bitstream": bit.resolve().as_posix(),
                                          "payload_sha256": before_payload, "file_sha256": before_file,
                                          "tool_exit_code": code, "console_path": console.resolve().as_posix(),
                                          "console_sha256": _sha(console)}, indent=2),
                              encoding="utf-8")


def _programmed() -> Path:
    """What `program` last loaded. The board holds one image, so this is suite-wide."""
    return SUITE / "build" / "programmed.json"


def _programming_console_ok(console: Path) -> bool:
    if not console.is_file():
        return False
    text = console.read_text(errors="replace")
    return (len(re.findall(r"^RESULT: programmed(?: .+)?$", text, re.MULTILINE)) == 1 and
            re.search(r"^(ERROR|CRITICAL WARNING|FATAL)\b", text, re.MULTILINE) is None)


def _check_programming_receipt(record, name, console: Path, payload: str) -> None:
    """Check recorded tool success, never infer it from a bitstream file alone."""
    try:
        valid = (isinstance(record, dict) and type(record.get("schema")) is int and record["schema"] == 1 and record["design"] == name and
                 type(record["tool_exit_code"]) is int and record["tool_exit_code"] == 0 and
                 re.fullmatch(r"[0-9a-f]{64}", record["file_sha256"]) is not None and
                 record["payload_sha256"] == payload and
                 _sha(console) == record["console_sha256"] and
                 _programming_console_ok(console))
    except (OSError, TypeError, ValueError, KeyError):
        valid = False
    if not valid:
        raise SuiteError(f"{name}: missing or invalid successful programming receipt; run program again")


def _programming_receipt(args, design) -> dict:
    """Local programming evidence, not device readback or external-change detection."""
    from . import reports
    try:
        record = json.loads(_programmed().read_text(encoding="utf-8"))
        bit = Path(args.bit) if getattr(args, "bit", None) else Path(record["bitstream"])
        payload = reports.bitstream_payload_sha256(bit)
        _check_programming_receipt(record, design.name, Path(record["console_path"]), payload)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise SuiteError(f"{design.name}: missing or invalid successful programming receipt; run program again") from exc
    return record


def _on_board(args, design) -> str:
    """Compatibility accessor: no file-only fallback and no legacy-record upgrade."""
    return _programming_receipt(args, design)["payload_sha256"]


def _hardware_control_accepted(report, wrong_model: bool, requested: int) -> bool:
    """A negative control is a completed mismatch, not a failed transport."""
    count, checked, mismatches = (report.get(k) for k in ("requested", "checked", "mismatches"))
    complete = (type(wrong_model) is bool and type(requested) is int and requested > 0 and
                {"passed", "wrong_model", "requested", "checked", "mismatches", "short_reply", "first_mismatch"}.issubset(report) and
                all(type(value) is int for value in (count, checked, mismatches)) and
                count == checked == requested and 0 <= mismatches <= checked and
                report.get("wrong_model") is wrong_model and report.get("short_reply") is None)
    if not complete:
        return False
    first = report.get("first_mismatch")
    if wrong_model:
        detail = (report.get("passed") is False and mismatches > 0 and isinstance(first, dict) and
                type(first.get("index")) is int and 0 <= first["index"] < checked and
                isinstance(first.get("expected"), str) and isinstance(first.get("got"), str))
        if not detail:
            return False
        try:
            expected, got = bytes.fromhex(first["expected"]), bytes.fromhex(first["got"])
            return len(expected) == len(got) > 0 and expected != got
        except ValueError:
            return False
    return report.get("passed") is True and mismatches == 0 and first is None


def cmd_hw(args, table):
    from . import hw
    for design in _selected(args, table, require_one=True):
        receipt = _programming_receipt(args, design)
        report = hw.run(design, port=args.port, count=args.count, chunk=args.chunk,
                        restart_every=args.restart_every, wrong_model=args.wrong_model, seed=args.seed)
        provenance_error = None
        try:
            if _programming_receipt(args, design) != receipt:
                raise SuiteError("programming receipt changed during hardware run")
        except SuiteError as exc:
            provenance_error = str(exc)
        report["bitstream_payload_sha256"] = receipt["payload_sha256"]
        report["programming_receipt"] = receipt
        report["programming_verified"] = provenance_error is None
        report["programming_error"] = provenance_error
        report["programming_provenance"] = "successful suite programming receipt; not device readback"
        report["control_accepted"] = provenance_error is None and _hardware_control_accepted(report, args.wrong_model, args.count)
        print(hw.format_report(report))
        out = SUITE / "build" / design.name / "hw"
        out.mkdir(parents=True, exist_ok=True)
        tag = "wrong_model" if args.wrong_model else "model"
        (out / f"{tag}_{args.count}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        if not report["control_accepted"]:
            raise SuiteError(f"{design.name}: hardware control incomplete, mismatched, or lacking programming proof")


def cmd_all(args, table):
    cmd_verify(args, table)
    cmd_sim(args, table)
    for design in _selected(args, table):
        one = argparse.Namespace(**{**vars(args), "design": design.name})
        cmd_build(one, table)
        cmd_program(one, table)
        cmd_hw(argparse.Namespace(**{**vars(one), "wrong_model": False}), table)
        cmd_hw(argparse.Namespace(**{**vars(one), "wrong_model": True, "count": min(args.count, 2000)}), table)


EVIDENCE_FILES = {
    "sim": ("xvlog.opt", "xelab.opt", "xvlog.txt", "xelab.txt", "xsim.txt", "simulation.json", "stim.hex", "expect.hex"),
    "fault/sim": ("xvlog.txt", "xelab.txt", "xsim.txt", "simulation.json"),
    "impl": ("sources.txt", "vivado_build.log", "vivado_console.txt", "timing_summary.rpt", "utilization.rpt",
             "utilization_hier.rpt", "utilization_winner.rpt", "drc.rpt", "program.log", "program_console.txt"),
}


def cmd_evidence(args, table):
    """Copy every archived output into one folder with a summary and SHA-256 manifest."""
    import hashlib
    from . import reports
    if not args.out:
        raise SuiteError("--out is required")
    final = Path(args.out).resolve()
    if final.exists() and any(final.iterdir()):
        raise SuiteError(f"{final} is not empty; evidence folders are never overwritten")
    # Assemble in a staging folder and move it into place only when complete,
    # so a failure never leaves a partial archive behind.
    out = final.with_name(final.name + ".partial")
    if out.exists():
        shutil.rmtree(out)
    try:
        _assemble_evidence(out, args, table)
    except BaseException:
        shutil.rmtree(out, ignore_errors=True)
        raise
    if final.exists():
        final.rmdir()
    out.rename(final)
    print(f"evidence moved into place: {final}")


def _assemble_evidence(out: Path, args, table):
    import hashlib
    from . import reports
    summary = {}
    for design in _selected(args, table):
        design.verify()
        src, dst = SUITE / "build" / design.name, out / design.name
        missing = []
        for sub, names in EVIDENCE_FILES.items():
            for name in names:
                path = src / sub / name
                if path.is_file():
                    (dst / sub).mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, dst / sub / name)
                else:
                    missing.append(f"{sub}/{name}")
        faulted = src / "fault" / f"{design.module}.v"
        if faulted.is_file():
            shutil.copy2(faulted, dst / "fault" / f"{design.module}.v.fault")
        for report in sorted((src / "hw").glob("*.json")) if (src / "hw").is_dir() else []:
            (dst / "hw").mkdir(parents=True, exist_ok=True)
            shutil.copy2(report, dst / "hw" / report.name)
        if missing:
            raise SuiteError(f"{design.name}: missing outputs {', '.join(missing)}; run `all` first")
        if not _simulation_evidence(src / "sim", "passed") or not _simulation_evidence(src / "fault" / "sim", "behavioral_failure"):
            raise SuiteError(f"{design.name}: missing valid simulation execution/assertion receipts; run sim again")
        sim_text = (src / "sim" / "xsim.txt").read_text(errors="replace")
        coverage = re.search(r"COVERAGE: (\d+) cycles with a result held under backpressure, (\d+) cycles", sim_text)
        hw_runs = {p.stem: json.loads(p.read_text()) for p in sorted((src / "hw").glob("*.json"))
                   if re.fullmatch(r"(model|wrong_model)_\d+", p.stem)}
        if not any(_hardware_control_accepted(r, False, r.get("requested")) for r in hw_runs.values()) or \
                not any(_hardware_control_accepted(r, True, r.get("requested")) for r in hw_runs.values()):
            raise SuiteError(f"{design.name}: needs completed hardware and actual wrong-model mismatch controls")
        bit = src / "impl" / "stream_shell.bit"
        payload = reports.bitstream_payload_sha256(bit)
        for run in hw_runs.values():
            if (run.get("programming_verified") is not True or run.get("control_accepted") is not True or
                    not _hardware_control_accepted(run, run.get("wrong_model"), run.get("requested"))):
                raise SuiteError(f"{design.name}: hardware run lacks verified programming receipt; old reports are not upgraded")
            _check_programming_receipt(run.get("programming_receipt", {}), design.name,
                                       src / "impl" / "program_console.txt", payload)
        tested = {r.get("bitstream_payload_sha256") for r in hw_runs.values()}
        if tested != {payload}:
            raise SuiteError(f"{design.name}: archived bitstream payload differs from the one tested on hardware")
        run_summary = json.loads((design.state.parent / "run_summary.json").read_text(encoding="utf-8"))
        best = run_summary["best_metrics"]
        harness = {"source": (design.state.parent / "run_summary.json").relative_to(design_table.REPO).as_posix(),
                   **{k: best[k] for k in ("lut_used", "ff_used", "dsp_used", "wns_ns", "whs_ns")}}
        summary[design.name] = {
            "title": design.title, "winner": design.winner.relative_to(design_table.REPO).as_posix(),
            "winner_sha256": design.sha256,
            "simulation": next(l for l in sim_text.splitlines() if l.startswith(("PASS", "FAIL"))),
            "backpressure_cycles": int(coverage.group(1)), "overlap_cycles": int(coverage.group(2)),
            "fault": design.fault["name"],
            "fault_simulation": next(l for l in (src / "fault" / "sim" / "xsim.txt").read_text(errors="replace")
                                     .splitlines() if l.startswith(("PASS", "FAIL"))),
            "build_warnings": reports.build_warnings(src / "impl" / "vivado_build.log"),
            **reports.build_result(src / "impl" / "vivado_console.txt"),
            "winner_resources": reports.winner_utilization(src / "impl" / "utilization_winner.rpt"),
            "harness_measurement": harness,
            "bitstream_payload_sha256": payload,
            "hardware_tested_this_payload": True,
            "programming_provenance": "successful suite programming receipt; not device readback",
            "bitstream_sha256": hashlib.sha256(bit.read_bytes()).hexdigest(),
            "hardware": {name: {k: run[k] for k in ("checked", "requested", "mismatches", "restarts",
                                                    "transactions_per_second", "passed", "wrong_model")}
                         for name, run in hw_runs.items()},
        }
    shared = [UART_RTL / "uart_rx.v", UART_RTL / "uart_tx.v", SUITE / "rtl" / "shell_fifo.v",
              SUITE / "rtl" / "stream_shell.v", SUITE / "sim" / "tb_stream_shell.v", SUITE / "designs.json",
              SUITE / "constraints" / "stream_shell.xdc", SUITE / "scripts" / "build.tcl",
              SUITE / "scripts" / "program.tcl"] + sorted((SUITE / "adapters").glob("*.v")) + \
             sorted((SUITE / "hwsuite").glob("*.py"))
    sources = {p.relative_to(design_table.REPO).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in shared}
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (out / "README.md").write_text(evidence_readme(summary), encoding="utf-8")
    files = {p.relative_to(out).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(out.rglob("*")) if p.is_file() and p.name != "manifest.json"}
    (out / "manifest.json").write_text(json.dumps({"schema": 1, "sources": sources, "files": files}, indent=2),
                                       encoding="utf-8")
    print(f"evidence: {len(summary)} designs, {len(files)} files, {len(sources)} bound sources")


def evidence_readme(summary: dict) -> str:
    """The archive's README, generated from summary.json so the two cannot disagree."""
    rows = []
    for name, s in summary.items():
        hw = next(r for r in s["hardware"].values() if not r["wrong_model"])
        wrong = next(r for r in s["hardware"].values() if r["wrong_model"])
        board, harness = s["winner_resources"], s["harness_measurement"]
        rows.append(
            f"| {s['title']} | {hw['checked']:,}/{hw['requested']:,}, {hw['mismatches']} mismatches, "
            f"{hw['restarts']} restarts | {wrong['mismatches']:,}/{wrong['checked']:,} differ | "
            f"{s['fault']}: {s['fault_simulation'].split(',')[0]} | {s['build_warnings']} | "
            f"{s['wns_ns']:+.3f} / {s['whs_ns']:+.3f} | {board['luts']} / {board['ffs']} / {board['dsps']} | "
            f"{harness['lut_used']} / {harness['ff_used']} / {harness['dsp_used']} |")
    return "\n".join([
        "# Every harness winner on the Basys 3, run 01",
        "",
        "Generated by `python -m hwsuite evidence` from `summary.json`. Each design is the unedited",
        "archived harness winner behind `hardware/basys3/harness_winners/rtl/stream_shell.v`. Every",
        "result is checked against an independent reference model written from the frozen",
        "specification. `manifest.json` binds every file here and the suite's sources by SHA-256.",
        "",
        "| Design | Hardware vs model | Wrong model | Injected fault (simulation) | Build warnings |"
        " WNS / WHS ns | Winner LUT / FF / DSP on board | Harness-measured LUT / FF / DSP |",
        "|---|---|---|---|---:|---:|---:|---:|",
        *rows,
        "",
        "How to read it:",
        "",
        "- **Hardware vs model**: random transactions with edge cases first, a UART-break restart",
        "  every 5,000, and the shell's LFSR traffic shaper applying random bubbles, random",
        "  `out_ready` and long stall phases.",
        "- **Wrong model**: the same hardware checked against a deliberately incorrect model, which",
        "  must fail.",
        "- **Injected fault**: the simulation repeated on a copy of the winner with one change,",
        "  which must fail. The winner's own simulation passed with backpressure and overlap",
        "  coverage requirements (see `summary.json`).",
        "- **Winner LUT / FF / DSP on board**: from `report_utilization -cells u_dut/u_winner`, with",
        "  the winner's hierarchy kept. Harness-measured: the same file's `best_metrics`, built",
        "  standalone. Small differences come from standalone top-level I/O. For example, the",
        "  divider's 8 extra standalone flip-flops are `quotient_work_reg[*]_lopt_replica` copies made",
        "  because, as a top, those bits drive output ports; see",
        "  `../divider-ff-replica-analysis-01`.",
        "- **Bitstreams**: `hardware_tested_this_payload` requires a successful programming receipt",
        "  with actual tool exit, console digest and matching configuration payload for every run.",
        "  This local receipt is not device readback and cannot detect external reprogramming. A .bit header holds",
        "  the build time, so payloads, not file hashes, are compared. See",
        "  `*/hw/tested_bitstream.json`.",
        "- I/O ports are false-path constrained (synchronized inputs, slow outputs), so slack covers",
        "  internal paths only.",
        "",
        "Limits: one board, one session and one PC; 100 MHz with no temperature variation; no",
        "formal equivalence. The hardware checks exercise each design through its handshake",
        "under the shaper's traffic; full temporal contracts (exact first-valid cycle, reset",
        "abort) remain covered by each run's independent testbench evidence.",
        "",
    ])


def _selected(args, table, require_one=False):
    if getattr(args, "design", None):
        if args.design not in table:
            raise SuiteError(f"unknown design {args.design!r}; choose from {', '.join(table)}")
        return [table[args.design]]
    if require_one:
        raise SuiteError("--design is required")
    return list(table.values())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=("verify", "sim", "build", "program", "hw", "all", "evidence"))
    parser.add_argument("--out", help="evidence: destination folder (must be new or empty)")
    parser.add_argument("--design")
    parser.add_argument("--bit", type=Path, help="program/hw: use this bitstream instead of build/<design>")
    parser.add_argument("--vivado", type=Path, default=DEFAULT_VIVADO)
    parser.add_argument("--port")
    parser.add_argument("--count", type=int, default=20000)
    parser.add_argument("--chunk", type=int, default=32)
    parser.add_argument("--restart-every", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=28)
    parser.add_argument("--wrong-model", action="store_true")
    args = parser.parse_args(argv)
    if args.bit and args.command not in ("program", "hw"):
        parser.error("--bit applies only to program and hw")
    table = design_table.load()
    try:
        {"verify": cmd_verify, "sim": cmd_sim, "build": cmd_build, "program": cmd_program,
         "hw": cmd_hw, "all": cmd_all, "evidence": cmd_evidence}[args.command](args, table)
    except (SuiteError, design_table.DesignError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0
