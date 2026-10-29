"""Find the highest clock each harness winner closes timing at, two ways.

    python hardware/basys3/fmax/fmax.py run --out DIR [--design NAME] [--mode harness|ooc]
    python hardware/basys3/fmax/fmax.py summarize DIR

harness mode repeats the harness's own measurement (autortl/vivado.py,
SYNTH_TCL): the core is the top level, so its ports get I/O buffers, with
zero external input and output delay. Its slack therefore includes pad and
clock-tree delay, which is what the harness optimized against.

ooc mode synthesizes the core out of context: no I/O buffers, the clock
modeled as coming from a global buffer, and only register-to-register paths
timed. That is the speed the logic can run at inside a larger design.

Each attempt is a fresh in-memory project at one period (synthesis, opt,
place, route), run in one long-lived Vivado session. An attempt closes when
routed setup, hold and clock pulse-width slack are all >= 0 with no failing
endpoints. The search keeps a bracket between a closing and a failing period
and steers by each attempt's slack, so it reaches RESOLUTION_NS in a few
attempts (see `search`). Timing-driven implementation is not monotonic near
the edge, so the result is the fastest period that closed during the search,
not a proof that every slower period closes. Infrastructure failures are
retried once and never count as a timing result.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SUITE = REPO / "hardware" / "basys3" / "harness_winners"
PART = "xc7a35tcpg236-1"
VIVADO = Path("C:/AMDDesignTools/2025.2/Vivado/bin")
RESOLUTION_NS = 0.05
SLOWEST_NS, FASTEST_NS = 10.0, 2.0          # 100 MHz (the harness target) .. 500 MHz
INFRA = ("[Designutils 20-411]", "[Common 17-345]", "[Common 17-301]")

TCL = """\
catch {{close_project -quiet}}
create_project -in_memory -part {part}
read_verilog {{{sources}}}
set fp [open "{work}/timing.xdc" w]
puts $fp {{create_clock -period {period:.3f} -name clk [get_ports clk]}}
{ooc_clock}close $fp
read_xdc "{work}/timing.xdc"
synth_design -top {top} -flatten_hierarchy rebuilt {ooc}
{io_delays}opt_design
place_design
route_design
report_timing_summary -file "{work}/timing_routed.rpt"
report_timing -max_paths 1 -nworst 1 -path_type full -file "{work}/critical_path.rpt"
report_utilization -file "{work}/utilization_routed.rpt"
puts "FMAX_ATTEMPT_DONE"
"""
# The harness's zero-delay I/O constraints, as in autortl/vivado.py SYNTH_TCL.
IO_DELAYS = """\
set data_inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]
if {[llength $data_inputs] > 0} {set_input_delay -clock clk -max 0.000 $data_inputs; set_input_delay -clock clk -min 0.000 $data_inputs}
if {[llength [all_outputs]] > 0} {set_output_delay -clock clk -max 0.000 [all_outputs]; set_output_delay -clock clk -min 0.000 [all_outputs]}
"""
OOC_CLOCK = 'puts $fp {set_property HD.CLK_SRC BUFGCTRL_X0Y0 [get_ports clk]}\n'


class FmaxError(RuntimeError):
    pass


def tcl_script(sources, top, period, mode, work):
    if mode not in ("harness", "ooc"):
        raise FmaxError(f"unknown mode {mode}")
    for path in [*sources, work]:
        if not re.fullmatch(r"[A-Za-z0-9_:./ -]+", path.as_posix()):
            raise FmaxError(f"path unsafe for TCL: {path}")
    return TCL.format(part=PART, sources=" ".join(p.as_posix() for p in sources), work=work.as_posix(),
                      period=period, top=top, ooc="-mode out_of_context" if mode == "ooc" else "",
                      ooc_clock=OOC_CLOCK if mode == "ooc" else "", io_delays=IO_DELAYS if mode == "harness" else "")


def parse_timing_summary(text):
    """Setup, hold and pulse-width slack from report_timing_summary's design table."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith("WNS(ns)") and "WHS(ns)" in line and "WPWS(ns)" in line:
            values = lines[i + 2].split() if i + 2 < len(lines) else []
            if len(values) < 12:
                break
            try:
                wns, tns, tns_fail, _, whs, ths, ths_fail, _, wpws, tpws, tpws_fail, _ = values[:12]
                return {"wns_ns": float(wns), "tns_ns": float(tns), "setup_failing": int(tns_fail),
                        "whs_ns": float(whs), "ths_ns": float(ths), "hold_failing": int(ths_fail),
                        "wpws_ns": float(wpws), "tpws_ns": float(tpws), "pulse_width_failing": int(tpws_fail)}
            except ValueError:
                break
    raise FmaxError("no design timing summary table in report")


