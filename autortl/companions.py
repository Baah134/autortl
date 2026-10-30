"""Which frozen companions a trusted testbench tests directly, and whether a
candidate still uses them.

A build's child modules become frozen companions: compiled unchanged beside
every candidate top. A candidate may inline a companion's logic instead of
instantiating it. When the trusted testbench instantiates that companion
directly, though, the companion is part of what the testbench verifies, and
an inlined candidate leaves those checks running against the stale companion
file instead of the candidate (taxonomy: stale_companion_masks_inlined_candidate).

A textual instance is not enough either (taxonomy:
companion_instance_does_not_prove_top_behavior): an instance inside
`generate if (0)`, or one whose outputs drive nothing, satisfies a textual
search while the top's real logic lives elsewhere. So each such companion
must be reached through LIVE instances: unconditional module-level items whose
outputs feed, through best-effort lexical dataflow, an output of the
instantiating module. See live_instance for the exact rule and its limits.

Instantiation discovery is lexical: comments and strings are removed, module
headers are dropped, and a known module name followed by `#(` or by an
instance name and `(` counts as an instantiation. Only known module names are
searched, so keywords and other identifiers cannot match.
"""
from __future__ import annotations
import re
from pathlib import Path

from .verilog_interface import IDENT, _group, infer_module, split_items, strip_comments

_MODULE = re.compile(rf"\bmodule\s+({IDENT})\b(.*?)\bendmodule\b", re.S)


def _clean(text):
    return re.sub(r'"(?:\\.|[^"\\])*"', '""', strip_comments(text))


def module_bodies(text):
    """Map each module declared in text to its body (header name removed)."""
    return {match[1]: match[2] for match in _MODULE.finditer(_clean(text))}


def instantiated(text, names):
    """The subset of names instantiated somewhere in text (already cleaned or not)."""
    body = re.sub(rf"\bmodule\s+{IDENT}", "module", _clean(text))
    found = set()
    for name in names:
        if re.search(rf"(?<![\w$]){re.escape(name)}\s*(?:#\s*\(|{IDENT}\s*(?:\[[^\]]*\]\s*)?\()", body):
            found.add(name)
    return found


def _sources(extra_sources):
    return [Path(path).read_text(encoding="utf-8", errors="replace") for path in extra_sources]


def companion_modules(extra_sources):
    """Map each module declared in the companion files to its body."""
    modules = {}
    for text in _sources(extra_sources):
        modules.update(module_bodies(text))
    return modules


def required_by_testbench(tb, extra_sources):
    """Companions the trusted testbench instantiates directly, sorted."""
    if tb is None or not extra_sources:
        return []
    names = set(companion_modules(extra_sources))
    return sorted(instantiated(Path(tb).read_text(encoding="utf-8", errors="replace"), names))


def unreachable(candidate_verilog, top, extra_sources, required):
    """Required companions that the candidate top no longer reaches."""
    if not required:
        return []
    companions = companion_modules(extra_sources)
    own = module_bodies(candidate_verilog)
    bodies = {**companions, **own}             # a candidate may define helpers, never companions
    reached, frontier = set(), [top]
    while frontier:
        name = frontier.pop()
        if name in reached or name not in bodies:
            continue
        reached.add(name)
        frontier.extend(instantiated(bodies[name], set(bodies) - reached))
    return sorted(set(required) - reached)


# --- Liveness (taxonomy: companion_instance_does_not_prove_top_behavior) -------------------------

_KEYWORDS = frozenset("""
    always always_comb always_ff always_latch and assign automatic begin bit buf case casex casez default
    defparam disable else end endcase endfunction endgenerate endtask for forever fork function generate
    genvar if initial inout input int integer join join_any join_none localparam logic nand negedge nor
    not or output parameter posedge reg repeat signed task tri unsigned wait while wire xnor xor
""".split())
_OPEN = frozenset({"begin", "case", "casex", "casez", "fork", "generate", "function", "task"})
_CLOSE = frozenset({"end", "endcase", "join", "join_any", "join_none", "endgenerate", "endfunction", "endtask"})
_STRUCTURE = re.compile(r"\b(?:begin|end|generate|endgenerate|casex|casez|case|endcase|fork|join_any|join_none|"
                        r"join|function|endfunction|task|endtask)\b|[;()]")
