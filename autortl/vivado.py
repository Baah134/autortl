"""Vivado + xsim toolchain driver with the verification ladder's tool rungs.

Rules enforced here (defence #11): LLM output only ever lands in .v files;
all TCL is generated from these templates with sanitised paths. No model
string is ever interpolated into a TCL command.

Message severity promotion (never demotion) is applied from the taxonomy.
"""
from __future__ import annotations
import re
import json
import hashlib
import os
import signal
import subprocess
import time
from pathlib import Path
from .config import RunConfig
from .state import atomic_write_text
from .report_parser import VivadoMetrics, parse_sim_log, parse_all, extract_message_ids
from .triage import classify, FailureKind


def _tcl_path(p: Path) -> str:
    s = str(Path(p).resolve()).replace("\\", "/")
    if re.search(r"[\"'{}\[\]$;]", s):
        raise ValueError(f"unsafe path for TCL: {s}")
    return s


def _output_text(value) -> str:
    # TimeoutExpired can contain bytes even when Popen is in text mode.
    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value or ""


def _merge_output(previous, current) -> str:
    previous, current = _output_text(previous), _output_text(current)
    # communicate after a timeout normally returns the entire captured stream.
    return current if current.startswith(previous) else previous + current


def _stop_tool(process: subprocess.Popen, stdout="", stderr="") -> tuple[str, str]:
    """Stop only our process tree and drain it within bounded cleanup deadlines."""
    notes = []
    try:
        if os.name == "nt":
            result = subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                                    capture_output=True, timeout=10, shell=False)
            if result.returncode:
                notes.append("process-tree cleanup failed: " + _output_text(result.stderr))
        else:
            # _run launches a private session; this group contains only our job.
            os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except (OSError, subprocess.TimeoutExpired) as exc:
        notes.append(f"process-tree cleanup failed: {exc}")
    if process.poll() is None:
        try:
            process.kill()
        except OSError as exc:
            notes.append(f"launcher cleanup failed: {exc}")
    try:
        final_stdout, final_stderr = process.communicate(timeout=5)
        stdout = _merge_output(stdout, final_stdout)
        stderr = _merge_output(stderr, final_stderr)
    except subprocess.TimeoutExpired as exc:
        stdout = _merge_output(stdout, exc.output)
        stderr = _merge_output(stderr, exc.stderr)
        notes.append("process cleanup timed out; output may be incomplete")
        # On Windows communicate uses reader threads. Closing a pipe here can
        # block on their read lock if a surviving descendant still owns it.
        if os.name != "nt":
            for stream in (process.stdout, process.stderr):
                if stream is not None:
                    stream.close()
        try:
            process.wait(timeout=5)
        except (OSError, subprocess.TimeoutExpired) as wait_error:
            notes.append(f"launcher could not be reaped: {wait_error}")
    return _output_text(stdout), _output_text(stderr) + "\n" + "\n".join(notes)


def _append_tool_exit_record(cwd: Path, record: dict) -> None:
    """Durably retain every invocation without recording arguments or output."""
    path = Path(cwd) / "tool_exit_records.log"
    previous = path.read_text(encoding="utf-8") if path.exists() else ""
    separator = "\n" if previous and not previous.endswith("\n") else ""
    atomic_write_text(path, previous + separator + json.dumps(record, sort_keys=True,
                                                             allow_nan=False) + "\n")


def _run(cmd: list[str], cwd: Path, timeout: int, log_path: Path) -> tuple[int, str]:
    t0 = time.monotonic()
    process, primary_error = None, None
    status, driver_rc, log_written = "launch_failed", None, False
    try:
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       text=True, encoding="utf-8", errors="replace",
                                       cwd=str(cwd), shell=False,
                                       start_new_session=os.name != "nt")
        except OSError as exc:
            driver_rc = 127 if isinstance(exc, FileNotFoundError) else 126
            msg = f"{cmd[0]} {'not found' if driver_rc == 127 else 'could not launch'}: {exc}"
            log_path.write_text(msg, encoding="utf-8", errors="replace")
            log_written = True
            return driver_rc, msg
        except BaseException:
            status = "cancelled"
            raise
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            status = "exited"
            # A mocked, missing or malformed process code cannot become zero.
            driver_rc = process.returncode if type(process.returncode) is int else 126
        except subprocess.TimeoutExpired as exc:
            status, driver_rc = "timed_out", 124
            stdout, stderr = _stop_tool(process, exc.output, exc.stderr)
            stderr += f"\ntimed out after {timeout}s"
        except BaseException as cancelled:
            status, driver_rc = "cancelled", None
            try:
                stdout, stderr = _stop_tool(process)
                log_path.write_text(stdout + "\n" + stderr + "\nTool execution cancelled",
                                    encoding="utf-8", errors="replace")
                log_written = True
            except BaseException as cleanup_error:
                cancelled.add_note("Tool cancellation cleanup failed: " + type(cleanup_error).__name__)
            raise
        out = _output_text(stdout) + "\n" + _output_text(stderr)
        log_path.write_text(out, encoding="utf-8", errors="replace")
        log_written = True
        return driver_rc, out
    except BaseException as exc:
        primary_error = exc
        raise
    finally:
        _run.last_seconds = max(0.0, time.monotonic() - t0)
        try:
            actual_rc = getattr(process, "returncode", None)
            pid = getattr(process, "pid", None)
            executable = str(cmd[0])
            basename = executable.replace("\\", "/").rsplit("/", 1)[-1].lower()
            tool = re.sub(r"\.(?:exe|bat|cmd)$", "", basename)
            record = {"schema_version": 1, "tool": tool, "executable": executable,
                      "cwd": str(Path(cwd).resolve()),
                      "pid": pid if type(pid) is int and pid > 0 else None,
                      "status": status,
                      "returncode": actual_rc if type(actual_rc) is int else None,
                      "driver_returncode": driver_rc, "elapsed_seconds": _run.last_seconds,
                      "output_log_path": str(Path(log_path).resolve()),
                      "output_log_sha256": hashlib.sha256(log_path.read_bytes()).hexdigest()
                                           if log_written else None}
            _append_tool_exit_record(cwd, record)
        except BaseException as receipt_error:
            if primary_error is None:
                raise
            primary_error.add_note("Tool exit receipt could not be saved: " + type(receipt_error).__name__)
