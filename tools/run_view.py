"""Static HTML view of AutoRTL runs: what each agent role did, and how each candidate fared.

Reads only the files a run already writes (events.jsonl, designs.jsonl,
run_summary.json, budget.json, config.json, contract.md, plan.md,
progress.md, iter_NNN/evaluation.md, candidate RTL, journal/*/completed.json
and, for build mode, modules/ and design_spec.json) and writes one
self-contained HTML file with no external resources.

    python tools/run_view.py <run-or-campaign-dir> [--out FILE]

Every string read from a run is untrusted (model output, RTL, tool logs) and
is HTML-escaped before it reaches the page. Large blocks are truncated.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime
import difflib
import hashlib
import html
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import role_report  # noqa: E402

MAX_LINES = 400          # lines shown per file, diff or model output
MAX_LINE_CHARS = 2000    # characters shown per line
MAX_ERROR_CHARS = 3000   # characters shown per error message
MINOR_CATEGORIES = {"decision", "cache", "proposal_feedback"}
METRICS = [("lut_used", "LUT", "count"), ("ff_used", "FF", "count"), ("wns_ns", "WNS ns", "slack"),
           ("whs_ns", "WHS ns", "slack"), ("reg2reg_wns_ns", "reg2reg WNS ns", "slack")]


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _clip(text: str, limit: int = MAX_ERROR_CHARS) -> str:
    text = str(text)
    return text if len(text) <= limit else text[:limit] + f"\n… ({len(text) - limit:,} more characters not shown)"


# ---------------------------------------------------------------- run data

def _time(event):
    """Seconds since the epoch from an optional event timestamp, else None."""
    for key in ("ts", "time", "timestamp", "t"):
        value = event.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
            except ValueError:
                continue
    return None


def _journal_dir(run: Path, identity: str) -> Path:
    return run / "journal" / hashlib.sha256(identity.encode()).hexdigest()


def _failed_attempt(run: Path, identity: str, attempt) -> str | None:
    """Logs the journal kept for an infrastructure-failed attempt, if any."""
    folder = _journal_dir(run, identity) / f"failed_attempt_{attempt}"
    if not folder.is_dir():
        return None
    parts = [f"== {path.name}\n{_read(path) or ''}" for path in sorted(folder.iterdir()) if path.is_file()]
    return "\n".join(parts) or None


def _journal(run: Path, identity: str):
    path = _journal_dir(run, identity) / "completed.json"
    if not path.is_file():
        return None
    data = role_report._json(path)
    return data.get("result") if isinstance(data, dict) and "result" in data else None


def describe_result(value):
    """(short summary, long text or None) for a journaled stage result."""
    if value is None:
        return "", None
    if isinstance(value, bool):
        return ("true" if value else "false"), None
    if isinstance(value, (int, float)):
        return (f"{value:.3g}" if isinstance(value, float) else str(value)), None
    if isinstance(value, str):
        first = value.strip().splitlines()[0] if value.strip() else ""
        if "\n" not in value.strip() and len(value) <= 120:
            return value, None
        return (first[:117] + "…" if len(first) > 120 else first), value
    if isinstance(value, dict) and "__kind" in value:
        kind, data = value.get("__kind"), value.get("value")
        if kind == "tuple" and isinstance(data, list):
            if len(data) == 3 and isinstance(data[0], bool):
                failure = data[2].get("value") if isinstance(data[2], dict) else data[2]
                message = str(data[1] or "")
                short = "passed" if data[0] else f"failed ({failure})"
                return short, (message or None)
            return "tuple", json.dumps(data, indent=2)
        if kind == "metrics" and isinstance(data, dict):
            parts = [f"{label} {data.get(key)}" for key, label, _ in METRICS[:3] if data.get(key) is not None]
            parts.append("sim passed" if data.get("sim_passed") else "sim failed")
            return " · ".join(parts), None
        if kind == "failure":
            return str(data), None
        if kind == "evaluation" and isinstance(data, dict):
            return str(data.get("recommendation") or "evaluation"), data.get("raw") or json.dumps(data, indent=2)
        return str(kind), json.dumps(data, indent=2)
    text = json.dumps(value, indent=2, ensure_ascii=False)
    compact = json.dumps(value, ensure_ascii=False)
    return (compact if len(compact) <= 120 else compact[:117] + "…"), (text if len(compact) > 120 else None)


def timeline(run: Path, events):
    """Stage attempts in order, grouped by scope, plus free-standing notes."""
    attempts, order, notes = {}, [], []
    for index, event in enumerate(events):
        stage = str(event.get("stage", ""))
        parts = stage.split(":")
        if len(parts) >= 4 and "attempt" in event:
            key = (stage, event.get("attempt", 1))
            if key not in attempts:
                scope, category, name, number = parts[0], parts[1], ":".join(parts[2:-1]), parts[-1]
                attempts[key] = {"stage": stage, "scope": scope, "category": category, "name": name,
                                 "index": number, "attempt": event.get("attempt", 1),
                                 "role": name.split(".")[0] if category == "model" else "",
                                 "outcome": "unfinished", "start": None, "end": None}
                order.append(key)
            record = attempts[key]
            if event.get("outcome") == "RUNNING":
                record["start"] = _time(event)
            else:
                record["outcome"] = str(event.get("outcome"))
                record["end"] = _time(event)
        else:
            scope = event.get("scope") or (f"iteration_{event['iteration']}" if "iteration" in event else "run")
            details = {k: event[k] for k in ("status", "failure_kind", "role", "error_code", "reason", "error")
                       if event.get(k) not in (None, "")}
            notes.append({"scope": str(scope), "stage": stage or "event", "outcome": str(event.get("outcome", "")),
                          "details": details, "position": index})
    stages = []
    for key in order:
        record = attempts[key]
        start, end = record.pop("start"), record.pop("end")
        record["duration"] = end - start if start is not None and end is not None and end >= start else None
        record["short"], record["long"] = ("", None)
        if record["outcome"] == "COMPLETE":
            record["short"], record["long"] = describe_result(_journal(run, record["stage"]))
        elif record["outcome"] != "unfinished":
            evidence = _failed_attempt(run, record["stage"], record["attempt"])
            if evidence:
                record["short"], record["long"] = "retained attempt logs", evidence
        stages.append(record)
    scopes = list(dict.fromkeys([s["scope"] for s in stages] + [n["scope"] for n in notes]))
    return {"scopes": scopes, "stages": stages, "notes": notes,
            "timed": any(s["duration"] is not None for s in stages)}


def _progress(run: Path):
    entries = {}
    text = _read(run / "progress.md") or ""
    for match in re.finditer(r"^## \[([^\]]+)\] iter (\d+) \| (\S+)\s*\n- (.*)$", text, re.MULTILINE):
        entries.setdefault(int(match.group(2)), []).append(
            {"ts": match.group(1), "outcome": match.group(3), "summary": match.group(4)})
    return entries


def _section(text: str, heading: str) -> str:
    match = re.search(r"^##\s*" + re.escape(heading) + r"\s*\n(.*?)(?=^##\s|\Z)", text, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _rtl_in(folder: Path, top: str):
    if not folder.is_dir():
        return None
    preferred = folder / f"{top}.v"
    if top and preferred.is_file():
        return preferred
    found = sorted(folder.glob("*.v"))
    return found[0] if found else None


def iterations(run: Path, designs, top: str):
    rows = {d.get("iteration"): d for d in designs if isinstance(d.get("iteration"), int)}
    on_disk = {int(p.name[5:]) for p in run.glob("iter_[0-9][0-9][0-9]") if p.is_dir()}
    progress = _progress(run)
    result = []
    for number in sorted((set(rows) | on_disk) - {0}):
        folder = run / f"iter_{number:03d}"
        row = rows.get(number, {})
        evaluation = _read(folder / "evaluation.md")
        verdict = row.get("recommendation") or (_section(evaluation, "Recommendation").split() or [None])[0] \
            if evaluation else row.get("recommendation")
        candidates = []
        for cand in sorted(folder.glob("cand_*")):
            candidates.append({"name": cand.name, "rtl": _rtl_in(cand, top)})
        result.append({"iteration": number, "row": row, "verdict": verdict, "evaluation": evaluation,
                       "reason": _section(evaluation or "", "Reason"), "candidates": candidates,
                       "progress": progress.get(number, []), "recorded": number in rows})
    return result


def rtl_pair(run: Path, summary, designs, top: str):
    """(baseline path, winner path, note) for the baseline and the promoted best."""
    baseline = _rtl_in(run / "iter_000", top)
    if baseline is None and (run / "inputs" / "design_path.v").is_file():
        baseline = run / "inputs" / "design_path.v"
    best = summary.get("best_iteration")
    if best is None:
        return baseline, None, "No verified best design was recorded for this run."
    if best == 0:
        return baseline, None, "Baseline retained: no candidate was promoted (best_iteration 0)."
    row = next((d for d in designs if d.get("iteration") == best), {})
    folder = run / f"iter_{best:03d}"
    cand_name = Path(str(row.get("artifact_dir") or "").replace("\\", "/")).name
    winner = _rtl_in(folder / cand_name, top) if cand_name.startswith("cand_") else None
    if winner is None:
        winner = next((r for r in (_rtl_in(c, top) for c in sorted(folder.glob("cand_*"))) if r), None)
    if winner is None and top and (run / f"{top}_best.v").is_file():
        winner = run / f"{top}_best.v"
    return baseline, winner, f"Promoted best: iteration {best}."


def build_modules(run: Path):
    folder = run / "modules"
    if not folder.is_dir():
        return []
    modules = []
    for path in sorted(p for p in folder.iterdir() if p.is_dir()):
        attempts = []
        for log in sorted(path.glob("golden_attempt_*.log"), key=lambda p: int(re.sub(r"\D", "", p.stem) or 0)):
            data = role_report._json(log)
            attempts.append({"file": log.name, "attempt": data.get("attempt"), "status": data.get("status"),
                             "diagnostic": data.get("diagnostic") or data.get("error") or ""})
        qualification = role_report._json(path / "tbqual" / "qualification.json")
        modules.append({"name": path.name, "rtl": path / f"{path.name}.v" if (path / f"{path.name}.v").is_file() else None,
                        "golden": path / "golden.py" if (path / "golden.py").is_file() else None,
                        "golden_attempts": attempts,
                        "qualification": qualification.get("status") or qualification.get("verdict") if qualification else None,
                        "candidates": sorted(p.name for p in path.glob("candidate_*") if p.is_dir())})
    return modules


def _gate_results(run: Path):
    """{entry: result} from the bench summary.json or entries.json beside a run."""
    for name in ("summary.json", "entries.json"):
        data = role_report._json(run.parent / name) if (run.parent / name).is_file() else None
        results = data.get("results") if isinstance(data, dict) else data
        if isinstance(results, list):
            return {r.get("entry"): r for r in results if isinstance(r, dict)}
    return {}


def collect(run: Path, root: Path):
    report = role_report.summarize(run)
    summary = role_report._json(run / "run_summary.json")
    config = role_report._json(run / "config.json")
    designs = role_report._jsonl(run / "designs.jsonl")
    events = role_report._jsonl(run / "events.jsonl")
    gate = _gate_results(run).get(run.name, {})
    gate_config = gate.get("config") if isinstance(gate.get("config"), dict) else {}
    spec_text = _read(run / "design_spec.json")
    try:
        spec = json.loads(spec_text) if spec_text else {}
    except ValueError:
        spec = {}
    top = (summary.get("top_module") or config.get("top_module") or gate_config.get("top_module")
           or (spec.get("top_name") if isinstance(spec, dict) else None) or "")
    try:
        label = run.relative_to(root).as_posix() if run != root else run.name
    except ValueError:
        label = run.name
    baseline, winner, rtl_note = rtl_pair(run, summary, designs, top)
    base_row = next((d for d in designs if d.get("iteration") == 0), None) or summary.get("baseline_metrics") or {}
    return {"label": label or run.name, "run": run, "report": report, "summary": summary, "config": config,
            "gate": gate, "top": top, "model": config.get("model") or gate_config.get("model"),
            "mode": config.get("mode") or gate_config.get("mode"),
            "objective": config.get("objective") or gate_config.get("objective"),
            "part": config.get("target_part") or gate_config.get("target_part"),
            "freq": config.get("target_freq_mhz") or gate_config.get("target_freq_mhz"),
            "budget": role_report._json(run / "budget.json"), "baseline_metrics": base_row,
            "iterations": iterations(run, designs, top), "timeline": timeline(run, events),
            "baseline_rtl": baseline, "winner_rtl": winner, "rtl_note": rtl_note,
            "modules": build_modules(run), "spec": spec_text,
            "contract": _read(run / "contract.md"), "plan": _read(run / "plan.md")}


def campaigns(found, root: Path):
    """Bench summaries (tier, pass count) for each folder that holds runs."""
    result = []
    for parent in dict.fromkeys(run.parent for run in found):
        data = role_report._json(parent / "summary.json") if (parent / "summary.json").is_file() else {}
        if not isinstance(data, dict) or "results" not in data:
            continue
        identity = data.get("runtime_identity") or {}
        try:
            label = parent.relative_to(root).as_posix() if parent != root else parent.name
        except ValueError:
            label = parent.name
        result.append({"label": label or parent.name, "tier": data.get("tier"), "passed": data.get("passed"),
                       "total": data.get("total"), "ts": data.get("ts"), "model": identity.get("model_identity"),
                       "qualified": data.get("qualified"), "held": data.get("held")})
    return result


# ---------------------------------------------------------------- rendering

def _fmt(value, digits=3):
    if value is None or value == "":
        return "—"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:.{digits}f}".rstrip("0").rstrip(".") if abs(value) < 1e6 else f"{value:,.0f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def _duration(seconds):
    if seconds is None:
        return "—"
    if seconds < 60:
        return f"{seconds:.1f} s"
    minutes, rest = divmod(int(round(seconds)), 60)
    return f"{minutes // 60} h {minutes % 60:02d} m" if minutes >= 60 else f"{minutes} m {rest:02d} s"


def _tone(value: str) -> str:
    value = str(value or "").upper()
    if value in ("DONE", "ACCEPT", "COMPLETE", "PASSED", "TRUE", "OK"):
        return "good"
    if value in ("BASELINE", ""):
        return "neutral"
    if value in ("REJECT", "INVESTIGATE", "UNFINISHED"):
        return "warn"
    return "bad"


def badge(text, tone=None) -> str:
    return f'<span class="badge {tone or _tone(text)}">{esc(text)}</span>'


def text_block(text, limit=MAX_LINES, label="lines") -> str:
    if text is None:
        return '<p class="muted">Not recorded.</p>'
    lines = str(text).splitlines()
    shown = [line if len(line) <= MAX_LINE_CHARS else line[:MAX_LINE_CHARS] + " …" for line in lines[:limit]]
    note = (f'<p class="note">Showing the first {limit} of {len(lines):,} {label}.</p>'
            if len(lines) > limit else "")
    return f"<pre>{esc(chr(10).join(shown))}</pre>{note}"


def file_block(path) -> str:
    return text_block(_read(path)) if path else '<p class="muted">Not recorded.</p>'


def diff_block(before, after, before_name="baseline", after_name="candidate") -> str:
    if before is None or after is None:
        return '<p class="muted">Both files are needed for a diff.</p>'
    lines = list(difflib.unified_diff(before.splitlines(), after.splitlines(), before_name, after_name,
                                      lineterm="", n=3))
    if not lines:
        return '<p class="muted">No textual difference.</p>'
    out = []
    for line in lines[:MAX_LINES]:
        line = line if len(line) <= MAX_LINE_CHARS else line[:MAX_LINE_CHARS] + " …"
        kind = ("hunk" if line.startswith("@@") else "head" if line.startswith(("+++", "---"))
                else "add" if line.startswith("+") else "del" if line.startswith("-") else "ctx")
        out.append(f'<span class="d-{kind}">{esc(line)}</span>')
    note = (f'<p class="note">Showing the first {MAX_LINES} of {len(lines):,} diff lines.</p>'
            if len(lines) > MAX_LINES else "")
    added = sum(1 for l in lines if l.startswith("+") and not l.startswith("+++"))
    removed = sum(1 for l in lines if l.startswith("-") and not l.startswith("---"))
    return (f'<p class="muted">{added} lines added, {removed} removed.</p>'
            f'<pre class="diff">{chr(10).join(out)}</pre>{note}')


def details(summary_html: str, body: str, open_=False, cls="") -> str:
    return (f'<details class="{cls}"{" open" if open_ else ""}><summary>{summary_html}</summary>'
            f'<div class="details-body">{body}</div></details>')


def table(headers, rows, numeric=(), cls="") -> str:
    head = "".join(f'<th class="{"num" if i in numeric else ""}">{esc(h)}</th>' for i, h in enumerate(headers))
    body = []
    for row in rows:
        cells, row_cls = (row["cells"], row.get("cls", "")) if isinstance(row, dict) else (row, "")
        body.append(f'<tr class="{row_cls}">' + "".join(
            f'<td class="{"num" if i in numeric else ""}">{c}</td>' for i, c in enumerate(cells)) + "</tr>")
    return f'<div class="scroll"><table class="{cls}"><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def _tokens(budget):
    tokens = budget.get("tokens") or {}
    if not tokens:
        return "—"
    cached = tokens.get("cached_input_tokens")
    text = f"{tokens.get('input_tokens', 0):,} in / {tokens.get('output_tokens', 0):,} out"
    return text + (f" ({cached:,} cached)" if cached else "")


def _delta(value, base, kind):
    if not isinstance(value, (int, float)) or not isinstance(base, (int, float)) or isinstance(value, bool):
        return esc(_fmt(value))
    change = value - base
    if kind == "count":
        tone = "good" if change < 0 else "bad" if change > 0 else "neutral"
        sign = f"{change:+,}" if isinstance(change, int) else f"{change:+.3f}"
        return f'{esc(_fmt(value))} <span class="delta {tone}">{esc(sign if change else "±0")}</span>'
    tone = "bad" if value < 0 else ""
    return f'<span class="{tone}">{esc(_fmt(value))}</span>'


def metrics_table(data) -> str:
    base = data["baseline_metrics"] or {}
    headers = ["Iteration", "Verdict", "Sim"] + [label for _, label, _ in METRICS] + ["Timing met", "Best", "Error"]
    has_r2r = any(r["row"].get("reg2reg_wns_ns") is not None for r in data["iterations"]) or \
        base.get("reg2reg_wns_ns") is not None
    if not has_r2r:
        headers.remove("reg2reg WNS ns")
    metrics = [m for m in METRICS if has_r2r or m[0] != "reg2reg_wns_ns"]
    rows = []
    if base:
        rows.append({"cls": "baseline", "cells": [esc("0 (baseline)"), badge("BASELINE"), esc(_fmt(base.get("sim_passed")))]
                     + [esc(_fmt(base.get(k))) for k, _, _ in metrics]
                     + [esc(_fmt(base.get("timing_met"))), esc("yes" if data["summary"].get("best_iteration") == 0 else ""),
                        esc(_first_error(base))]})
    for item in data["iterations"]:
        row = item["row"]
        rows.append([f'<a href="#{data["anchor"]}-iter-{item["iteration"]}">{esc(item["iteration"])}</a>',
                     badge(item["verdict"] or ("not recorded" if not item["recorded"] else "—"),
                           None if item["verdict"] else "warn"),
                     esc(_fmt(row.get("sim_passed")))]
                    + [_delta(row.get(k), base.get(k), kind) for k, _, kind in metrics]
                    + [esc(_fmt(row.get("timing_met"))), esc("yes" if row.get("is_best") else ""),
                       esc(_first_error(row))])
    numeric = set(range(3, 3 + len(metrics)))
    return table(headers, rows, numeric=numeric, cls="metrics")


def _first_error(row):
    error = row.get("sim_error") or row.get("synth_error") or ""
    return error.strip().splitlines()[0][:160] if str(error).strip() else ""


def render_facts(data) -> str:
    summary, budget, report = data["summary"], data["budget"], data["report"]
    gate = data["gate"]
    facts = [("Status", badge(report["status"])),
             ("Failure kind", esc(summary.get("failure_kind") or "—")),
             ("Mode", esc(data["mode"] or "—")), ("Top module", f'<code>{esc(data["top"] or "—")}</code>'),
             ("Model", esc(data["model"] or "—")), ("Objective", esc(data["objective"] or "—")),
             ("Target", esc(" @ ".join(x for x in (data["part"], f"{_fmt(data['freq'])} MHz" if data["freq"] else "") if x) or "—")),
             ("Model calls", esc(_fmt(budget.get("llm_calls")))), ("Tokens", esc(_tokens(budget))),
             ("Vivado time", esc(_duration(budget.get("vivado_seconds")))),
             ("Wall time", esc(_duration(budget.get("elapsed")))),
             ("Best iteration", esc(_fmt(summary.get("best_iteration")))),
             ("Improvement", esc(summary.get("improvement_kind") or "—"))]
    if gate:
        facts.append(("Bench gate", badge("passed" if gate.get("ok") else "failed") +
                      (f' <span class="muted">{esc(gate.get("reason"))}</span>' if gate.get("reason") else "")))
    items = "".join(f"<div><dt>{esc(k)}</dt><dd>{v}</dd></div>" for k, v in facts)
    errors = "".join(f'<pre class="error">{esc(_clip(e))}</pre>' for e in report["errors"])
    return f'<dl class="facts">{items}</dl>' + (f"<h4>Errors</h4>{errors}" if errors else "")


def render_roles(data) -> str:
    roles = data["report"]["roles"]
    if not roles:
        return '<p class="muted">No model calls were recorded.</p>'
    rows = [[f'{badge(m.split(".")[0], "role-" + m.split(".")[0])} <code>{esc(m)}</code>', esc(c["completed"]),
             esc(c["unfinished"]) if not c["unfinished"] else f'<span class="bad">{esc(c["unfinished"])}</span>',
             esc(c["retries"])] for m, c in roles.items()]
    return table(["Role method", "Completed", "Unfinished", "Retries"], rows, numeric={1, 2, 3})


def render_iterations(data) -> str:
    if not data["iterations"] and not data["baseline_metrics"]:
        return '<p class="muted">No iterations were recorded.</p>'
    parts = [metrics_table(data)]
    base_text = _read(data["baseline_rtl"]) if data["baseline_rtl"] else None
    for item in data["iterations"]:
        body = []
        for note in item["progress"]:
            body.append(f'<p><span class="muted">{esc(note["ts"])}</span> {badge(note["outcome"])} '
                        f'<span class="muted">planner instruction:</span> {esc(note["summary"])}</p>')
        if item["reason"]:
            body.append(f'<blockquote><strong>Evaluator reason.</strong> {esc(_clip(item["reason"], 1200))}</blockquote>')
        body.append(details("Evaluator report <code>evaluation.md</code>", text_block(item["evaluation"])))
        for cand in item["candidates"]:
            name = cand["rtl"].name if cand["rtl"] else "no RTL"
            cand_text = _read(cand["rtl"]) if cand["rtl"] else None
            body.append(details(f'Candidate <code>{esc(cand["name"])}/{esc(name)}</code>: diff against the baseline',
                                diff_block(base_text, cand_text, "baseline", f'{cand["name"]}/{name}')))
            body.append(details(f'Candidate <code>{esc(cand["name"])}/{esc(name)}</code>: full source',
                                text_block(cand_text)))
        if not item["candidates"]:
            body.append('<p class="muted">No candidate folder on disk.</p>')
        title = (f'Iteration {esc(item["iteration"])} {badge(item["verdict"] or "not recorded", None if item["verdict"] else "warn")}'
                 + (' <span class="badge good">best</span>' if item["row"].get("is_best") else ""))
        parts.append(f'<div id="{data["anchor"]}-iter-{item["iteration"]}">' + details(title, "".join(body), cls="iter") + "</div>")
    return "".join(parts)


def render_rtl(data) -> str:
    base, win = data["baseline_rtl"], data["winner_rtl"]
    base_text = _read(base) if base else None
    out = [f'<p>{esc(data["rtl_note"])}</p>']
    if win:
        out.append(details(f'Diff: baseline <code>{esc(base.name if base else "?")}</code> → winner <code>{esc(win.parent.name)}/{esc(win.name)}</code>',
                           diff_block(base_text, _read(win), "baseline", "winner"), open_=True))
        out.append('<div class="pair">' + details("Baseline RTL", text_block(base_text)) +
                   details("Winning RTL", file_block(win)) + "</div>")
    else:
        out.append(details(f'Baseline RTL <code>{esc(base.name if base else "not recorded")}</code>', text_block(base_text)))
    return "".join(out)


def _result_cell(stage) -> str:
    if stage["long"]:
        return details(esc(stage["short"] or "output"), text_block(stage["long"]), cls="inline")
    return esc(stage["short"])


def render_repairs(data) -> str:
    repair_methods = role_report.REPAIR_METHODS
    stages = [s for s in data["timeline"]["stages"] if s["category"] == "model" and s["name"] in repair_methods]
    out = []
    counts = data["report"]["repairs"]
    if counts:
        out.append("<p>" + " · ".join(f"{esc(k)}: <strong>{esc(v)}</strong>" for k, v in counts.items()) + "</p>")
    if stages:
        rows = [[esc(s["scope"]), f'<code>{esc(s["name"])}</code>', esc(f'#{s["index"]}'), esc(s["attempt"]),
                 badge(s["outcome"]), _result_cell(s)] for s in stages]
        out.append(table(["Scope", "Role method", "Call", "Attempt", "Outcome", "Result"], rows, numeric={2, 3}))
    golden = [(m["name"], a) for m in data["modules"] for a in m["golden_attempts"]]
    if golden:
        rows = [[f'<code>{esc(name)}</code>', esc(_fmt(a["attempt"])), badge(a["status"] or "unknown"),
                 f'<code class="wrap">{esc(_clip(a["diagnostic"], 400))}</code>'] for name, a in golden]
        out.append("<h4>Golden-model attempts</h4>" + table(["Module", "Attempt", "Status", "Diagnostic"], rows, numeric={1}))
    return "".join(out) or '<p class="muted">No repairs, golden-model attempts or spec attempts.</p>'


def render_modules(data) -> str:
    if not data["modules"] and not data["spec"]:
        return ""
    out = []
    if data["spec"]:
        out.append(details("Planner build spec <code>design_spec.json</code>", text_block(data["spec"])))
    for module in data["modules"]:
        bits = []
        if module["qualification"]:
            bits.append(f'<p>Testbench qualification: {badge(module["qualification"])}</p>')
        if module["candidates"]:
            bits.append(f'<p class="muted">Candidates: {esc(", ".join(module["candidates"]))}</p>')
        bits.append(details("Accepted module RTL", file_block(module["rtl"])))
        if module["golden"]:
            bits.append(details("Golden model <code>golden.py</code>", file_block(module["golden"])))
        out.append(details(f'Module <code>{esc(module["name"])}</code>', "".join(bits)))
    return "<h3>Build modules</h3>" + "".join(out)


def render_timeline(data) -> str:
    tl = data["timeline"]
    if not tl["stages"] and not tl["notes"]:
        return '<p class="muted">No events were recorded.</p>'
    out = []
    if not tl["timed"]:
        out.append('<p class="muted">events.jsonl carries no timestamps, so stage durations are not available; '
                   'start/end pairing still marks unfinished attempts.</p>')
    for scope in tl["scopes"]:
        stages = [s for s in tl["stages"] if s["scope"] == scope]
        notes = [n for n in tl["notes"] if n["scope"] == scope]
        rows = []
        for s in stages:
            category = s["category"]
            label = (f'{badge(s["role"], "role-" + s["role"])} <code>{esc(s["name"])}</code>' if category == "model"
                     else f'<code>{esc(s["name"])}</code>')
            result = _result_cell(s)
            rows.append({"cls": "minor" if category in MINOR_CATEGORIES else "",
                         "cells": [f'<span class="cat cat-{esc(category)}">{esc(category)}</span>', label,
                                   esc(s["index"]), esc(s["attempt"]), badge(s["outcome"]),
                                   esc(_duration(s["duration"])), result]})
        for n in notes:
            text = "; ".join(f"{k}: {v}" for k, v in n["details"].items() if k != "error")
            error = n["details"].get("error")
            rows.append({"cls": "note-row", "cells": [
                '<span class="cat cat-note">event</span>', f'<code>{esc(n["stage"])}</code>', "", "",
                badge(n["outcome"] or "event"), "—",
                esc(text) + (f'<pre class="error">{esc(_clip(error, 800))}</pre>' if error else "")]})
        unfinished = sum(s["outcome"] == "unfinished" for s in stages)
        failed = sum(s["outcome"] not in ("COMPLETE", "unfinished") for s in stages)
        model = sum(s["category"] == "model" for s in stages)
        flags = (f' {badge(f"{unfinished} unfinished", "warn")}' if unfinished else "") + \
                (f' {badge(f"{failed} failed", "bad")}' if failed else "")
        title = f'<code>{esc(scope)}</code> <span class="muted">{len(stages)} stages, {model} model calls</span>{flags}'
        out.append(details(title, table(["Kind", "Stage", "Call", "Attempt", "Outcome", "Duration", "Result"],
                                        rows, numeric={2, 3}, cls="timeline"), cls="scope"))
    return "".join(out)


def render_run(data) -> str:
    report = data["report"]
    anchor = data["anchor"]
    blocks = [f'<section class="run" id="{anchor}">',
              f'<h2>{esc(data["label"])} {badge(report["status"])}</h2>',
              render_facts(data),
              "<h3>Role calls</h3>", render_roles(data),
              "<h3>Iterations</h3>", render_iterations(data),
              "<h3>RTL: baseline and winner</h3>", render_rtl(data),
              "<h3>Repairs</h3>", render_repairs(data),
              render_modules(data),
              "<h3>Timeline</h3>", render_timeline(data)]
    extra = []
    if data["plan"] is not None:
        extra.append(details("Latest planner plan <code>plan.md</code>", text_block(data["plan"])))
    if data["contract"] is not None:
        extra.append(details("Fixed contract <code>contract.md</code>", text_block(data["contract"])))
    if extra:
        blocks += ["<h3>Plan and contract</h3>"] + extra
    blocks.append('<p class="top-link"><a href="#top">Back to top</a></p></section>')
    return "".join(blocks)


def render_campaign(runs_data, groups) -> str:
    out = ['<section class="campaign"><h2>Campaign summary</h2>']
    for g in groups:
        out.append(f'<p><code>{esc(g["label"])}</code>: tier {esc(_fmt(g["tier"]))}, '
                   f'<strong>{esc(_fmt(g["passed"]))} / {esc(_fmt(g["total"]))}</strong> entries passed'
                   + (f', model {esc(g["model"])}' if g["model"] else "")
                   + (f', qualified {esc(_fmt(g["qualified"]))}' if g["qualified"] is not None else "")
                   + (f' <span class="muted">({esc(g["ts"])})</span>' if g["ts"] else "") + "</p>")
    rows = []
    for d in runs_data:
        r, budget = d["report"], d["budget"]
        verdicts = ", ".join(f"{k} {v}" for k, v in sorted(r["verdicts"].items())) or "—"
        repairs = ", ".join(f"{k} {v}" for k, v in r["repairs"].items() if v) or "—"
        gate = d["gate"]
        rows.append([f'<a href="#{d["anchor"]}">{esc(d["label"])}</a>', badge(r["status"]),
                     esc(d["summary"].get("failure_kind") or "—"), esc(d["model"] or "—"),
                     esc(_fmt(budget.get("llm_calls"))), esc(_tokens(budget)),
                     esc(_fmt(r["baseline_lut"])), esc(_fmt(r["best_lut"])), esc(_fmt(r["best_iteration"])),
                     esc(verdicts), esc(repairs),
                     badge("passed" if gate.get("ok") else "failed") if gate else "—"])
    out.append(table(["Run", "Status", "Failure kind", "Model", "Calls", "Tokens", "Baseline LUT", "Best LUT",
                      "Best iter", "Evaluator verdicts", "Repairs", "Bench gate"], rows, numeric={4, 6, 7, 8}))
    out.append("</section>")
    return "".join(out)


STYLE = """
:root{--bg:#fbfbfa;--panel:#ffffff;--text:#1d2125;--muted:#5f6b76;--line:#e2e5e8;--code:#f3f4f6;
--accent:#2457a6;--good:#1f7a45;--good-bg:#e6f4ec;--warn:#8a5a00;--warn-bg:#fbf1dc;--bad:#b42318;--bad-bg:#fdebea;
--neutral-bg:#eef0f2;--add:#e6f4ec;--del:#fdebea;--hunk:#e8eefb;
--planner:#6b3fa0;--generator:#1f6f8b;--evaluator:#8a5a00;--doctor:#a03f5c}
@media (prefers-color-scheme: dark){:root{--bg:#15181b;--panel:#1c2024;--text:#e4e7ea;--muted:#9aa5b1;
--line:#30363d;--code:#23282d;--accent:#7fa7e8;--good:#6fcf97;--good-bg:#173524;--warn:#e3b55b;--warn-bg:#3a2f15;
--bad:#f28b82;--bad-bg:#3d1d1b;--neutral-bg:#2a3036;--add:#17331f;--del:#3a1c1b;--hunk:#1d2a40;
--planner:#c3a3ee;--generator:#79c6e0;--evaluator:#e3b55b;--doctor:#ef9ab4}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:1180px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:1.6rem;margin:0 0 4px}h2{font-size:1.3rem;margin:0 0 12px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
h3{font-size:1.05rem;margin:28px 0 8px;padding-bottom:4px;border-bottom:1px solid var(--line)}h4{margin:16px 0 6px;font-size:.95rem}
a{color:var(--accent)}code,pre{font-family:ui-monospace,"Cascadia Mono",Consolas,Menlo,monospace;font-size:.86em}
code{background:var(--code);padding:1px 4px;border-radius:4px}code.wrap{white-space:pre-wrap;word-break:break-word}
pre{background:var(--code);border:1px solid var(--line);border-radius:6px;padding:10px 12px;overflow:auto;max-height:70vh;margin:6px 0;line-height:1.4}
pre.error{white-space:pre-wrap;word-break:break-word;border-color:var(--bad);max-height:18em}
.muted{color:var(--muted)}.note{color:var(--warn);font-size:.88em;margin:2px 0 8px}
header.page{margin-bottom:20px}.controls{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
button{font:inherit;font-size:.85rem;padding:4px 10px;border:1px solid var(--line);border-radius:6px;background:var(--panel);color:var(--text);cursor:pointer}
section.run,section.campaign{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:18px 18px 8px;margin:0 0 24px}
.badge{display:inline-block;padding:0 8px;border-radius:999px;font-size:.78rem;font-weight:600;line-height:1.7;background:var(--neutral-bg);color:var(--text);white-space:nowrap}
.badge.good{background:var(--good-bg);color:var(--good)}.badge.warn{background:var(--warn-bg);color:var(--warn)}.badge.bad{background:var(--bad-bg);color:var(--bad)}
.badge.role-planner{color:var(--planner)}.badge.role-generator{color:var(--generator)}.badge.role-evaluator{color:var(--evaluator)}.badge.role-doctor{color:var(--doctor)}
.good{color:var(--good)}.bad{color:var(--bad)}
.delta{font-size:.8em;margin-left:4px}.delta.neutral{color:var(--muted)}
dl.facts{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:8px 16px;margin:0}
dl.facts div{min-width:0}dt{font-size:.76rem;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}dd{margin:0;overflow-wrap:anywhere}
.scroll{overflow-x:auto;margin:6px 0 10px}
table{border-collapse:collapse;width:100%;font-size:.9rem}
th,td{text-align:left;padding:5px 8px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-size:.78rem;text-transform:uppercase;letter-spacing:.03em;color:var(--muted);white-space:nowrap}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
tr.baseline td{background:var(--neutral-bg)}tr.minor td{color:var(--muted)}tr.note-row td{background:var(--warn-bg)}
body.hide-minor tr.minor{display:none}
.cat{font-size:.75rem;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}.cat-model{color:var(--accent);font-weight:600}.cat-tool{color:var(--good)}.cat-note{color:var(--warn)}
details{border:1px solid var(--line);border-radius:8px;margin:8px 0;background:var(--panel)}
details>summary{cursor:pointer;padding:7px 12px;list-style-position:inside}
details[open]>summary{border-bottom:1px solid var(--line)}
.details-body{padding:4px 12px 8px;min-width:0}
details.inline{border:none;margin:0;background:transparent}details.inline>summary{padding:0}details.inline[open]>summary{border:none}details.inline .details-body{padding:4px 0}
blockquote{margin:8px 0;padding:6px 12px;border-left:3px solid var(--evaluator);background:var(--code);border-radius:0 6px 6px 0}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:12px}.pair>details{min-width:0}
pre.diff span{display:block}.d-add{background:var(--add)}.d-del{background:var(--del)}.d-hunk{background:var(--hunk);color:var(--muted)}.d-head{color:var(--muted)}
.top-link{text-align:right;font-size:.85rem}
@media (max-width:720px){main{padding:16px 16px 48px}.pair{grid-template-columns:1fr}section.run,section.campaign{padding:14px 12px 6px}body{font-size:14px}}
"""

SCRIPT = """document.querySelectorAll('.controls').forEach(function(c){c.hidden=false;});
document.querySelectorAll('[data-act]').forEach(function(b){b.addEventListener('click',function(){
var a=b.getAttribute('data-act');if(a==='minor'){var on=document.body.classList.toggle('hide-minor');
b.textContent=on?'Show harness decisions':'Hide harness decisions';return;}
document.querySelectorAll('details').forEach(function(d){d.open=(a==='open');});});});"""


def render_page(runs_data, groups, title) -> str:
    digest = base64.b64encode(hashlib.sha256(SCRIPT.encode()).digest()).decode()
    csp = f"default-src 'none'; style-src 'unsafe-inline'; script-src 'sha256-{digest}'; img-src data:"
    multiple = len(runs_data) > 1
    intro = (f"{len(runs_data)} runs" if multiple else "1 run") + \
        ". Read from the run files; every value comes from the harness's own records."
    nav = ""
    if multiple:
        nav = render_campaign(runs_data, groups)
    body = "".join(render_run(d) for d in runs_data)
    return ("<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            f"<meta http-equiv=\"Content-Security-Policy\" content=\"{esc(csp)}\">"
            "<meta name=\"referrer\" content=\"no-referrer\">"
            f"<title>{esc('AutoRTL run view: ' + title)}</title><style>{STYLE}</style></head>"
            f"<body><main id=\"top\"><header class=\"page\"><h1>AutoRTL run view: {esc(title)}</h1>"
            f"<p class=\"muted\">{esc(intro)} Roles: planner, generator, evaluator, timing doctor; "
            "deterministic gates decide promotion.</p>"
            "<div class=\"controls\" hidden><button type=\"button\" data-act=\"open\">Expand all</button>"
            "<button type=\"button\" data-act=\"close\">Collapse all</button>"
            "<button type=\"button\" data-act=\"minor\">Hide harness decisions</button></div></header>"
            f"{nav}{body}</main><script>{SCRIPT}</script></body></html>\n")


def build(path) -> str:
    root = Path(path)
    found = role_report.runs([root])
    if not found:
        raise FileNotFoundError(f"no runs found under {root}")
    runs_data = []
    for number, run in enumerate(found, 1):
        data = collect(run, root)
        data["anchor"] = f"run-{number}"
        runs_data.append(data)
    name = root.resolve()
    title = f"{name.parent.name}/{name.name}" if name.name in ("run", "runs") and name.parent.name else name.name
    return render_page(runs_data, campaigns(found, root), title)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("path", help="a run folder, or a campaign folder holding run folders")
    parser.add_argument("--out", help="output HTML file (default: <path>/run-view.html)")
    args = parser.parse_args(argv)
    try:
        page = build(args.path)
    except FileNotFoundError as error:
        print(error, file=sys.stderr)
        return 1
    out = Path(args.out) if args.out else Path(args.path) / "run-view.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
