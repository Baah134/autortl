"""Bounded advisory context for the editable top and frozen compilation inputs.

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
Preserve observable cycles, reset behavior, parameter/interface semantics and
clock usage. Do not add clocks or change latency to obtain timing closure.
The module inventory is advisory context, not a semantic acceptance result.
Source previews are bounded excerpts; paths and SHA256 identify complete files.
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


def candidate_scope(top_module, extra_sources, testbench_companions=()):
    """Return bounded model guidance; never silently omit frozen input metadata.

    testbench_companions names frozen companions the trusted testbench
    instantiates directly. The top must keep instantiating those; the field
    appears only when nonempty, so other runs' prompts are unchanged.
    """
    if not valid_identifier(top_module):
        raise ValueError("candidate scope requires a valid editable top identifier")
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
                   "instantiating them is rejected."}
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
