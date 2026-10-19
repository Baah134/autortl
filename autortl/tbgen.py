"""Testbenches with explicit edge and accepted-transfer semantics.

Latency 0 is combinational; latency N samples after the Nth rising edge
following falling-edge stimulus. Handshakes sample before NBA updates.
"""
from __future__ import annotations
import json
import random
import re
from pathlib import Path
from .spec import ModuleSpec
from .golden import GoldenModel


def _ports(spec):
    return ([p for p in spec.ports if p.direction == "input" and p.protocol == "none"
             and p.name not in ("clk", spec.reset.signal)],
            [p for p in spec.ports if p.direction == "output" and p.protocol == "none"])


def _validate(spec, stimulus=None, expected=None):
    identifier = r"[A-Za-z_][A-Za-z0-9_]*"
    if not re.fullmatch(identifier, spec.name):
        raise ValueError("invalid testbench module name")
    names = [p.name for p in spec.ports]
    if len(names) != len(set(names)):
        raise ValueError("duplicate testbench ports")
    if type(spec.latency) is not int or not 0 <= spec.latency <= 1024:
        raise ValueError("unsupported latency")
    if spec.compare_mode not in ("fixed_latency", "scoreboard"):
        raise ValueError("unsupported compare mode")
    for p in spec.ports:
        if not re.fullmatch(identifier, p.name) or p.name.startswith("_autortl_"):
            raise ValueError("invalid or reserved testbench port name")
        if p.direction not in ("input", "output") or type(p.width) is not int or not 1 <= p.width <= 1024:
            raise ValueError("unsupported testbench port shape")
        if p.clock_domain != "clk" or p.protocol not in ("none", "valid_ready"):
            raise ValueError("unsupported clock domain or protocol")
    if spec.clock_domains != ["clk"]:
        raise ValueError("only one clk domain is supported")
    by_name = {p.name: p for p in spec.ports}
    for name in ("clk", spec.reset.signal):
        if name in by_name and (by_name[name].direction != "input" or by_name[name].width != 1
                               or by_name[name].protocol != "none"):
            raise ValueError("clock/reset must be scalar plain inputs")
    if spec.reset.signal == "clk" or spec.reset.kind not in ("sync", "async"):
        raise ValueError("unsupported reset contract")
    if type(spec.reset.duration_cycles) is not int or not 1 <= spec.reset.duration_cycles <= 1000:
        raise ValueError("unsupported reset duration")
    if spec.latency > 0 or spec.compare_mode == "scoreboard":
        if "clk" not in names or spec.reset.signal not in names:
            raise ValueError("sequential verification requires clock and reset")
    if spec.compare_mode == "fixed_latency" and any(p.protocol != "none" for p in spec.ports):
        raise ValueError("fixed latency does not accept handshake ports")
    if any(type(v) is not int or abs(v) > 2**31 for v in spec.parameters.values()):
        raise ValueError("parameters must be bounded integer literals")
    if any(not re.fullmatch(identifier, k) for k in spec.parameters):
        raise ValueError("invalid parameter name")
    inputs, outputs = _ports(spec)
    if not outputs:
        raise ValueError("testbench requires data outputs")
    if stimulus is not None:
        if not stimulus or len(stimulus) > 10000 or len(stimulus) != len(expected):
            raise ValueError("stimulus/expected lengths must match and be nonempty")
        for rows, ports in ((stimulus, inputs), (expected, outputs)):
            for row in rows:
                if set(row) != {p.name for p in ports}:
                    raise ValueError("stimulus/expected must cover exactly all data ports")
                for p in ports:
                    if type(row[p.name]) is not int or not 0 <= row[p.name] < (1 << p.width):
                        raise ValueError("value is not a masked port integer")
    return inputs, outputs


def gen_stimulus(spec: ModuleSpec, n_random=100, seed=1234):
    inputs, _ = _validate(spec)
    if type(n_random) is not int or not 0 <= n_random <= 9997:
        raise ValueError("invalid stimulus count")
    rng = random.Random(seed)
    stimulus = [{p.name: fn(p.width) for p in inputs} for fn in
                (lambda w: 0, lambda w: (1 << w)-1, lambda w: 1 << (w-1))]
    stimulus += [{p.name: rng.randrange(1 << p.width) for p in inputs} for _ in range(n_random)]
    return stimulus


