"""Static Verilog checks — rung 1 of the verification ladder. Milliseconds, no tools.

These catch the failure classes we have actually hit in v1-v3:
wrong module extracted, interface drift, latches, banned constructs.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from .spec import ModuleSpec


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
    if src.count("begin") != src.count("end") - src.count("endmodule") - src.count("endcase") \
       and abs(src.count("begin") - (src.count("end") - src.count("endmodule") - src.count("endcase"))) > 0:
        # heuristic only; xvlog is the authority. Flag when wildly off.
        diff = src.count("begin") - (src.count("end") - src.count("endmodule") - src.count("endcase"))
        if abs(diff) > 0:
            errs.append(f"begin/end imbalance heuristic tripped (diff={diff}) — verify blocks")

    if contract is not None:
        errs.extend(_check_interface(src, contract))
        errs.extend(_check_latches(src))

    return StaticResult(len(errs) == 0, errs)


def _strip_comments(text: str) -> str:
    text = re.sub(r"//.*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return text


def _check_interface(src: str, c: ModuleSpec) -> list[str]:
    errs = []
    m = re.search(rf"\bmodule\s+({c.name})\b", src)
    if not m:
        found = re.search(r"\bmodule\s+(\w+)", src)
        errs.append(f"module name mismatch: contract says '{c.name}', "
                    f"code says '{found.group(1) if found else '?'}'")
        return errs
    for p in c.ports:
        if not re.search(rf"\b{re.escape(p.name)}\b", src):
            errs.append(f"contract port '{p.name}' missing from code")
    return errs


def _check_latches(src: str) -> list[str]:
    """Detect combinational always blocks where a signal is conditionally assigned
    without a default — the classic inferred-latch pattern."""
    errs = []
    for block in re.finditer(r"always\s*@\s*\(\s*\*\s*\)\s*(begin(.*?)end|[^;]+;)",
                             src, flags=re.DOTALL):
        body = block.group(0)
        if "if" in body and "else" not in body:
            assigned = set(re.findall(r"(\w+)\s*(?:<=|=)\s*", body))
            if assigned:
                errs.append(
                    "possible inferred latch: combinational always @(*) has 'if' "
                    f"without 'else' assigning {sorted(assigned)[:3]} — add default "
                    "assignments at the top of the block")
    return errs
