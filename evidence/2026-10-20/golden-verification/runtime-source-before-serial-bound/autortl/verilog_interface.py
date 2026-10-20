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
    return re.sub(r"//[^\n]*|/\*.*?\*/", " ", text, flags=re.S)


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
            bits = int(match[1])
            if not 1 <= bits <= 65536:
                raise ValueError("literal width outside supported range")
            value = int(digits, base) & ((1 << bits) - 1)
            if re.search(r"'[sS]", match[0]) and value & (1 << (bits - 1)):
                value -= 1 << bits
            return f"({value})"
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


def _symbolic(expression: str) -> str:
    # Preserve identifiers/operators and literal spelling; whitespace/comments are irrelevant.
    tokens = re.findall(r"\d+'[sS]?[bBoOdDhH][0-9a-fA-F_xXzZ?]+|[A-Za-z_$][A-Za-z0-9_$]*|\d+|<<|>>|[^\s]", expression)
    return " ".join(tokens)


def _dependencies(expression: str) -> set[str]:
    expression = re.sub(r"\d+'[sS]?[bBoOdDhH][0-9a-fA-F_xXzZ?]+", "0", expression)
    return set(re.findall(IDENT, expression)) - {"$clog2"}


def _validate_expression(expression: str, names: set[str]) -> None:
    normalized = re.sub(r"\d+'[sS]?[bBoOdDhH][0-9a-fA-F_xXzZ?]+", "0", expression).replace("$clog2", "clog2")
    try:
        tree = ast.parse(normalized.strip(), mode="eval")
    except SyntaxError as exc:
        raise ValueError("unsupported symbolic constant expression") from exc
    allowed = (ast.Expression, ast.Constant, ast.Name, ast.Load, ast.UnaryOp, ast.UAdd,
               ast.USub, ast.Invert, ast.BinOp, ast.Add, ast.Sub, ast.Mult, ast.Div,
               ast.LShift, ast.RShift, ast.BitAnd, ast.BitOr, ast.BitXor, ast.Mod, ast.Call)
    for node in ast.walk(tree):
        if not isinstance(node, allowed):
            raise ValueError("unsupported symbolic constant expression")
        if isinstance(node, ast.Constant) and type(node.value) is not int:
            raise ValueError("symbolic constant must be integer")
        if isinstance(node, ast.Name) and node.id not in names | {"clog2"}:
            raise ValueError(f"unknown symbolic interface dependency '{node.id}'")
        if isinstance(node, ast.Call) and not (isinstance(node.func, ast.Name) and node.func.id == "clog2" and len(node.args) == 1 and not node.keywords):
            raise ValueError("unsupported symbolic constant function")


def validate_signature(signature: dict) -> None:
    if not isinstance(signature, dict) or set(signature) != {"version", "parameters", "ports", "localparams"} or type(signature["version"]) is not int or signature["version"] != 1:
        raise ValueError("unsupported signature version/fields")
    for key in ("parameters", "ports", "localparams"):
        if not isinstance(signature[key], list):
            raise ValueError(f"signature {key} must be a list")
        names = []
        for item in signature[key]:
            expected = {"name", "type", "default"} if key != "ports" else {"name", "direction", "signed", "dimensions", "value_type"}
            if not isinstance(item, dict) or set(item) != expected or not re.fullmatch(IDENT, item.get("name", "")):
                raise ValueError(f"invalid signature {key} entry")
            names.append(item["name"])
            if key != "ports":
                if not all(isinstance(item[k], str) for k in ("type", "default")) or not item["default"]:
                    raise ValueError("invalid parameter expression/type")
            else:
                if item["direction"] not in ("input", "output", "inout") or type(item["signed"]) is not bool or item["value_type"] not in ("logic", "bit", "int", "integer"):
                    raise ValueError("invalid signature port type")
                if not isinstance(item["dimensions"], list) or any(not isinstance(d, list) or len(d) != 2 or any(not isinstance(b, str) or not b for b in d) for d in item["dimensions"]):
                    raise ValueError("invalid symbolic packed dimensions")
        if len(names) != len(set(names)):
            raise ValueError("duplicate signature name")
    constants = signature["parameters"] + signature["localparams"]
    constant_names = {p["name"] for p in constants}
    if len(constant_names) != len(constants):
        raise ValueError("duplicate public/local parameter name")
    for parameter in constants:
        _validate_expression(parameter["default"], constant_names)
        type_text = parameter["type"]
        ranges = re.findall(r"\[([^\]]+)\]", type_text)
        remainder = re.sub(r"\[[^\]]+\]", "", type_text)
        if any(t not in {"integer", "int", "signed", "unsigned", "logic", "bit", "reg"} for t in remainder.split()):
            raise ValueError("unsupported signature parameter type")
        for range_text in ranges:
            bounds = split_items(range_text, ":")
            if len(bounds) != 2: raise ValueError("parameter packed range needs two bounds")
            for bound in bounds: _validate_expression(bound, constant_names)
    for port in signature["ports"]:
        for bounds in port["dimensions"]:
            for bound in bounds: _validate_expression(bound, constant_names)