def expected_outputs(spec, golden, stimulus):
    return golden.run(stimulus)


def _header(spec, stimulus, expected, inputs, outputs, extra=""):
    n = len(stimulus)
    lines = ["`timescale 1ns/1ps", f"module {spec.name}_tb;", "reg _autortl_clk = 0;",
             "always #5 _autortl_clk = ~_autortl_clk;"]
    for p in spec.ports:
        if p.name != "clk":
            lines.append(f"{'reg' if p.direction == 'input' else 'wire'} [{p.width-1}:0] {p.name};")
    lines += ["integer _autortl_cycle, _autortl_errors, _autortl_index;", extra]
    for ports, kind in ((inputs, "stim"), (outputs, "exp")):
        for p in ports:
            lines.append(f"reg [{p.width-1}:0] _autortl_{kind}_{p.name} [0:{n-1}];")
    params = " #( " + ", ".join(f".{k}({v})" for k,v in spec.parameters.items()) + " )" if spec.parameters else ""
    conns = ", ".join(f".{p.name}({'_autortl_clk' if p.name == 'clk' else p.name})" for p in spec.ports)
    lines.append(f"{spec.name}{params} dut ({conns});")
    lines += ["initial begin", "_autortl_errors = 0;"]
    for p in spec.ports:
        if p.direction == "input" and p.name != "clk":
            lines.append(f"{p.name} = 0;")
    for ports, rows, kind in ((inputs, stimulus, "stim"), (outputs, expected, "exp")):
        for p in ports:
            lines += [f"_autortl_{kind}_{p.name}[{i}] = {p.width}'d{row[p.name]};"
                      for i, row in enumerate(rows)]
    if spec.reset.signal in {p.name for p in spec.ports}:
        asserted = 1 if spec.reset.active_high else 0
        lines += [f"{spec.reset.signal} = 1'b{asserted};",
                  f"repeat ({spec.reset.duration_cycles}) @(posedge _autortl_clk);",
                  "@(negedge _autortl_clk);", f"{spec.reset.signal} = 1'b{1-asserted};"]
    else:
        lines.append("@(negedge _autortl_clk);")
    return lines


def _checks(outputs, index):
    return [f'if ({p.name} !== _autortl_exp_{p.name}[{index}]) begin '
            f'$display("FAIL index=%0d signal={p.name}", {index}); '
            '_autortl_errors = _autortl_errors + 1; end' for p in outputs]


def _footer(spec, cycles):
    return ['if (_autortl_errors == 0) $display("TEST PASSED");',
            'else $display("TEST FAILED: %0d errors", _autortl_errors);', '$finish;', 'end',
            f'initial begin #{(cycles + spec.reset.duration_cycles + 20)*10}; '
            '$display("TEST FAILED: watchdog timeout"); $finish; end', 'endmodule', '']


def generate_fixed_latency_tb(spec, stimulus, expected):
    inputs, outputs = _validate(spec, stimulus, expected)
    n, offset = len(stimulus), max(spec.latency-1, 0)
    cycles = n + offset
    lines = _header(spec, stimulus, expected, inputs, outputs)
    lines += [f"for (_autortl_cycle=0; _autortl_cycle<{cycles}; _autortl_cycle=_autortl_cycle+1) begin",
              "if (_autortl_cycle > 0) @(negedge _autortl_clk);",
              f"if (_autortl_cycle < {n}) begin"]
    lines += [f"{p.name} = _autortl_stim_{p.name}[_autortl_cycle];" for p in inputs]
    lines.append("end")
    if spec.latency:
        lines.append("@(posedge _autortl_clk);")
    lines += ["#1;", f"_autortl_index = _autortl_cycle - {offset};",
              f"if (_autortl_index >= 0 && _autortl_index < {n}) begin"]
    lines += _checks(outputs, "_autortl_index")
    lines += ["end", "end"] + _footer(spec, cycles)
    return "\n".join(lines)


