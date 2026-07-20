"""Vivado + xsim toolchain driver with the verification ladder's tool rungs.

Rules enforced here (defence #11): LLM output only ever lands in .v files;
all TCL is generated from these templates with sanitised paths. No model
string is ever interpolated into a TCL command.

Message severity promotion (never demotion) is applied from the taxonomy.
"""
from __future__ import annotations
import re
import subprocess
import time
from pathlib import Path
from .config import RunConfig
from .report_parser import VivadoMetrics, parse_sim_log, parse_all, extract_message_ids
from .triage import classify, FailureKind


def _tcl_path(p: Path) -> str:
    s = str(Path(p).resolve()).replace("\\", "/")
    if re.search(r"[\"'{}\[\]$;]", s):
        raise ValueError(f"unsafe path for TCL: {s}")
    return s


def _run(cmd: list[str], cwd: Path, timeout: int, log_path: Path) -> tuple[int, str]:
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout, cwd=str(cwd))
        out = (r.stdout or "") + "\n" + (r.stderr or "")
        log_path.write_text(out, errors="replace")
        return r.returncode, out
    except subprocess.TimeoutExpired:
        msg = f"timed out after {timeout}s"
        log_path.write_text(msg)
        return 124, msg
    except FileNotFoundError as e:
        msg = f"{cmd[0]} not found: {e}"
        log_path.write_text(msg)
        return 127, msg
    finally:
        _run.last_seconds = time.time() - t0
_run.last_seconds = 0.0


def promotion_tcl(promotions: dict[str, str]) -> str:
    """set_msg_config lines. We promote, we NEVER demote."""
    lines = []
    for mid, sev in promotions.items():
        if sev.upper() != "ERROR":
            continue  # promote-only policy
        lines.append(f"set_msg_config -id {{{mid}}} -new_severity ERROR")
    return "\n".join(lines)


# ---------------- Rung 2: xvlog compile check ----------------

def xvlog_check(files: list[Path], cfg: RunConfig, work_dir: Path,
                sv: bool = False) -> tuple[bool, str, FailureKind]:
    args = [cfg.xvlog_bin] + (["-sv"] if sv else []) + [str(f) for f in files]
    rc, out = _run(args, work_dir, 120, work_dir / "xvlog.log")
    if rc == 0:
        return True, "", FailureKind.DESIGN
    return False, _error_lines(out), classify(out)


# ---------------- Rung 3/4: xelab + xsim batch simulation ----------------

def xsim_run(design_files: list[Path], tb_file: Path, tb_top: str,
             cfg: RunConfig, work_dir: Path,
             timeout: int = 300) -> tuple[bool, str, FailureKind]:
    """Full batch sim without project creation: xvlog -> xelab -> xsim."""
    ok, err, kind = xvlog_check(design_files + [tb_file], cfg, work_dir)
    if not ok:
        return False, err, kind
    snap = f"{tb_top}_snap"
    rc, out = _run([cfg.xelab_bin, tb_top, "-s", snap, "--debug", "off"],
                   work_dir, timeout, work_dir / "xelab.log")
    if rc != 0:
        return False, _error_lines(out), classify(out)
    rc, out = _run([cfg.xsim_bin, snap, "-runall"],
                   work_dir, timeout, work_dir / "xsim.log")
    (work_dir / "sim_log.txt").write_text(out, errors="replace")
    passed, sim_err = parse_sim_log(work_dir / "sim_log.txt")
    if rc != 0 and passed:
        passed = False
        sim_err = sim_err or _error_lines(out)
    return passed, sim_err, classify(out) if not passed else FailureKind.DESIGN


# ---------------- Rung 5: synthesis + implementation ----------------