_CONDITIONAL = re.compile(r"\b(?:if|else|for|while|repeat|case|casex|casez|generate)\b")
_LITERAL = re.compile(r"\d*\s*'[sS]?[bBoOdDhH]\s*[0-9a-fA-F_xXzZ?]+|'[01xXzZ]|\$[\w$]*|\b\d[\d_]*(?:\.\d+)?")
_ASSIGN_OP = re.compile(r"<=|(?<![=!<>])=(?!=)")
_LHS = re.compile(rf"(\{{[^{{}}]*\}}|{IDENT}(?:\s*\[[^\]]*\])*)\s*$")
_ANY_INSTANCE = re.compile(rf"(?<![\w$.])({IDENT})\s*(?:#\s*\(|{IDENT}\s*(?:\[[^\]]*\]\s*)?\()")
_LABEL = re.compile(rf"\s*{IDENT}\s*(?:\[[^\]]*\]\s*)?")


def _identifiers(text):
    return set(re.findall(rf"(?<![\w$']){IDENT}", _LITERAL.sub(" ", text))) - _KEYWORDS


def _targets(lhs):
    return _identifiers(re.sub(r"\[[^\]]*\]", " ", lhs))


def _port_directions(text, module):
    """[(port, direction)] in declaration order, or None when the interface cannot be read."""
    try:
        return [(port.name, port.direction) for port in infer_module(text, module).ports]
    except ValueError:
        pass
    body = module_bodies(text).get(module)
    if body is None:
        return None
    try:                                         # lexical fallback: ANSI header, else body declarations
        tail = body.lstrip()
        if tail.startswith("#"):
            tail = tail[1:].lstrip()
            _, end = _group(tail, 0)
            tail = tail[end:].lstrip()
        header, _ = _group(tail, 0)
    except ValueError:
        return None
    declarations = header if re.search(r"\b(?:input|output|inout)\b", header) else ",".join(
        match[0][:-1] for match in re.finditer(r"\b(?:input|output|inout)\b[^;]*;", body))
    try:
        items = split_items(declarations)
    except ValueError:
        return None
    ports, direction = [], None
    for item in items:
        keyword = re.match(r"\s*(input|output|inout)\b", item)
        direction = keyword[1] if keyword else direction
        names = re.findall(rf"(?<![\w$]){IDENT}", re.sub(r"\[[^\]]*\]|=.*", " ", item, flags=re.S))
        if direction and names:
            ports.append((names[-1], direction))
    return ports or None


def _instances(body, name):
    """(start offset, connection list text) of each instance of module name in a cleaned body."""
    for match in re.finditer(rf"(?<![\w$.]){re.escape(name)}\s*", body):
        rest = match.end()
        try:
            if body.startswith("#", rest):
                rest += 1
                while rest < len(body) and body[rest].isspace():
                    rest += 1
                _, rest = _group(body, rest)
            label = _LABEL.match(body, rest)
            if not label or not body.startswith("(", label.end()):
                continue
            connections, _ = _group(body, label.end())
        except ValueError:
            continue
        yield match.start(), connections


def _connected(connections, ports, directions):
    """Identifiers bound to the instance ports whose direction is in directions.

    Named (`.p(x)`, `.p`, `.*`) and positional bindings are understood. When the
    child's interface is unknown every binding counts, so unknown means lenient.
    """
    try:
        items = [item for item in split_items(connections) if item]
    except ValueError:
        return _identifiers(connections)
    if ports is None:
        return set().union(*map(_identifiers, items)) if items else set()
    wanted = {port for port, direction in ports if direction in directions}
    found = set()
    for index, item in enumerate(items):
        if item == ".*":
            found |= wanted
            continue
        named = re.fullmatch(rf"\.\s*({IDENT})\s*(?:\((.*)\))?", item, re.S)
        if named:
            if named[1] in wanted:
                found |= {named[1]} if named[2] is None else _identifiers(named[2])
        elif index < len(ports) and ports[index][0] in wanted:
            found |= _identifiers(item)
    return found


