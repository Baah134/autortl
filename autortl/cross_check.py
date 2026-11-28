"""Independent request traces: a second derivation that checks a planner-written spec.

Taxonomy: planner_spec_error_shared_by_oracle_and_rtl. For a prose request the
planner writes the typed spec, and the golden model, the generated testbench and
the RTL all derive from it, so a planner misreading of the request is verified
and accepted. A separate role call reads the ORIGINAL request and the module's
port list only (never the behavior text, latency, examples or the golden model)
and writes short cycle-by-cycle traces. The harness runs them through the
qualified golden model; a disagreement goes back to the planner once.

Trace row semantics are physical and independent of the spec's latency: row k
holds the inputs during clock cycle k and the outputs visible during cycle k,
after the inputs settle and before the rising edge that ends cycle k. Row 0 is
the first cycle after the harness's reset (or a resetless module's unchecked
initialization prefix). An input omitted from a row keeps its previous value
(0 in row 0; the reset port starts deasserted). The golden model's step i is
observed in physical cycle i + latency (the generated testbench's own
fixed_latency observation phase), so trace row k is compared with step k - latency
and rows before the latency are not compared.
"""
from __future__ import annotations

import json

from .spec import ModuleSpec, port_declaration

MAX_TRACES = 6
MAX_ROWS = 32
MAX_TOTAL_ROWS = 120
MAX_QUOTE = 300
# At most one planner repair per run comes from this check: the traces are an
# unverified second reading, so they may make the planner look again but never
# override its considered answer.
MAX_REPLANS = 1
FEEDBACK_MAX_CHARS = 1500


def skip_reason(module: ModuleSpec) -> str:
    """Why a module's traces cannot be compared ("" when they can)."""
    if module.compare_mode != "fixed_latency":
        return "scoreboard steps are transactions, not clock cycles"
    if not module.latency_known or type(module.latency) is not int:
        return "unknown numeric latency"
    if not data_outputs(module):
        return "no data outputs"
    return ""


def data_inputs(module: ModuleSpec) -> dict:
    return {p.name: p for p in module.ports
            if p.direction == "input" and p.name != "clk" and p.protocol == "none"}


def data_outputs(module: ModuleSpec) -> dict:
    return {p.name: p for p in module.ports if p.direction == "output" and p.protocol == "none"}


def interface_text(module: ModuleSpec) -> str:
    """The interface the trace writer sees: ports and reset only, no behavior."""
    lines = [f"module {module.name}"]
    lines += [f"  {port_declaration(p, include_direction=True)}" for p in module.ports]
    clocked = any(p.name == "clk" and p.direction == "input" for p in module.ports)
    lines.append("clock: " + ("rising edges of clk; one row per clock cycle" if clocked else
                              "none; each row is an independent combinational evaluation"))
    reset = module.reset
    if reset.present:
        level = 1 if reset.active_high else 0
        lines.append(f"reset: {reset.signal} ({reset.kind}, asserted when {reset.signal}={level}). The harness "
                     f"asserts it for {reset.duration_cycles} cycle(s) before row 0 and deasserts it in row 0. "
                     f"Rows may assert {reset.signal} again to check reset behavior.")
    elif module.init_rows():
        held = ", ".join(f"{k}={v}" for k, v in sorted(module.init_inputs.items())) or "all data inputs 0"
        lines.append(f"reset: none. Before row 0 the harness holds {held} (other data inputs 0) for "
                     f"{module.init_cycles} rising clock edge(s), unchecked.")
    else:
        lines.append("reset: none")
    lines.append("trace inputs may name: " + ", ".join(sorted(data_inputs(module))))
    lines.append("trace expected may name: " + ", ".join(sorted(data_outputs(module))))
    return "\n".join(lines)