def _parameter_declarations(text: str, records: dict, public: list, kind="parameter") -> None:
    inherited = ""
    current_kind = kind
    for part in split_items(text):
        if not part or "=" not in part:
            raise ValueError("parameter needs an explicit integer default")
        marker = re.match(r"^(parameter|localparam)\b", part)
        if marker:
            current_kind = marker[1]
            inherited = ""
            part = part[marker.end():].strip()
        left, right = part.split("=", 1)
        name = re.search(rf"({IDENT})\s*$", left)
        if not name:
            raise ValueError("unsupported parameter declaration")
        prefix = left[:name.start()].strip()
        if prefix:
            inherited = _symbolic(prefix)
        # Only bounded scalar/integer/packed constant parameter types are supported.
        remainder = re.sub(r"\[[^\]]+\]", "", inherited)
        if any(t not in {"integer", "int", "signed", "unsigned", "logic", "bit", "reg"} for t in remainder.split()):
            raise ValueError(f"unsupported parameter type: {inherited}")
        if name[1] in records:
            raise ValueError(f"duplicate or scoped parameter '{name[1]}' unsupported")
        records[name[1]] = {"name": name[1], "type": inherited, "default": _symbolic(right)}
        if current_kind == "parameter":
            public.append(name[1])


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


def _declarations(text: str, values: dict) -> tuple[list[Port], list[dict]]:
    ports, signatures = [], []
    direction, width, signed, dims, symbolic, value_type = None, 1, False, [], [], "logic"
    for item in split_items(text):
        match = re.match(r"^(input|output|inout)\b", item)
        if match:
            direction, width, signed, dims, symbolic, value_type = match[1], 1, False, [], [], "logic"
            explicit_signed = None
            item = item[match.end():].strip()
            while True:
                qualifier = re.match(r"^(wire|reg|logic|bit|var|signed|unsigned|integer|int)\b\s*", item)
                if not qualifier: break
                word = qualifier[1]
                if word in ("integer", "int"):
                    width, signed, value_type = 32, True, word
                elif word == "bit":
                    value_type = "bit"
                elif word in ("signed", "unsigned"):
                    explicit_signed = word == "signed"
                item = item[qualifier.end():]
            if explicit_signed is not None: signed = explicit_signed
            while item.startswith("["):
                end = item.find("]")
                if end < 0: raise ValueError("unterminated packed range")
                bounds = split_items(item[1:end], ":")
                if len(bounds) != 2: raise ValueError("packed range needs two bounds")
                if value_type in ("int", "integer"):
                    raise ValueError("packed dimensions on integer ports unsupported")
                resolved = [integer(b, values) for b in bounds]
                dims.append(resolved)
                symbolic.append([_symbolic(b) for b in bounds])
                item = item[end + 1:].strip()
            if dims:
                width = 1
                for a, b in dims: width *= abs(a-b)+1
            elif width == 32:
                dims, symbolic = [[31, 0]], [["31", "0"]]
        if direction is None or not re.fullmatch(IDENT, item):
            raise ValueError(f"unsupported port declaration: {item}")
        if not 1 <= width <= 65536:
            raise ValueError("port width outside supported range")
        ports.append(Port(item, direction, width, signed=signed, packed_dimensions=[list(d) for d in dims] or None))
        signatures.append({"name":item,"direction":direction,"signed":signed,"dimensions":[list(d) for d in symbolic],"value_type":value_type})
    return ports, signatures