def _statement_end(body, start):
    """End offset of the module item or procedural statement starting at start (best-effort)."""
    depth = parens = 0
    for token in _STRUCTURE.finditer(body, start):
        word = token[0]
        if word in "()":
            parens += 1 if word == "(" else -1
            continue
        if parens > 0:
            continue
        if word in _OPEN:
            depth += 1
            continue
        if word in _CLOSE:
            depth -= 1
        if depth <= 0 and not re.match(r"\s*else\b", body[token.end():]):
            return token.end()
    return len(body)


def _unconditional(body, position):
    """True when position sits at module-item level: outside every generate region,
    begin/end, case and function, and not governed by an unbraced if/else/for."""
    depth = parens = 0
    boundary = 0
    for token in _STRUCTURE.finditer(body, 0, position):
        word = token[0]
        if word in "()":
            parens += 1 if word == "(" else -1
            continue
        if parens > 0:
            continue
        if word in _OPEN:
            depth += 1
        elif word in _CLOSE:
            depth -= 1
            if depth == 0:
                boundary = token.end()
        elif depth == 0:
            boundary = token.end()                # ';' ends the previous module item
    return depth == 0 and parens == 0 and not _CONDITIONAL.search(body, boundary, position)


def _flow(body, interface):
    """Lexical dataflow edges source -> {targets} within one cleaned module body.

    Over-approximates on purpose: every identifier read anywhere in an always
    block (data or control) flows to every target the block assigns, and an
    instance of a module with an unknown interface connects all its bindings
    both ways. Instances of known modules flow from input to output bindings.
    """
    edges = {}

    def add(sources, targets):
        for source in sources:
            edges.setdefault(source, set()).update(targets)

    for match in re.finditer(r"\bassign\b", body):
        statement = body[match.end():_statement_end(body, match.end())].rstrip().rstrip(";")
        try:
            items = split_items(statement)
        except ValueError:
            items = [statement]
        for item in items:
            op = _ASSIGN_OP.search(item)
            if op:
                add(_identifiers(item[op.end():]), _targets(item[:op.start()]))
    for match in re.finditer(r"\b(?:wire|tri|wand|wor|logic)\b([^;]*);", body):   # net declaration assignments
        try:
            items = split_items(match[1])
        except ValueError:
            continue
        for item in items:
            op = _ASSIGN_OP.search(item)
            lhs = _LHS.search(item[:op.start()]) if op else None
            if lhs:
                add(_identifiers(item[op.end():]), _targets(lhs[1]))
    for match in re.finditer(r"\balways(?:_comb|_ff|_latch)?\b", body):
        block = body[match.end():_statement_end(body, match.end())]
        targets, parens, last = set(), 0, 0
        for op in _ASSIGN_OP.finditer(block):
            parens += block.count("(", last, op.start()) - block.count(")", last, op.start())
            last = op.start()
            lhs = _LHS.search(block[:op.start()]) if parens == 0 else None
            if lhs:
                targets |= _targets(lhs[1])
        add(_identifiers(block), targets)
    for match in _ANY_INSTANCE.finditer(body):
        name = match[1]
        if name in _KEYWORDS:
            continue
        for start, connections in _instances(body, name):
            if start != match.start():
                continue
            ports = interface(name)
            if ports is None:
                bound = _connected(connections, None, ())
                add(bound, bound)
            else:
                add(_connected(connections, ports, {"input", "inout"}),
                    _connected(connections, ports, {"output", "inout"}))
    return edges


def _reaches(sources, sinks, edges):
    seen, frontier = set(), list(sources)
    while frontier:
        signal = frontier.pop()
        if signal in sinks:
            return True
        if signal not in seen:
            seen.add(signal)
            frontier.extend(edges.get(signal, ()))
    return False