def parse_traces(text: str, module: ModuleSpec) -> tuple[list[dict], list[str]]:
    """Validate a trace writer's JSON answer against the module interface.

    Returns the valid traces (normalized) and one error per rejected trace or
    structural problem. Untrusted text: only bounded integers and a quote survive.
    """
    errors = []
    start, end = text.find("{"), text.rfind("}")
    try:
        data = json.loads(text[start:end + 1]) if 0 <= start < end else None
    except ValueError as exc:
        return [], [f"answer is not JSON: {str(exc)[:200]}"]
    if not isinstance(data, dict) or not isinstance(data.get("traces"), list) or not data["traces"]:
        return [], ['answer must be one JSON object {"traces": [...]} with at least one trace']
    inputs, outputs = data_inputs(module), data_outputs(module)
    traces, total = [], 0
    for index, trace in enumerate(data["traces"][:MAX_TRACES]):
        label = f"trace {index}"
        if not isinstance(trace, dict) or not isinstance(trace.get("rows"), list) or not trace["rows"]:
            errors.append(f"{label}: needs a nonempty rows list")
            continue
        quote = trace.get("quote")
        if not isinstance(quote, str) or not quote.strip():
            errors.append(f"{label}: needs a quote of the request text it relies on")
            continue
        rows, problems, checked = [], [], 0
        if len(trace["rows"]) > MAX_ROWS:
            problems.append(f"at most {MAX_ROWS} rows")
        for number, row in enumerate(trace["rows"][:MAX_ROWS]):
            if not isinstance(row, dict) or set(row) - {"inputs", "expected"}:
                problems.append(f"row {number} must be an object with inputs and expected only")
                break
            given, expected = row.get("inputs", {}), row.get("expected", {})
            for mapping, ports, kind in ((given, inputs, "inputs"), (expected, outputs, "expected")):
                if not isinstance(mapping, dict):
                    problems.append(f"row {number} {kind} must be an object")
                    continue
                for name, value in mapping.items():
                    if name not in ports:
                        problems.append(f"row {number} {kind}: {name!r} is not one of {sorted(ports)}")
                    elif type(value) is not int or not 0 <= value < (1 << ports[name].width):
                        problems.append(f"row {number} {kind} {name} must be an integer in "
                                        f"0..{(1 << ports[name].width) - 1}")
            if problems:
                break
            checked += len(expected)
            rows.append({"inputs": dict(given), "expected": dict(expected)})
        if not problems and not checked:
            problems.append("no row has an expected output")
        if not problems and total + len(rows) > MAX_TOTAL_ROWS:
            problems.append(f"traces exceed {MAX_TOTAL_ROWS} rows in total")
        if problems:
            errors.append(f"{label}: " + "; ".join(problems[:3]))
            continue
        total += len(rows)
        traces.append({"index": index, "quote": quote.strip()[:MAX_QUOTE], "rows": rows})
    if len(data["traces"]) > MAX_TRACES:
        errors.append(f"only the first {MAX_TRACES} traces are used")
    return traces, errors


def stimulus(module: ModuleSpec, trace: dict) -> list[dict]:
    """Golden stimulus for one trace: the init prefix, then each row's held inputs."""
    current = {name: 0 for name in data_inputs(module)}
    if module.reset.present and module.reset.signal in current:
        current[module.reset.signal] = 0 if module.reset.active_high else 1
    rows = []
    for row in trace["rows"]:
        current.update(row["inputs"])
        rows.append(dict(current))
    return module.init_rows() + rows


def compare(module: ModuleSpec, trace: dict, outputs: list[dict]) -> tuple[list[dict], int]:
    """Mismatches of one trace against the golden outputs for stimulus(module, trace)."""
    offset = len(module.init_rows())
    mismatches, compared = [], 0
    for number, row in enumerate(trace["rows"]):
        step = number - module.latency
        if step < 0 or not row["expected"]:
            continue
        given = outputs[offset + step]
        for name, value in sorted(row["expected"].items()):
            compared += 1
            if given.get(name) != value:
                mismatches.append({"trace": trace["index"], "row": number, "port": name,
                                   "request_reading": value, "spec_model": given.get(name)})
    return mismatches, compared


def run_traces(golden, module: ModuleSpec, traces: list[dict]) -> tuple[list[dict], int]:
    """Run every trace through a qualified golden model; GoldenTimeoutError propagates."""
    mismatches, compared = [], 0
    for trace in traces:
        found, count = compare(module, trace, golden.run(stimulus(module, trace)))
        mismatches += found
        compared += count
    return mismatches, compared


def _compact(mapping: dict) -> str:
    return "{" + ", ".join(f"{k}={v}" for k, v in sorted(mapping.items())) + "}"


def feedback_text(module: ModuleSpec, traces: list[dict], mismatches: list[dict]) -> str:
    """Bounded planner feedback: each disagreeing trace up to its last mismatch row."""
    by_trace = {}
    for item in mismatches:
        by_trace.setdefault(item["trace"], []).append(item)
    lines = []
    for trace in traces:
        found = by_trace.get(trace["index"])
        if not found:
            continue
        last = max(item["row"] for item in found)
        lines.append(f"trace {trace['index']}, relying on the request text: \"{trace['quote']}\"")
        current = {}
        for number, row in enumerate(trace["rows"][:last + 1]):
            current.update(row["inputs"])
            wrong = [item for item in found if item["row"] == number]
            line = f"  row {number}: inputs {_compact(current)}"
            if wrong:
                line += (" -> request reading " + _compact({i["port"]: i["request_reading"] for i in wrong})
                         + ", spec model " + _compact({i["port"]: i["spec_model"] for i in wrong}))
            lines.append(line)
    text = "\n".join(lines)
    if len(text) > FEEDBACK_MAX_CHARS:
        text = text[:FEEDBACK_MAX_CHARS - 40].rsplit("\n", 1)[0] + "\n  [further rows truncated]"
    return text
