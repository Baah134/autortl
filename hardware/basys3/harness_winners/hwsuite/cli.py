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


def simulate(design, vivado: Path, out: Path, winner_path: Path) -> tuple[bool, str]:
    """Compile and run the generic testbench; return (passed, verdict line)."""
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    stimulus, expected = vectors.build(design.name, SIM_COUNT, SIM_RESTART)
    vectors.write(out, stimulus, expected)
    sources = [p.as_posix() for p in rtl_sources(design, winner_path)] + [(SUITE / "sim" / "tb_stream_shell.v").as_posix()]
    (out / "xvlog.opt").write_text("\n".join(sources) + "\n", encoding="ascii")
    generics = {"IN_BYTES": design.in_bytes, "OUT_BYTES": design.out_bytes,
                "N": SIM_COUNT, "RESTART_AT": SIM_RESTART, "CHUNK": SIM_CHUNK,
                "REQUIRE_OVERLAP": int(design.overlap)}
    (out / "xelab.opt").write_text("\n".join(
        ["tb_stream_shell", "-s", "snap", "-debug", "off"] +
        [f'-generic_top "{k}={v}"' for k, v in generics.items()]) + "\n", encoding="ascii")
    if _run([_tool(vivado, "xvlog"), "-f", "xvlog.opt"], out, out / "xvlog.txt"):
        return False, "FAIL: xvlog error (see xvlog.txt)"
    if _run([_tool(vivado, "xelab"), "-f", "xelab.opt"], out, out / "xelab.txt"):
        return False, "FAIL: xelab error (see xelab.txt)"
    warnings = _warnings(out / "xvlog.txt", out / "xelab.txt")
    if warnings:
        return False, "FAIL: compile warnings: " + "; ".join(warnings[:3])
    _run([_tool(vivado, "xsim"), "snap", "-R"], out, out / "xsim.txt")
    verdicts = [l for l in (out / "xsim.txt").read_text(encoding="utf-8", errors="replace").splitlines()
                if l.startswith(("PASS", "FAIL"))]
    verdict = verdicts[-1] if verdicts else "FAIL: no verdict (see xsim.txt)"
    return verdict.startswith("PASS"), verdict


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
        caught = not fault_ok and "compile" not in fault_verdict and "xvlog" not in fault_verdict
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
    bitstream for the wrong design fails the hardware check against the model.
    """
    return Path(args.bit) if getattr(args, "bit", None) else SUITE / "build" / design.name / "impl" / "stream_shell.bit"


def cmd_program(args, table):
    for design in _selected(args, table, require_one=True):
        out = SUITE / "build" / design.name / "impl"
        bit = _bitstream(args, design)
        if not bit.is_file():
            raise SuiteError(f"{design.name}: build first or pass --bit ({bit} missing)")
        out.mkdir(parents=True, exist_ok=True)
        cmd = [_tool(args.vivado, "vivado"), "-mode", "batch", "-nojournal", "-log", "program.log",
               "-source", (SUITE / "scripts" / "program.tcl").as_posix(), "-tclargs", bit.as_posix()]
        _programmed().unlink(missing_ok=True)       # the board's old image is gone either way
        code = _run(cmd, out, out / "program_console.txt")
        ok = "RESULT: programmed" in (out / "program_console.txt").read_text(errors="replace")
        print(f"{design.name:18} program exit {code}: {'programmed' if ok else 'FAILED'}")
        if code or not ok:
            raise SuiteError(f"{design.name}: programming failed")
        from . import reports
        _programmed().parent.mkdir(parents=True, exist_ok=True)
        _programmed().write_text(json.dumps({"design": design.name, "bitstream": bit.resolve().as_posix(),
                                          "payload_sha256": reports.bitstream_payload_sha256(bit)}, indent=2),
                              encoding="utf-8")


def _programmed() -> Path:
    """What `program` last loaded. The board holds one image, so this is suite-wide."""
    return SUITE / "build" / "programmed.json"


def _on_board(args, design) -> str:
    """Payload digest of the image on the board, from the last `program` record.

    Without a record (the board was programmed some other way) it falls back
    to the bitstream `hw` was pointed at, as before.
    """
    from . import reports
    bit = _bitstream(args, design)
    if not _programmed().is_file():
        if not bit.is_file():
            raise SuiteError(f"{design.name}: build and program first, or pass --bit ({bit} missing)")
        return reports.bitstream_payload_sha256(bit)
    record = json.loads(_programmed().read_text(encoding="utf-8"))
    if record["design"] != design.name:
        raise SuiteError(f"{design.name}: the board was last programmed with {record['design']}")
    if getattr(args, "bit", None) and reports.bitstream_payload_sha256(bit) != record["payload_sha256"]:
        raise SuiteError(f"{design.name}: --bit {bit} is not the image last programmed ({record['bitstream']})")
    return record["payload_sha256"]


def cmd_hw(args, table):
    from . import hw
    for design in _selected(args, table, require_one=True):
        payload = _on_board(args, design)
        report = hw.run(design, port=args.port, count=args.count, chunk=args.chunk,
                        restart_every=args.restart_every, wrong_model=args.wrong_model, seed=args.seed)
        # Identify what was on the board: the payload of the bitstream last programmed.
        report["bitstream_payload_sha256"] = payload
        print(hw.format_report(report))
        out = SUITE / "build" / design.name / "hw"
        out.mkdir(parents=True, exist_ok=True)
        tag = "wrong_model" if args.wrong_model else "model"
        (out / f"{tag}_{args.count}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        if report["passed"] == args.wrong_model:
            raise SuiteError(f"{design.name}: hardware check {'passed against the wrong model' if args.wrong_model else 'failed'}")


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
    "sim": ("xvlog.opt", "xelab.opt", "xvlog.txt", "xelab.txt", "xsim.txt", "stim.hex", "expect.hex"),
    "fault/sim": ("xvlog.txt", "xelab.txt", "xsim.txt"),
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
        sim_text = (src / "sim" / "xsim.txt").read_text(errors="replace")
        coverage = re.search(r"COVERAGE: (\d+) cycles with a result held under backpressure, (\d+) cycles", sim_text)
        hw_runs = {p.stem: json.loads(p.read_text()) for p in sorted((src / "hw").glob("*.json"))
                   if re.fullmatch(r"(model|wrong_model)_\d+", p.stem)}
        if not any(not r["wrong_model"] and r["passed"] for r in hw_runs.values()) or \
                not any(r["wrong_model"] and not r["passed"] for r in hw_runs.values()):
            raise SuiteError(f"{design.name}: needs a passing hardware run and a failing wrong-model run")
        bit = src / "impl" / "stream_shell.bit"
        payload = reports.bitstream_payload_sha256(bit)
        tested = {r.get("bitstream_payload_sha256") for r in hw_runs.values()}
        record = src / "hw" / "tested_bitstream.json"
        if None in tested and record.is_file():
            tested = (tested - {None}) | {json.loads(record.read_text())["payload_sha256"]}
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
        "- **Bitstreams**: `hardware_tested_this_payload` is true only when the archived bitstream's",
        "  configuration payload equals the one programmed for the hardware runs. A .bit header holds",
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