SYNTH_TCL = """\
{promotions}
set_part {part}
read_verilog {sources}
set fp [open "{workdir}/timing.xdc" w]
puts $fp "create_clock -period {period} -name clk [get_ports clk]"
close $fp
read_xdc "{workdir}/timing.xdc"
synth_design -top {top} -flatten_hierarchy rebuilt {extra_synth}
report_utilization -file "{workdir}/utilization.rpt"
report_timing_summary -file "{workdir}/timing.rpt"
opt_design
place_design
{phys_opt}
route_design
report_utilization -file "{workdir}/utilization_routed.rpt"
report_timing_summary -file "{workdir}/timing_routed.rpt"
report_design_analysis -logic_level_distribution -file "{workdir}/design_analysis.rpt"
report_power -file "{workdir}/power.rpt"
catch {{ report_methodology -file "{workdir}/methodology.rpt" }}
catch {{ report_qor_suggestions -file "{workdir}/qor_suggestions.rpt" }}
puts "SYNTH_COMPLETE"
"""


def run_synthesis(design_files: list[Path], top: str, cfg: RunConfig,
                  work_dir: Path, promotions: dict[str, str] | None = None,
                  retiming: bool = False, phys_opt: bool = False,
                  timeout: int = 900) -> tuple[bool, str, FailureKind]:
    tcl = SYNTH_TCL.format(
        promotions=promotion_tcl(promotions or {}),
        part=cfg.target_part,
        sources=" ".join(f'"{_tcl_path(f)}"' for f in design_files),
        workdir=_tcl_path(work_dir),
        period=f"{cfg.target_period_ns:.3f}",
        top=top,
        extra_synth="-retiming" if retiming else "",
        phys_opt="phys_opt_design" if phys_opt else "",
    )
    script = work_dir / "synth.tcl"
    script.write_text(tcl)
    rc, out = _run([cfg.vivado_bin, "-mode", "batch", "-source", _tcl_path(script),
                    "-nojournal", "-nolog"], work_dir, timeout,
                   work_dir / "vivado_synth_output.log")
    if rc != 0 or "SYNTH_COMPLETE" not in out:
        return False, _error_lines(out), classify(out)
    return True, "", FailureKind.DESIGN


def full_metrics(work_dir: Path) -> VivadoMetrics:
    return parse_all(work_dir)


def vivado_seconds() -> float:
    return _run.last_seconds


def message_ids_in(work_dir: Path) -> list[str]:
    ids = []
    for name in ("xvlog.log", "xelab.log", "xsim.log", "vivado_synth_output.log"):
        p = work_dir / name
        if p.exists():
            ids.extend(extract_message_ids(p.read_text(errors="replace")))
    return list(dict.fromkeys(ids))


def _error_lines(out: str) -> str:
    lines = [l.strip() for l in out.splitlines() if "ERROR" in l or "CRITICAL" in l]
    return "\n".join(lines[:15]) or out[-500:]


# ---------------- Planner advisory digest (advisory only, never blocking) ----

def advisor_digest(work_dir: Path, taxonomy=None, max_items: int = 8) -> str:
    """Digest methodology violations + QoR suggestions from a synthesised
    work dir into planner-facing text. Empty string when nothing found.

    catch{} in the TCL means these reports may be absent on older Vivado
    versions | absence is fine, the digest is simply empty.
    """
    from .report_parser import parse_methodology, parse_qor_suggestions
    parts: list[str] = []
    meth = parse_methodology(work_dir / "methodology.rpt")[:max_items]
    if meth:
        lines = []
        for rid, sev, desc in meth:
            advice = ""
            if taxonomy is not None:
                e = taxonomy.lookup_methodology(rid)
                if e:
                    advice = f" | plan: {e.get('advice', '')}"
                else:
                    taxonomy.log_unknown(rid)
            lines.append(f"- [{rid}] ({sev}) {desc}{advice}")
        parts.append("Methodology violations (advisory):\n" + "\n".join(lines))
    qor = parse_qor_suggestions(work_dir / "qor_suggestions.rpt", limit=max_items)
    if qor:
        parts.append("Vivado QoR suggestions (advisory):\n"
                     + "\n".join(f"- {q}" for q in qor))
    return "\n\n".join(parts)
