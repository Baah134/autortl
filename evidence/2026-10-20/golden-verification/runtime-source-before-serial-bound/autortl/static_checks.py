"""Static Verilog checks — rung 1 of the verification ladder. Milliseconds, no tools.

These catch the failure classes we have actually hit in v1-v3:
wrong module extracted, interface drift, latches, banned constructs.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from .spec import ModuleSpec
from .verilog_interface import infer_module, strip_comments


@dataclass
class StaticResult:
    passed: bool
    errors: list[str]


def check(verilog: str, contract: ModuleSpec | None = None) -> StaticResult:
    errs: list[str] = []
    src = _strip_comments(verilog)

    if not re.search(r"\bmodule\s+\w+", src):
        return StaticResult(False, ["no module declaration found — is this Verilog at all?"])
    if "endmodule" not in src:
        errs.append("missing endmodule")
    if re.search(r"\binitial\b", src):
        errs.append("initial block present — not synthesisable on Xilinx, remove it")
    tokens = re.findall(r"\b(?:begin|end)\b", re.sub(r'"(?:\\.|[^"\\])*"', '""', src))
    depth = 0
    for token in tokens:
        depth += 1 if token == "begin" else -1
        if depth < 0:
            break
    if depth:
        errs.append("begin/end imbalance — verify blocks")

    if contract is not None:
        errs.extend(_check_interface(src, contract))
        errs.extend(_check_latches(src))

    return StaticResult(len(errs) == 0, errs)


def _strip_comments(text: str) -> str:
    return strip_comments(text)


def _check_interface(src: str, c: ModuleSpec) -> list[str]:
    errs = []
    try:
        inferred = infer_module(src, c.name)
        actual = {p.name: p for p in inferred.ports}
    except ValueError as exc:
        return [str(exc)]
    if list(c.parameters.items()) != list(inferred.parameters.items()):
        errs.append("contract public parameter names/order/defaults mismatch")
    if c.interface_signature is not None and c.interface_signature != inferred.interface_signature:
        errs.append("contract symbolic interface signature mismatch (parameter types/defaults, dependencies or packed ranges changed)")
    expected = {p.name: p for p in c.ports}
    for name, port in expected.items():
        if name not in actual:
            errs.append(f"contract port '{name}' missing from interface")
        elif (port.direction, port.width) != (actual[name].direction, actual[name].width):
            errs.append(f"contract port '{name}' direction/width mismatch: expected {port.direction}[{port.width}], got {actual[name].direction}[{actual[name].width}]")
        if name in actual:
            observed = actual[name]
            if port.signed != observed.signed:
                errs.append(f"contract port '{name}' signedness mismatch")
            def shape(p):
                return p.packed_dimensions if p.packed_dimensions is not None else ([[p.width-1,0]] if p.width > 1 else [])
            if shape(port) != shape(observed):
                errs.append(f"contract port '{name}' packed dimensions/orientation mismatch")
    for name in actual.keys() - expected.keys():
        errs.append(f"unexpected interface port '{name}'")
    return errs


def _check_latches(src: str) -> list[str]:
    """Detect combinational always blocks where a signal is conditionally assigned
    without a default — the classic inferred-latch pattern."""
    errs = []
    for block in re.finditer(r"always\s*@\s*\(\s*\*\s*\)\s*(begin(.*?)end|[^;]+;)",
                             src, flags=re.DOTALL):
        body = block.group(0)
        if re.search(r"\bif\b", body) and not re.search(r"\belse\b", body):
            assigned = set(re.findall(r"(\w+)\s*(?:<=|=)\s*", body))
            prefix = re.split(r"\bif\b", body, maxsplit=1)[0]
            defaults = set(re.findall(r"(\w+)\s*(?:<=|=)\s*", prefix))
            missing = assigned - defaults
            if missing:
                errs.append(
                    "possible inferred latch: combinational always @(*) has 'if' "
                    f"without 'else' assigning {sorted(missing)[:3]} — add default "
                    "assignments at the top of the block")
    return errs