_run.last_seconds = 0.0


def promotion_tcl(promotions: dict[str, str]) -> str:
    """set_msg_config lines. We promote, we NEVER demote."""
    lines = []
    for mid, sev in promotions.items():
        if sev.upper() != "ERROR":
            continue  # promote-only policy
        lines.append(f"set_msg_config -id {{{mid}}} -new_severity ERROR")
    return "\n".join(lines)


def _duplicate_module_error(output: str) -> str:
    """These tool diagnostics mean a source replaced another module definition."""
    pattern = r"\[(?:VRFC\s+10-3609|Synth\s+8-9873)\]"
    lines = [line.strip()[:1000] for line in output.splitlines() if re.search(pattern, line)]
    return "\n".join(lines[:8])


# ---------------- Rung 2: xvlog compile check ----------------

def xvlog_check(files: list[Path], cfg: RunConfig, work_dir: Path,
                sv: bool = False, timeout: float = 120) -> tuple[bool, str, FailureKind]:
    args = [cfg.xvlog_bin] + (["-sv"] if sv else []) + [str(f) for f in files]
    rc, out = _run(args, work_dir, timeout, work_dir / "xvlog.log")
    kind = classify(out)
    if rc != 0 and kind == FailureKind.INFRA:
        return False, _error_lines(out), kind
    duplicate = _duplicate_module_error(out)
    if duplicate:
        return False, duplicate, FailureKind.DESIGN
    if rc == 0:
        return True, "", FailureKind.DESIGN
    return False, _error_lines(out), kind


# ---------------- Rung 3/4: xelab + xsim batch simulation ----------------

def xsim_run(design_files: list[Path], tb_file: Path, tb_top: str,
             cfg: RunConfig, work_dir: Path,
             timeout: int = 300) -> tuple[bool, str, FailureKind]:
    """Full batch sim with one deadline across xvlog -> xelab -> xsim."""
    deadline = time.monotonic() + timeout
    if timeout <= 0:
        return False, "timed out after 0s", FailureKind.INFRA
    ok, err, kind = xvlog_check(design_files + [tb_file], cfg, work_dir,
                                timeout=min(120, timeout))
    if not ok:
        return False, err, kind
    snap = f"{tb_top}_snap"
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        return False, f"timed out after {timeout}s", FailureKind.INFRA
    rc, out = _run([cfg.xelab_bin, tb_top, "-s", snap, "--debug", "off"],
                   work_dir, remaining, work_dir / "xelab.log")
    if rc != 0:
        return False, _error_lines(out), classify(out)
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        return False, f"timed out after {timeout}s", FailureKind.INFRA
    rc, out = _run([cfg.xsim_bin, snap, "-runall"],
                   work_dir, remaining, work_dir / "xsim.log")
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
puts $fp {{create_clock -period {period} -name clk [get_ports clk]}}
close $fp
read_xdc "{workdir}/timing.xdc"
synth_design -top {top} -flatten_hierarchy rebuilt {extra_synth}
set fp [open "{workdir}/timing_io.tcl" w]
puts $fp {{set data_inputs [get_ports -filter {{DIRECTION == IN && NAME != clk}}]}}
puts $fp {{if {{[llength $data_inputs] > 0}} {{set_input_delay -clock clk -max 0.000 $data_inputs; set_input_delay -clock clk -min 0.000 $data_inputs}}}}
puts $fp {{if {{[llength [all_outputs]] > 0}} {{set_output_delay -clock clk -max 0.000 [all_outputs]; set_output_delay -clock clk -min 0.000 [all_outputs]}}}}
close $fp
source "{workdir}/timing_io.tcl"
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
                  timeout: int = 900, hold_fix: bool = False) -> tuple[bool, str, FailureKind]:
    tcl = SYNTH_TCL.format(
        promotions=promotion_tcl(promotions or {}),
        part=cfg.target_part,
        sources=" ".join(f'"{_tcl_path(f)}"' for f in design_files),
        workdir=_tcl_path(work_dir),
        period=f"{cfg.target_period_ns:.3f}",
        top=top,
        extra_synth="-retiming" if retiming else "",
        phys_opt="phys_opt_design -hold_fix" if hold_fix else ("phys_opt_design" if phys_opt else ""),
    )
    script = work_dir / "synth.tcl"
    script.write_text(tcl)
    rc, out = _run([cfg.vivado_bin, "-mode", "batch", "-source", _tcl_path(script),
                    "-nojournal", "-nolog"], work_dir, timeout,
                   work_dir / "vivado_synth_output.log")
    kind = classify(out)
    if rc != 0 and kind == FailureKind.INFRA:
        return False, _error_lines(out), kind
    duplicate = _duplicate_module_error(out)
    if duplicate:
        return False, duplicate, FailureKind.DESIGN
    if rc != 0 or "SYNTH_COMPLETE" not in out:
        return False, _error_lines(out), kind
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