def infer_module(verilog: str, top: str) -> ModuleSpec:
    if not re.fullmatch(IDENT, top):
        raise ValueError("invalid module identifier")
    source = strip_comments(verilog)
    match = re.search(rf"\bmodule\s+{re.escape(top)}\b", source)
    if not match: raise ValueError(f"module name mismatch: expected '{top}'")
    tail = source[match.end():].lstrip()
    records, public = {}, []
    if tail.startswith("#"):
        tail = tail[1:].lstrip()
        group, pos = _group(tail, 0)
        _parameter_declarations(group, records, public)
        tail = tail[pos:].lstrip()
    header, pos = _group(tail, 0)
    body = tail[pos:]
    end = re.search(r"\bendmodule\b", body)
    if end is None: raise ValueError("missing endmodule")
    body = body[:end.start()]
    if not body.lstrip().startswith(";"): raise ValueError("module header missing semicolon")
    for declaration in re.finditer(r"\b(parameter|localparam)\b([^;]+);", body):
        _parameter_declarations(declaration[2], records, public, declaration[1])
    values, resolving = {}, set()
    def resolve(name):
        if name in values: return values[name]
        if name not in records: raise ValueError(f"unknown interface parameter '{name}'")
        if name in resolving: raise ValueError(f"cyclic interface parameter '{name}'")
        resolving.add(name)
        record = records[name]
        for dependency in _dependencies(record["default"]): resolve(dependency)
        value = integer(record["default"], values)
        type_text = record["type"]
        typed_ranges = re.findall(r"\[([^\]]+)\]", type_text)
        bits = 32 if re.search(r"\b(?:int|integer)\b", type_text) else None
        if typed_ranges:
            bits = 1
            for range_text in typed_ranges:
                bounds = split_items(range_text, ":")
                if len(bounds) != 2: raise ValueError("parameter packed range needs two bounds")
                for bound in bounds:
                    for dependency in _dependencies(bound): resolve(dependency)
                a, b = (integer(bound, values) for bound in bounds)
                bits *= abs(a-b)+1
        if bits is not None:
            if not 1 <= bits <= 65536: raise ValueError("parameter width outside supported range")
            value &= (1 << bits) - 1
            is_signed = bool(re.search(r"\b(?:signed|int|integer)\b", type_text)) and not re.search(r"\bunsigned\b", type_text)
            if is_signed and value & (1 << (bits-1)): value -= 1 << bits
        values[name] = value
        resolving.remove(name)
        return values[name]
    for name in public: resolve(name)
    # Resolve interface-referenced locals only. Internal implementation constants are free.
    declaration_text = header if re.search(r"\b(input|output|inout)\b", header) else ",".join(d[0][:-1] for d in re.finditer(r"\b(input|output|inout)\b([^;]+);", body))
    required = set()
    for expression in re.findall(r"\[([^\]]+)\]", declaration_text): required.update(_dependencies(expression))
    for name in public:
        required.update(_dependencies(records[name]["default"]))
        required.update(_dependencies(records[name]["type"]) - {"integer", "int", "signed", "unsigned", "logic", "reg", "bit"})
    for name in required: resolve(name)
    if re.search(r"\b(input|output|inout)\b", header):
        ports, port_signature = _declarations(header, values)
    else:
        names = split_items(header)
        if not all(re.fullmatch(IDENT, name) for name in names):
            raise ValueError("unsupported non-ANSI port list")
        declared, signatures = {}, {}
        for declaration in re.finditer(r"\b(input|output|inout)\b([^;]+);", body):
            parsed, parsed_signatures = _declarations(declaration[0][:-1], values)
            for port, signature in zip(parsed, parsed_signatures):
                if port.name in names:
                    if port.name in declared: raise ValueError("duplicate port declaration")
                    declared[port.name], signatures[port.name] = port, signature
        if set(names) != set(declared): raise ValueError("missing non-ANSI port declarations")
        # Accept separate reg/net declarations only when they repeat the exact
        # interface type. Scalar/vector or signedness merging is ambiguous.
        for statement in body.split(";"):
            net = re.match(r"^\s*(?:wire|reg|logic|bit|integer|int)\b(.*)$", statement, re.S)
            if not net:
                continue
            mentioned = []
            for item in split_items(net[1]):
                declared_name = re.search(rf"({IDENT})\s*(?:=.*)?$", item)
                if declared_name and declared_name[1] in names:
                    mentioned.append(declared_name[1])
            if not mentioned:
                continue
            try:
                _, repeated = _declarations("input " + statement.strip(), values)
                for repeated_signature in repeated:
                    name = repeated_signature["name"]
                    if name not in mentioned:
                        continue
                    repeated_signature["direction"] = signatures[name]["direction"]
                    if repeated_signature != signatures[name]:
                        raise ValueError(f"conflicting port type/shape for '{name}'")
            except ValueError as exc:
                raise ValueError("ambiguous non-ANSI port redeclaration; combine matching signedness and packed bounds with input/output declaration") from exc
        ports, port_signature = [declared[n] for n in names], [signatures[n] for n in names]
    if len({port.name for port in ports}) != len(ports): raise ValueError("duplicate module port")
    seen = set()
    def retain(name):
        if name in seen: return
        if name not in records: raise ValueError(f"unknown symbolic interface dependency '{name}'")
        seen.add(name)
        r = records[name]
        for dependency in _dependencies(r["default"]): retain(dependency)
        for bounds in re.findall(r"\[([^\]]+)\]", r["type"]):
            for dependency in _dependencies(bounds): retain(dependency)
    for name in required: retain(name)
    signature = {"version":1,"parameters":[records[n] for n in public],"ports":port_signature,
                 "localparams":[records[n] for n in sorted(seen-set(public))]}
    validate_signature(signature)
    latency = re.search(r"//\s*@latency\s+(\d+)", verilog)
    reset = "rst_n" if any(p.name == "rst_n" for p in ports) else "rst"
    return ModuleSpec(top, "existing design under optimization", ports,
                      latency=int(latency[1]) if latency else 0,
                      reset=ResetSpec(signal=reset, active_high=reset != "rst_n"),
                      parameters={n:values[n] for n in public}, interface_signature=signature,
                      latency_known=latency is not None)
