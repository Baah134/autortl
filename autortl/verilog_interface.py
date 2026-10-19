"""Parse the synthesizable scalar/packed module interfaces used by AutoRTL.

Unsupported syntax fails explicitly. Integer expressions are interpreted,
never passed to Python eval or a shell.
"""
from __future__ import annotations
import ast
import operator
import re
from .spec import ModuleSpec, Port, ResetSpec

IDENT = r"[A-Za-z_][A-Za-z0-9_$]*"


def strip_comments(text: str) -> str:
    return re.sub(r"//[^\n]*|/\*.*?\*/", "", text, flags=re.S)


def split_items(text: str, delimiter=",") -> list[str]:
    result, start, depth = [], 0, 0
    for i, char in enumerate(text):
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
            if depth < 0:
                raise ValueError("unbalanced interface expression")
        elif char == delimiter and depth == 0:
            result.append(text[start:i].strip())
            start = i + 1
    if depth:
        raise ValueError("unbalanced interface expression")
    result.append(text[start:].strip())
    return result


def integer(expression: str, parameters: dict[str, int]) -> int:
    def literal(match):
        base = {"b": 2, "o": 8, "d": 10, "h": 16}[match[2].lower()]
        digits = match[3].replace("_", "")
        try:
            return str(int(digits, base))
        except ValueError as exc:
            raise ValueError("unknown digits in width/parameter") from exc
    expression = re.sub(r"(\d+)'[sS]?([bBoOdDhH])([0-9a-fA-F_xXzZ?]+)", literal, expression)
    expression = expression.replace("$clog2", "clog2")
    try:
        tree = ast.parse(expression.strip(), mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"unsupported integer expression: {expression}") from exc
    operations = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
                  ast.LShift: operator.lshift, ast.RShift: operator.rshift,
                  ast.BitAnd: operator.and_, ast.BitOr: operator.or_, ast.BitXor: operator.xor,
                  ast.Mod: operator.mod}
    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) is int:
            value = node.value
        elif isinstance(node, ast.Name) and node.id in parameters:
            value = parameters[node.id]
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub, ast.Invert)):
            arg = visit(node.operand)
            value = arg if isinstance(node.op, ast.UAdd) else -arg if isinstance(node.op, ast.USub) else ~arg
        elif isinstance(node, ast.BinOp) and type(node.op) in operations:
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, (ast.LShift, ast.RShift)) and not 0 <= right <= 63:
                raise ValueError("unsafe shift in integer expression")
            value = operations[type(node.op)](left, right)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            left, right = visit(node.left), visit(node.right)
            if not right:
                raise ValueError("division by zero in parameter")
            value = (abs(left) // abs(right)) * (-1 if (left < 0) != (right < 0) else 1)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "clog2" and len(node.args) == 1 and not node.keywords:
            arg = visit(node.args[0])
            if arg < 0:
                raise ValueError("negative clog2 argument")
            value = (arg - 1).bit_length() if arg > 1 else 0
        else:
            raise ValueError(f"unsupported integer expression: {expression}")
        if abs(value) > (1 << 63):
            raise ValueError("integer expression exceeds supported range")
        return value
    try:
        return visit(tree.body)
    except (ZeroDivisionError, OverflowError) as exc:
        raise ValueError("invalid integer expression") from exc


def _parameters(text: str, values: dict) -> None:
    for part in split_items(text):
        if not part:
            continue
        if "=" not in part:
            raise ValueError("parameter needs an explicit integer default")
        left, right = part.split("=", 1)
        name = re.search(rf"({IDENT})\s*$", left)
        if not name:
            raise ValueError("unsupported parameter declaration")
        values[name[1]] = integer(right, values)


def _group(text: str, start: int) -> tuple[str, int]:
    if start >= len(text) or text[start] != "(":
        raise ValueError("expected module port/parameter group")
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "(": depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0: return text[start + 1:i], i + 1
    raise ValueError("unterminated module header")


def _declarations(text: str, values: dict) -> list[Port]:
    ports, direction, width = [], None, 1
    for item in split_items(text):
        match = re.match(r"^(input|output|inout)\b", item)
        if match:
            direction, width = match[1], 1
            item = item[match.end():].strip()
            while True:
                qualifier = re.match(r"^(wire|reg|logic|bit|var|signed|unsigned|integer|int)\b\s*", item)
                if not qualifier: break
                if qualifier[1] in ("integer", "int"): width = 32
                item = item[qualifier.end():]
            while item.startswith("["):
                end = item.find("]")
                if end < 0: raise ValueError("unterminated packed range")
                bounds = split_items(item[1:end], ":")
                if len(bounds) != 2: raise ValueError("packed range needs two bounds")
                size = abs(integer(bounds[0], values) - integer(bounds[1], values)) + 1
                width = size if width == 1 else width * size
                item = item[end + 1:].strip()
        if direction is None or not re.fullmatch(IDENT, item):
            raise ValueError(f"unsupported port declaration: {item}")
        if not 1 <= width <= 65536:
            raise ValueError("port width outside supported range")
        ports.append(Port(item, direction, width))
    return ports


def infer_module(verilog: str, top: str) -> ModuleSpec:
    if not re.fullmatch(IDENT, top):
        raise ValueError("invalid module identifier")
    source = strip_comments(verilog)
    match = re.search(rf"\bmodule\s+{re.escape(top)}\b", source)
    if not match: raise ValueError(f"module name mismatch: expected '{top}'")
    tail = source[match.end():].lstrip()
    params = {}
    if tail.startswith("#"):
        tail = tail[1:].lstrip()
        group, pos = _group(tail, 0)
        _parameters(group, params)
        tail = tail[pos:].lstrip()
    header, pos = _group(tail, 0)
    body = tail[pos:]
    end = re.search(r"\bendmodule\b", body)
    if end is None: raise ValueError("missing endmodule")
    body = body[:end.start()]
    if not body.lstrip().startswith(";"): raise ValueError("module header missing semicolon")
    for declaration in re.finditer(r"\b(?:parameter|localparam)\b([^;]+);", body):
        _parameters(declaration[1], params)
    if re.search(r"\b(input|output|inout)\b", header):
        ports = _declarations(header, params)
    else:
        names = split_items(header)
        if not all(re.fullmatch(IDENT, name) for name in names):
            raise ValueError("unsupported non-ANSI port list")
        declared = {}
        for declaration in re.finditer(r"\b(input|output|inout)\b([^;]+);", body):
            for port in _declarations(declaration[0][:-1], params):
                if port.name in names:
                    if port.name in declared: raise ValueError("duplicate port declaration")
                    declared[port.name] = port
        if set(names) != set(declared): raise ValueError("missing non-ANSI port declarations")
        ports = [declared[name] for name in names]
    if len({port.name for port in ports}) != len(ports): raise ValueError("duplicate module port")
    latency = re.search(r"//\s*@latency\s+(\d+)", verilog)
    reset = "rst_n" if any(p.name == "rst_n" for p in ports) else "rst"
    return ModuleSpec(top, "existing design under optimization", ports,
                      latency=int(latency[1]) if latency else 0,
                      reset=ResetSpec(signal=reset, active_high=reset != "rst_n"), parameters=params)
