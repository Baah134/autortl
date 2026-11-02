"""Bounded advisory context for the editable source and frozen compilation inputs.

The editable source is either a top module beside frozen companions or, after a
build verified by a trusted integration testbench, one unit holding every
generated module and the top (taxonomy frozen_children_block_build_optimization).

Declaration discovery is context only. The compiler and interface checks remain
acceptance authorities; an unsupported interface never becomes an invented fact.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from .contract_context import file_evidence
from .spec import valid_identifier
from .verilog_interface import IDENT, infer_module, strip_comments

MAX_SCOPE_CHARS = 16000
PREVIEW_CHARS_PER_FILE = 2000
_HEADER = """# CANDIDATE COMPILATION BOUNDARY (immutable)
Only the editable top module named below may be replaced. Return its RTL only.
Companion files/modules are frozen and already compiled alongside your output:
do not redeclare, replace, rename or modify them. You may instantiate them, or
inline equivalent logic INSIDE the editable top while preserving its contract.
Inlining by itself saves nothing: synthesis flattens the hierarchy, so a
verbatim copy of a child routes to the same design. Inline only to make a
logic change across the boundary, such as sharing or removing state.
Preserve observable cycles, reset behavior, parameter/interface semantics and
clock usage. Do not add clocks or change latency to obtain timing closure.
The module inventory is advisory context, not a semantic acceptance result.
Source previews are bounded excerpts; paths and SHA256 identify complete files.
"""
_UNIT_HEADER = """# CANDIDATE COMPILATION BOUNDARY (immutable)
The editable source is ONE unit holding every generated child module of this
build and the top module named below (children first, top last). No frozen
companion file is compiled beside it. Return the COMPLETE unit -- every module
the top needs, top module last -- in one verilog fence: a module you omit is
not supplied from anywhere else.
Only the top carries the contract: keep its name, ports, parameters and
defaults, reset, clocking, latency annotation rule and every observable cycle
at its ports. You may change, merge, split, rename or remove child modules and
move logic across their boundaries, as long as the top's contract holds.
Restructuring or inlining by itself saves nothing: synthesis flattens the
hierarchy, so change logic, such as sharing or removing state.
Every candidate is verified by the trusted integration testbench of the top
and every other gate. The per-child generated oracles and testbenches verified
the baseline children only; they do not verify changed children.
Do not add clocks or change latency to obtain timing closure.
The module inventory is advisory context, not a semantic acceptance result.
"""


def _inventory(text):
    source = strip_comments(text)
    source = re.sub(r'"(?:\\.|[^"\\])*"', '""', source)
    # Reuse the interface parser's identifier and declaration convention; only
    # discover names here, then ask that parser for any interface facts.
    names = [match[1] for match in re.finditer(rf"\bmodule\s+({IDENT})\b", source)]
    result = []
    for name in names:
        record = {"name": name}
        try:
            module = infer_module(text, name)
            record["parameters"] = module.parameters
            record["ports"] = [{"name":p.name,"direction":p.direction,"width":p.width,
                                "signed":p.signed,"packed_dimensions":p.packed_dimensions}
                               for p in module.ports]
        except (ValueError, TypeError) as exc:
            record["interface_warning"] = str(exc)[:240]
        result.append(record)
    return result


def _unit_scope(top_module, editable_unit):
    """Whole-design build mode: one editable multi-module unit, no companions."""
    fact = file_evidence(Path(editable_unit["source"]), limit=0)
    modules = _inventory(Path(editable_unit["source"]).read_text(encoding="utf-8", errors="replace"))
    if not any(module["name"] == top_module for module in modules):
        raise ValueError("editable unit does not declare the top module")
    scope = {"editable_top": top_module,
             "editable_unit": {"path": fact["path"], "sha256": fact["sha256"], "modules": modules,
                               "note": "The generation seed is the complete current unit text."},
             "frozen_companions": []}
    required = sorted(editable_unit.get("testbench_modules") or ())
    if required:
        scope["must_keep_live_under_top"] = {
            "modules": required,
            "why": "The trusted testbench instantiates these modules directly, so it also checks them on their "
                   "own. Keep each defined with an interface that testbench accepts and keep it a live instance "
                   "reached from the top: unconditional at module level (not inside generate, if/else, case, for "
                   "or begin/end) with at least one output feeding logic that drives a top output port. "
                   "Otherwise those checks would test a module the top no longer uses, and the candidate is "
                   "rejected."}
    # editable_unit_inventory_overflow: the inventory is advisory (the complete unit
    # text is the generation seed), so a large unit is summarized step by step;
    # the top's full interface is always kept.
    def child(record, level):
        if record["name"] == top_module or level == 0:
            return record
        if level == 1:
            return {"name": record["name"], "ports": [p["name"] for p in record.get("ports", [])]}
        return {"name": record["name"]}
    for level, indent in ((0, 2), (0, None), (1, None), (2, None)):
        unit = dict(scope["editable_unit"], modules=[child(m, level) for m in modules])
        if level:
            unit["inventory_summarized"] = ("child modules listed by " + ("port names" if level == 1 else "name")
                                            + " only; read their full interfaces in the unit text")
        text = _UNIT_HEADER + json.dumps(dict(scope, editable_unit=unit), sort_keys=True, indent=indent)
        if len(text) <= MAX_SCOPE_CHARS:
            return text
    raise ValueError("editable unit metadata exceeds candidate context budget; partition the compilation unit")


def candidate_scope(top_module, extra_sources, testbench_companions=(), *, editable_unit=None):
    """Return bounded model guidance; never silently omit frozen input metadata.

    testbench_companions names frozen companions the trusted testbench
    instantiates directly. The top must keep instantiating those; the field
    appears only when nonempty, so other runs' prompts are unchanged.

    editable_unit ({"source": path, "testbench_modules": [...]}) selects the
    whole-design build mode: the unit holds every generated module and the
    top, nothing is frozen, and extra_sources must be empty.
    """
    if not valid_identifier(top_module):
        raise ValueError("candidate scope requires a valid editable top identifier")
    if editable_unit is not None:
        if extra_sources or testbench_companions:
            raise ValueError("an editable unit has no frozen companions")
        return _unit_scope(top_module, editable_unit)
    paths = list(dict.fromkeys(Path(path).resolve() for path in extra_sources))
    files = []
    for path in paths:
        fact = file_evidence(path, limit=0)
        modules = _inventory(path.read_text(encoding="utf-8",errors="replace"))
        if any(module["name"] == top_module for module in modules):
            raise ValueError("editable top is also declared in a frozen companion file")
        files.append({"path":fact["path"],"sha256":fact["sha256"],"modules":modules,
                      "source_preview":"","preview_truncated":fact["truncated"]})
    scope = {"editable_top":top_module,"frozen_companions":files}
    if testbench_companions:
        scope["must_keep_instantiating"] = {
            "modules": sorted(testbench_companions),
            "why": "The trusted testbench instantiates these companions directly. Inlining them would leave those "
                   "checks testing the frozen companion instead of your top, so a candidate that stops "
                   "instantiating them is rejected. Each must stay a live instance: unconditional at module "
                   "level (not inside generate, if/else, case, for or begin/end) with at least one output "
                   "feeding logic that drives a top output port."}
    render = lambda: _HEADER + json.dumps(scope,sort_keys=True,indent=2)
    if len(render()) > MAX_SCOPE_CHARS:
        raise ValueError("frozen companion metadata exceeds candidate context budget; partition the compilation unit")
    # JSON escaping affects the final budget. Search each preview length against
    # actual rendered characters, retaining complete metadata even at zero text.
    for fact,path in zip(files,paths):
        preview = file_evidence(path,limit=PREVIEW_CHARS_PER_FILE)
        low,high=0,len(preview["text"])
        while low<high:
            middle=(low+high+1)//2
            fact["source_preview"]=preview["text"][:middle]
            fact["preview_truncated"]=preview["truncated"] or middle<len(preview["text"])
            if len(render()) <= MAX_SCOPE_CHARS:
                low=middle
            else:
                high=middle-1
        fact["source_preview"]=preview["text"][:low]
        fact["preview_truncated"]=preview["truncated"] or low<len(preview["text"])
    return render()
