"""Synthesise sealed, functionally passing submissions and seal their PPA metrics (ROADMAP B3).

    python -m benchmark.ppa measure --attempt DIR --vivado PATH [--arms single_call full]
    python -m benchmark.ppa verify  --attempt DIR

Every arm goes through the same harness flow: `autortl.vivado.run_synthesis`
with the out-of-context template, one part and one clock period (FLOW). The
flow, its template hash and the Vivado version are written into every record,
so the paired report (`benchmark.ppa_report`) can refuse records that were not
measured the same way.

Gates, in order (each refusal is an exception, never a recorded design result):
- the submission must load as a sealed artifact under the trusted receipt ID in
  the cell's run.json (no unsealed, edited or substituted RTL);
- it must be a candidate (a missing-output record has no RTL);
- its graded verdict must be an upstream pass for that same receipt: a
  functionally failing design has no PPA.

A design that passes function but fails synthesis is a real outcome: it is
sealed with status `synth_failed`. Infrastructure failures (Vivado license,
crash, timeout) raise PpaInfraError, write no record and never count as a
result; the partial work directory is kept and moved aside on the next run.
Metrics come only from the routed reports of the requested part; a missing or
mismatched report is a harness error, not a zero.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

from autortl.fileio import read_json

from . import artifacts

SCHEMA = 1
FLOW = {"implementation": "out_of_context", "part": "xc7a35tcpg236-1", "period_ns": 10.0}
ARMS = ("single_call", "full")
REPORTS = ("utilization_routed.rpt", "timing_routed.rpt")
OPTIONAL_REPORTS = ("no_timing_paths.txt",)
RECORD = "ppa.json"
STATUSES = ("measured", "synth_failed")
METRIC_KEYS = ("lut", "ff", "dsp", "bram", "wns_ns", "whs_ns", "timing_met", "no_timing_paths")


class PpaError(ValueError):
    """A submission may not be measured, or its reports cannot be trusted."""


class PpaInfraError(RuntimeError):
    """Vivado did not run to a verdict (license, crash, timeout); never a result."""


# ----------------------------------------------------------------- helpers
def _canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _cell_name(cell: dict) -> str:
    return f"{cell['task']}-{cell['arm']}-{cell['trial']}"


def template_sha256(implementation: str = FLOW["implementation"]) -> str:
    """Hash of the harness TCL template the flow runs (pinned by tests/test_ooc_flow.py)."""
    from autortl import vivado
    return hashlib.sha256(vivado.TEMPLATES[implementation].encode("utf-8")).hexdigest()


def flow_identity(flow: dict | None = None) -> dict:
    flow = dict(FLOW if flow is None else flow)
    if set(flow) != set(FLOW):
        raise PpaError(f"flow must name exactly {sorted(FLOW)}")
    if flow["implementation"] != "out_of_context":
        raise PpaError("B3 measures every arm out of context")
    period = flow["period_ns"]
    if type(period) not in (int, float) or not 0 < period < 1000:
        raise PpaError("period_ns must be a positive number of nanoseconds")
    flow["period_ns"] = float(period)
    return dict(flow, template_sha256=template_sha256(flow["implementation"]))


def _header(text: str, field: str) -> str | None:
    for line in text.splitlines()[:20]:
        stripped = line.strip().lstrip("|").strip()
        if stripped.startswith(field):
            name, _, value = stripped.partition(":")
            if name.strip() == field:
                return value.strip()
    return None


# ---------------------------------------------------------------- parsing
def parse_reports(work: Path, top: str, part: str) -> dict:
    """LUT, FF, DSP, BRAM, WNS, WHS from the routed reports of one OOC run.

    Refuses (PpaError) a report that is missing, not routed, for another design
    or part, or without a parsed LUT row or timing summary: never a silent zero.
    """
    from autortl.report_parser import VivadoMetrics, apply_no_timing_paths, parse_timing, parse_utilization

    work = Path(work)
    for name in REPORTS:
        if not (work / name).is_file():
            raise PpaError(f"{name} is missing; only routed reports are measured")
    util_text = (work / "utilization_routed.rpt").read_text(encoding="utf-8", errors="replace")
    timing_text = (work / "timing_routed.rpt").read_text(encoding="utf-8", errors="replace")
    for name, text in (("utilization_routed.rpt", util_text), ("timing_routed.rpt", timing_text)):
        if _header(text, "Design State") != "Routed":
            raise PpaError(f"{name} is not a routed report")
        if _header(text, "Design") != top:
            raise PpaError(f"{name} reports design {_header(text, 'Design')!r}, not {top!r}")
    if _header(util_text, "Device") != part:
        raise PpaError(f"utilization_routed.rpt is for {_header(util_text, 'Device')!r}, not {part!r}")
    m = VivadoMetrics()
    parse_utilization(work / "utilization_routed.rpt", m)
    if m.lut_total <= 0 or m.ff_total <= 0:
        raise PpaError("utilization_routed.rpt has no parsable LUT/register row")
    parse_timing(work / "timing_routed.rpt", m)
    marker = work / "no_timing_paths.txt"
    no_paths = marker.is_file()
    apply_no_timing_paths(marker, m)
    if m.wns_ns == -999.0 or m.whs_ns == -999.0:
        raise PpaError("timing_routed.rpt has no WNS/WHS and Vivado left no no-timing-paths marker")
    return {"lut": m.lut_used, "ff": m.ff_used, "dsp": m.dsp_used, "bram": m.bram_used,
            "wns_ns": m.wns_ns, "whs_ns": m.whs_ns, "timing_met": bool(m.timing_met),
            "no_timing_paths": no_paths, "tool_version": _header(util_text, "Tool Version")}


# --------------------------------------------------------------- measuring
def _load_submission(run_dir: Path) -> tuple[dict, dict]:
    run_dir = Path(run_dir)
    record_path = run_dir / "run.json"
    if not record_path.is_file():
        raise PpaError(f"{run_dir.name}: cell is not sealed (no run.json)")
    record = read_json(record_path)
    try:
        receipt = artifacts.load_artifact(run_dir / "submission", expected_id=record["receipt_id"])
    except (artifacts.ArtifactError, KeyError) as exc:
        raise PpaError(f"{run_dir.name}: submission is not a sealed artifact: {exc}") from exc
    return record, receipt


def _check_verdict(verdict: dict, receipt: dict) -> None:
    if verdict.get("receipt_id") != receipt["id"]:
        raise PpaError("verdict belongs to a different submission")
    if verdict.get("cell") is not None and verdict["cell"] != {k: receipt["cell"][k] for k in ("task", "trial", "arm")}:
        raise PpaError("verdict belongs to a different cell")
    if verdict.get("upstream_pass") is not True:
        raise PpaError("functionally failing design: no PPA is measured")


def measure(run_dir: Path, verdict: dict, out: Path, *, vivado_bin: str, flow: dict | None = None,
            timeout: int = 1800, synthesize=None, read_metrics=parse_reports) -> dict:
    """Synthesise one sealed, passing submission; seal and return its PPA record.

    `out` must not exist. `synthesize` defaults to autortl.vivado.run_synthesis
    (injected in tests); `read_metrics` to parse_reports.
    """
    from autortl.config import RunConfig
    from autortl.triage import FailureKind

    if synthesize is None:
        from autortl.vivado import run_synthesis as synthesize
    identity = flow_identity(flow)
    record, receipt = _load_submission(run_dir)
    if receipt["kind"] != "candidate":
        raise PpaError("missing-output record: there is no design to synthesise")
    _check_verdict(verdict, receipt)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    work, sources = out / "work", out / "work" / "src"
    sources.mkdir(parents=True)
    files = []
    for entry in receipt["files"]:
        target = sources / entry["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path(run_dir) / "submission" / entry["path"], target)
        if _sha256(target) != entry["sha256"]:
            raise PpaError(f"{entry['path']} changed while copying")
        files.append(target)
    period = identity["period_ns"]
    cfg = RunConfig(mode="build", implementation=identity["implementation"], target_part=identity["part"],
                    target_freq_mhz=1000.0 / period, vivado_bin=vivado_bin)
    ok, error, kind = synthesize(files, receipt["top"], cfg, work, timeout=timeout)
    # INFRA and UNKNOWN are not final for their inputs (autortl.triage): retry later.
    if not ok and kind in (FailureKind.INFRA, FailureKind.UNKNOWN):
        raise PpaInfraError(f"{_cell_name(receipt['cell'])}: {error.strip()[:300]}")
    payload = {"schema": SCHEMA, "kind": "ppa", "cell": {k: receipt["cell"][k] for k in ("task", "arm", "trial")},
               "receipt_id": receipt["id"], "top": receipt["top"],
               "verdict_sha256": hashlib.sha256(_canonical(verdict)).hexdigest(),
               "flow": identity, "status": None, "failure_kind": None, "failure": None,
               "metrics": None, "tool_version": None, "reports": []}
    if ok:
        metrics = read_metrics(work, receipt["top"], identity["part"])
        payload["tool_version"] = metrics.pop("tool_version", None)
        payload["status"], payload["metrics"] = "measured", metrics
    else:
        payload["status"], payload["failure_kind"] = "synth_failed", getattr(kind, "value", str(kind))
        payload["failure"] = error.strip()[:2000]
    for name in REPORTS + OPTIONAL_REPORTS:
        if (work / name).is_file():
            payload["reports"].append({"path": f"work/{name}", "sha256": _sha256(work / name)})
    return _seal(out, payload)


def _seal(out: Path, payload: dict) -> dict:
    payload = json.loads(_canonical(payload))
    payload["id"] = hashlib.sha256(_canonical(payload)).hexdigest()
    _validate(payload)
    pending = out / (RECORD + ".pending")
    with pending.open("xb") as stream:
        stream.write(_canonical(payload) + b"\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(pending, out / RECORD)
    return load_record(out)


def _validate(record: dict) -> None:
    keys = {"schema", "kind", "cell", "receipt_id", "top", "verdict_sha256", "flow", "status",
            "failure_kind", "failure", "metrics", "tool_version", "reports", "id"}
    if type(record) is not dict or set(record) != keys:
        raise PpaError("malformed PPA record")
    if record["schema"] != SCHEMA or record["kind"] != "ppa":
        raise PpaError("unknown PPA record schema")
    if record["status"] not in STATUSES:
        raise PpaError("unknown PPA status")
    if record["status"] == "measured":
        if type(record["metrics"]) is not dict or set(record["metrics"]) != set(METRIC_KEYS):
            raise PpaError("measured record lacks metrics")
    elif record["metrics"] is not None:
        raise PpaError("a synthesis failure carries no metrics")


def load_record(out: Path) -> dict:
    """Load a sealed record and verify its identity and every report hash."""
    path = Path(out) / RECORD
    if not path.is_file():
        raise PpaError(f"{Path(out).name}: no sealed PPA record")
    record = json.loads(path.read_bytes())
    _validate(record)
    if record["id"] != hashlib.sha256(_canonical({k: v for k, v in record.items() if k != "id"})).hexdigest():
        raise PpaError(f"{Path(out).name}: PPA record identity mismatch")
    for entry in record["reports"]:
        if _sha256(Path(out) / entry["path"]) != entry["sha256"]:
            raise PpaError(f"{Path(out).name}: {entry['path']} changed after sealing")
    return record


# ------------------------------------------------------------- attempt-wide
def _set_aside(out: Path) -> None:
    """An unsealed directory is an infrastructure leftover: keep it, never reuse it."""
    k = 1
    while (aside := out.with_name(f"{out.name}.infra-{k}")).exists():
        k += 1
    out.rename(aside)


def measure_attempt(attempt: Path, *, vivado_bin: str, arms=ARMS, flow: dict | None = None,
                    timeout: int = 1800, synthesize=None, read_metrics=parse_reports, log=print) -> dict:
    """Measure every graded upstream-passing cell of `arms`; skip sealed ones.

    Returns {"measured": [...], "infra": [...], "skipped_failing": n}. Infra
    failures leave the cell unmeasured for a later run.
    """
    attempt = Path(attempt)
    rows = read_json(attempt / "grades" / "summary.json")
    root = attempt / "ppa"
    root.mkdir(exist_ok=True)
    done, infra, failing = [], [], 0
    for row in rows:
        if row["arm"] not in arms:
            continue
        if not row["upstream_pass"]:
            failing += 1
            continue
        name = f"{row['task']}-{row['arm']}-{row['trial']}"
        out = root / name
        if (out / RECORD).is_file():
            done.append(load_record(out))
            continue
        if out.exists():
            _set_aside(out)
        verdict = read_json(attempt / "grades" / name / "verdict.json")
        try:
            done.append(measure(attempt / "runs" / name, verdict, out, vivado_bin=vivado_bin, flow=flow,
                                timeout=timeout, synthesize=synthesize, read_metrics=read_metrics))
            log(f"{name}: {done[-1]['status']}")
        except PpaInfraError as exc:
            infra.append(name)
            log(f"{name}: infrastructure, not measured: {exc}")
    return {"measured": done, "infra": infra, "skipped_failing": failing}


def collect(attempt: Path) -> list[dict]:
    """Every sealed record under attempt/ppa, verified, ordered by cell."""
    root = Path(attempt) / "ppa"
    return [load_record(d) for d in sorted(root.iterdir())
            if d.is_dir() and (d / RECORD).is_file()] if root.is_dir() else []


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="python -m benchmark.ppa")
    sub = p.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("measure")
    m.add_argument("--attempt", required=True, type=Path)
    m.add_argument("--vivado", required=True, help="absolute path of vivado(.bat); see run.py doctor")
    m.add_argument("--arms", nargs="+", default=list(ARMS), choices=list(ARMS))
    m.add_argument("--timeout", type=int, default=1800)
    v = sub.add_parser("verify")
    v.add_argument("--attempt", required=True, type=Path)
    a = p.parse_args(argv)
    if a.cmd == "measure":
        result = measure_attempt(a.attempt, vivado_bin=a.vivado, arms=tuple(a.arms), timeout=a.timeout)
        print(json.dumps({"sealed": len(result["measured"]), "infra": result["infra"],
                          "skipped_failing": result["skipped_failing"]}, indent=1))
        return 1 if result["infra"] else 0
    records = collect(a.attempt)
    print(json.dumps({"verified": len(records)}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