def live_instance(body, child, child_ports, parent_ports, edges):
    """True when a cleaned module body holds at least one live instance of child.

    Live means: (1) the instance is an unconditional module item -- not inside
    any generate region, generate if/for/case, begin/end block, or unbraced
    if/else/for; and (2) at least one child output (or inout) is bound to a
    signal that reaches an output (or inout) port of the instantiating module,
    directly or through continuous assigns, always blocks and other instances
    (see _flow).

    Limits: purely lexical and best-effort. It does not elaborate, evaluate
    parameters or generate conditions, or resolve hierarchical references, and
    dataflow is over-approximated, so an instance whose values are in fact
    masked (e.g. ANDed with 0) can still be judged live. When an interface
    cannot be read the check is lenient for that side. It rejects only clearly
    dead, conditional or disconnected instances; the behavior of the top is
    still proven by the trusted testbench's top-level checks, never by this rule.
    """
    sinks = None if parent_ports is None else {port for port, direction in parent_ports
                                               if direction in ("output", "inout")}
    for start, connections in _instances(body, child):
        if not _unconditional(body, start):
            continue
        driven = _connected(connections, child_ports, {"output", "inout"})
        if driven and (sinks is None or _reaches(driven, sinks, edges)):
            return True
    return False


def live_reached(candidate_verilog, top, extra_sources):
    """Modules reached from top through live instances.

    Inside candidate-owned modules (the top and its helpers) each instance must be
    live (live_instance). Inside frozen companions a textual instance suffices:
    their source is fixed, not the candidate's to fake.
    """
    companions, origin = {}, {}
    for text in _sources(extra_sources):
        for name, body in module_bodies(text).items():
            companions[name], origin[name] = body, text
    own = module_bodies(candidate_verilog)
    origin.update(dict.fromkeys(own, candidate_verilog))
    bodies = {**companions, **own}
    cache = {}

    def interface(name):
        if name not in cache:
            cache[name] = _port_directions(origin[name], name) if name in origin else None
        return cache[name]

    reached, frontier = set(), [top]
    while frontier:
        name = frontier.pop()
        if name in reached or name not in bodies:
            continue
        reached.add(name)
        children = instantiated(bodies[name], set(bodies) - reached)
        if name in own:
            edges = _flow(bodies[name], interface)
            children = {child for child in children
                        if live_instance(bodies[name], child, interface(child), interface(name), edges)}
        frontier.extend(children)
    return reached


def not_live(candidate_verilog, top, extra_sources, required):
    """Required companions the candidate reaches only through dead, conditional or disconnected instances."""
    if not required:
        return []
    return sorted(set(required) - live_reached(candidate_verilog, top, extra_sources))


def violation(candidate_verilog, top, extra_sources, tb):
    """A repair-ready error message, or "" when the candidate is acceptable."""
    required = required_by_testbench(tb, extra_sources)
    missing = unreachable(candidate_verilog, top, extra_sources, required)
    if missing:
        names = ", ".join(missing)
        return (f"ERROR: candidate top {top} no longer instantiates frozen companion(s) {names}, which the trusted "
                f"testbench {Path(tb).name} instantiates directly; those checks would test the stale companion, not "
                f"this candidate. Keep instantiating {names} from {top}.")
    dead = not_live(candidate_verilog, top, extra_sources, required)
    if not dead:
        return ""
    names = ", ".join(dead)
    return (f"ERROR: candidate top {top} instantiates frozen companion(s) {names} only in dead, conditional or "
            f"disconnected form, while the trusted testbench {Path(tb).name} instantiates {names} directly; a "
            f"textual instance does not show that {top} uses it (companion_instance_does_not_prove_top_behavior). "
            f"Keep a live instance of {names} in {top}: an unconditional module-level instance (not inside "
            f"generate, if/else, case, for or begin/end) with at least one output connected to logic that drives "
            f"an output port of {top}.")