def generate_scoreboard_tb(spec, stimulus, expected):
    inputs, outputs = _validate(spec, stimulus, expected)
    controls = [p for p in spec.ports if p.protocol == "valid_ready"]
    def control(direction, suffix):
        found = [p for p in controls if p.direction == direction and p.name.endswith(suffix) and p.width == 1]
        if len(found) != 1:
            raise ValueError("scoreboard requires exactly one input and output valid/ready channel")
        return found[0].name
    if len(controls) != 4 or not inputs:
        raise ValueError("unsupported scoreboard channel shape")
    iv, ir, ov, ore = control("input", "valid"), control("output", "ready"), control("output", "valid"), control("input", "ready")
    n, cycles = len(stimulus), len(stimulus)*12+32
    extra = "integer _autortl_push, _autortl_pop, _autortl_drain;\nreg _autortl_stalled;\n"
    extra += "\n".join(f"reg [{p.width-1}:0] _autortl_held_{p.name};" for p in outputs)
    lines = _header(spec, stimulus, expected, inputs, outputs, extra)
    lines += ["_autortl_push=0; _autortl_pop=0; _autortl_drain=0; _autortl_stalled=0;",
              f"for (_autortl_cycle=0; _autortl_cycle<{cycles} && _autortl_drain<4; _autortl_cycle=_autortl_cycle+1) begin",
              "if (_autortl_cycle > 0) @(negedge _autortl_clk);",
              f"{iv} = (_autortl_push < {n});",
              f"{ore} = (_autortl_cycle % 7 >= 2); // periodic backpressure",
              f"if (_autortl_push < {n}) begin"]
    lines += [f"{p.name} = _autortl_stim_{p.name}[_autortl_push];" for p in inputs]
    lines += ["end", "@(posedge _autortl_clk); // sample accepted transfers BEFORE NBA",
              f"if (({ir} !== 1'b0 && {ir} !== 1'b1) || ({ov} !== 1'b0 && {ov} !== 1'b1)) begin",
              '$display("FAIL unknown handshake"); _autortl_errors=_autortl_errors+1; end',
              "if (_autortl_stalled) begin",
              f"if ({ov} !== 1'b1) begin $display(\"FAIL valid dropped under backpressure\"); _autortl_errors=_autortl_errors+1; end"]
    lines += [f"if ({p.name} !== _autortl_held_{p.name}) begin $display(\"FAIL unstable {p.name}\"); _autortl_errors=_autortl_errors+1; end" for p in outputs]
    lines += ["end", f"if ({iv} === 1'b1 && {ir} === 1'b1) _autortl_push=_autortl_push+1;",
              f"if ({ov} === 1'b1 && {ore} === 1'b1) begin",
              f"if (_autortl_pop >= _autortl_push || _autortl_pop >= {n}) begin",
              '$display("FAIL unexpected output transaction"); _autortl_errors=_autortl_errors+1;', "end else begin"]
    lines += _checks(outputs, "_autortl_pop")
    lines += ["end", "_autortl_pop=_autortl_pop+1;", "end",
              f"_autortl_stalled=({ov} === 1'b1 && {ore} === 1'b0);"]
    lines += [f"_autortl_held_{p.name}={p.name};" for p in outputs]
    lines += [f"if (_autortl_pop >= {n}) _autortl_drain=_autortl_drain+1;", "end",
              f"if (_autortl_push != {n} || _autortl_pop != {n}) begin",
              '$display("FAIL scoreboard did not drain"); _autortl_errors=_autortl_errors+1; end']
    lines += _footer(spec, cycles)
    return "\n".join(lines)


def generate(spec: ModuleSpec, golden: GoldenModel, out_dir: Path, n_random=100, seed=1234):
    stimulus = gen_stimulus(spec, n_random, seed)
    expected = expected_outputs(spec, golden, stimulus)
    generator = generate_scoreboard_tb if spec.compare_mode == "scoreboard" else generate_fixed_latency_tb
    text = generator(spec, stimulus, expected)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{spec.name}_tb.v"
    path.write_text(text)
    (out_dir / "stimulus.json").write_text(json.dumps({"stimulus": stimulus, "expected": expected}, indent=1))
    return path