def parse_critical_path(text):
    """Start, end, logic levels and whether the worst path touches a pad."""
    def field(name):
        match = re.search(rf"^\s*{name}:\s+(\S+)", text, re.M)
        return match.group(1) if match else None
    levels = re.search(r"^\s*Logic Levels:\s+(\d+)\s*(?:\((.*)\))?", text, re.M)
    cells = (levels.group(2) or "") if levels else ""
    return {"source": field("Source"), "destination": field("Destination"),
            "logic_levels": int(levels.group(1)) if levels else None, "cells": cells,
            # Data-path pad cells only; the clock's own IBUF is not counted in Logic Levels.
            "through_pad": bool(re.search(r"\b(IBUF|OBUF)=", cells)),
            "path_type": classify_path(field("Source"), field("Destination"))}


def classify_path(source, destination):
    def is_pin(name):
        return name is not None and "/" not in name
    if is_pin(source) and is_pin(destination):
        return "input_to_output"
    if is_pin(source):
        return "input_to_register"
    if is_pin(destination):
        return "register_to_output"
    return "register_to_register"


def closes(timing):
    """Setup, hold and clock pulse width all met. Pulse width is the device's
    own limit (BUFG and flip-flop minimum periods); a design can meet setup
    above it and still not run."""
    return (timing["wns_ns"] >= 0 and timing["whs_ns"] >= 0 and timing["wpws_ns"] >= 0
            and timing["setup_failing"] == 0 and timing["hold_failing"] == 0
            and timing["pulse_width_failing"] == 0)


def predict(period, timing):
    """The period this attempt's setup slack suggests: slack is time to spare
    (or missing) on the worst path. Pulse-width slack is not used: those
    checks cover half a period or a fixed minimum, so they do not scale one
    for one; a pulse-width failure just tightens the bracket."""
    return period - timing["wns_ns"]


def search(attempt, slowest=SLOWEST_NS, fastest=FASTEST_NS, resolution=RESOLUTION_NS, limit=12):
    """Find the fastest closing period; attempt(period) -> timing dict.

    Keeps a bracket: `best` closed, `lo` failed (or is the search floor).
    Each next period is the slack prediction from the last attempt, pulled
    inside the bracket, or the bracket's midpoint if the prediction falls
    outside it. The search stops when the bracket is within one resolution
    step. The slowest period must close, or there is nothing to search.
    Every attempt is returned so the report shows the whole search.
    """
    tried = []

    def run(period):
        period = round(period, 3)
        result = attempt(period)
        tried.append({"period_ns": period, **result, "closes": closes(result)})
        return tried[-1]

    first = run(slowest)
    if not first["closes"]:
        return {"best_period_ns": None, "attempts": tried}
    best, lo, last = slowest, fastest, first
    while best - lo > resolution + 1e-9 and len(tried) < limit:
        steps = predict(last["period_ns"], last) / resolution
        # After a pass, probe at or just inside the prediction; after a fail,
        # just outside it. Either way the next attempt can close the bracket.
        guess = (math.floor(steps + 1e-9) if last["closes"] else math.ceil(steps - 1e-9)) * resolution
        guess = min(max(guess, lo + resolution), best - resolution)
        if not lo < guess < best:
            guess = round((best + lo) / 2 / resolution) * resolution
        if guess >= best - 1e-9 or guess <= lo + 1e-9:
            break
        last = run(guess)
        if last["closes"]:
            best = last["period_ns"]
        else:
            lo = last["period_ns"]
    return {"best_period_ns": round(best, 3), "attempts": tried, "bracket_ns": [round(lo, 3), round(best, 3)]}


class VivadoSession:
    """One long-lived `vivado -mode tcl`, fed scripts over stdin.

    Loading the part and starting Vivado cost most of a small design's run,
    so every attempt shares one session; each script starts a fresh
    in-memory project. A session that dies is restarted.
    """

    MARK = "@@FMAX_SCRIPT_END@@"

    def __init__(self, vivado=VIVADO, cwd=None):
        self.exe = next((p for p in (vivado / "vivado.bat", vivado / "vivado") if p.exists()), None)
        if self.exe is None:
            raise FmaxError(f"vivado not found in {vivado}")
        self.cwd = Path(cwd or REPO)
        self.proc = None
        self.count = 0

    def _start(self):
        self.cwd.mkdir(parents=True, exist_ok=True)
        self.proc = subprocess.Popen([str(self.exe), "-mode", "tcl", "-nojournal", "-log", "vivado_session.log"],
                                     cwd=self.cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")

    def run(self, script):
        """Source script; return its console text (empty if the session died)."""
        if self.proc is None or self.proc.poll() is not None:
            self._start()
        self.count += 1
        mark = f"{self.MARK}{self.count}"
        try:
            self.proc.stdin.write(f'catch {{source "{script.as_posix()}"}} fmax_error\n'
                                  f'puts "FMAX_TCL_ERROR: $fmax_error"\nputs "{mark}"\n')
            self.proc.stdin.flush()
        except OSError:
            self.proc = None
            return ""
        lines = []
        for line in self.proc.stdout:
            if line.rstrip() == mark:
                return "".join(lines)
            lines.append(line)
        self.proc = None                      # stdout closed: Vivado exited mid-script
        return "".join(lines)

    def close(self):
        if self.proc is not None and self.proc.poll() is None:
            try:
                self.proc.stdin.write("exit\n")
                self.proc.stdin.close()
                self.proc.wait(timeout=120)
            except (OSError, subprocess.TimeoutExpired):
                self.proc.kill()
        self.proc = None


def vivado_attempt(design, mode, out, session):
    """Return attempt(period) running one implementation in the shared session."""
    entry = json.loads((SUITE / "designs.json").read_text(encoding="utf-8"))[design]
    winner = REPO / entry["winner"]
    if hashlib.sha256(winner.read_bytes()).hexdigest() != entry["sha256"]:
        raise FmaxError(f"{design}: winner does not match its recorded SHA-256")

    def attempt(period):
        work = out / design / mode / f"p{period:.3f}"
        for retry in range(2):
            if work.exists():
                shutil.rmtree(work)
            work.mkdir(parents=True)
            script = work / "fmax.tcl"
            script.write_text(tcl_script([winner], entry["module"], period, mode, work), encoding="utf-8")
            text = session.run(script)
            (work / "vivado.log").write_text(text, encoding="utf-8", newline="\n")
            if "FMAX_ATTEMPT_DONE" in text:
                timing = parse_timing_summary((work / "timing_routed.rpt").read_text(errors="replace"))
                timing["critical_path"] = parse_critical_path((work / "critical_path.rpt").read_text(errors="replace"))
                return timing
            if retry == 0 and (not text or any(tag in text for tag in INFRA)):
                (work / "vivado.log").rename(work.parent / f"infra_attempt1_p{period:.3f}.log")
                continue
            raise FmaxError(f"{design} {mode} at {period} ns: Vivado failed; see {work / 'vivado.log'}")
    return attempt


def summarize(out):
    rows = {}
    for path in sorted(Path(out).glob("*/*/search.json")):
        result = json.loads(path.read_text(encoding="utf-8"))
        design, mode = path.parent.parent.name, path.parent.name
        best = result["best_period_ns"]
        at_best = next((a for a in result["attempts"] if a["period_ns"] == best), None)
        first = result["attempts"][0]
        rows.setdefault(design, {})[mode] = {
            "fmax_mhz": round(1000 / best, 1) if best else None, "best_period_ns": best,
            "wns_at_100mhz_ns": first["wns_ns"] if first["period_ns"] == SLOWEST_NS else None,
            "attempts": len(result["attempts"]),
            "critical_path_at_fmax": at_best["critical_path"] if at_best else None,
        }
    return rows


def markdown(rows):
    """The results table for a README, rendered from `summarize` output."""
    def cell(entry):
        if not entry or not entry["fmax_mhz"]:
            return "does not close", ""
        path = entry["critical_path_at_fmax"] or {}
        limit = f"{path.get('path_type', '?').replace('_', ' ')}, {path.get('logic_levels')} levels"
        if path.get("cells"):
            limit += f" ({path['cells']})"
        return f"{entry['fmax_mhz']:.1f} MHz ({entry['best_period_ns']:.2f} ns)", limit
    out = ["| Design | Harness flow Fmax | Its critical path | Out-of-context Fmax | Its critical path |",
           "|---|---:|---|---:|---|"]
    for design, modes in rows.items():
        h, hp = cell(modes.get("harness"))
        o, op = cell(modes.get("ooc"))
        out.append(f"| {design} | {h} | {hp} | {o} | {op} |")
    return "\n".join(out)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    run_p = sub.add_parser("run")
    run_p.add_argument("--out", type=Path, required=True)
    run_p.add_argument("--design", action="append")
    run_p.add_argument("--mode", action="append", choices=("harness", "ooc"))
    run_p.add_argument("--vivado", type=Path, default=VIVADO)
    sum_p = sub.add_parser("summarize")
    sum_p.add_argument("out", type=Path)
    sum_p.add_argument("--markdown", action="store_true", help="print the README results table instead of JSON")
    args = parser.parse_args(argv)
    if args.command == "summarize":
        rows = summarize(args.out)
        print(markdown(rows) if args.markdown else json.dumps(rows, indent=2))
        return 0
    designs = args.design or list(json.loads((SUITE / "designs.json").read_text(encoding="utf-8")))
    session = VivadoSession(args.vivado, cwd=args.out)
    try:
        for design in designs:
            for mode in args.mode or ("ooc", "harness"):
                target = args.out / design / mode / "search.json"
                if target.exists():
                    print(f"{design} {mode}: done earlier, skipping")
                    continue
                try:
                    result = search(vivado_attempt(design, mode, args.out, session))
                except FmaxError as error:
                    print(f"ERROR: {error}", file=sys.stderr)
                    return 1
                target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
                best = result["best_period_ns"]
                print(f"{design:18} {mode:8} fmax {1000 / best:6.1f} MHz ({best} ns) in {len(result['attempts'])} attempts"
                      if best else f"{design} {mode}: does not close at {SLOWEST_NS} ns", flush=True)
    finally:
        session.close()
    (args.out / "summary.json").write_text(json.dumps(summarize(args.out), indent=2) + "\n",
                                           encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
