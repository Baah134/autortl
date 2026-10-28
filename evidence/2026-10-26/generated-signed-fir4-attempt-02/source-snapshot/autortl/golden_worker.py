"""Restricted oracle interpreter entry point; generated code never runs in the supervisor.

This is a deliberately small Python subset, not a general Python sandbox.
The parent also enforces an execution deadline and strips the environment.
"""
from __future__ import annotations
import ast
import json
import operator
import itertools
import sys

_allocation_left = 100000


def reserve_allocation(count):
    global _allocation_left
    if count > _allocation_left:
        raise ValueError("golden cumulative allocation limit exceeded")
    _allocation_left -= count


def bounded_range(*args):
    result = range(*args)
    if len(result) > 10000:
        raise ValueError("golden range exceeds limit")
    return result


def bounded_list(values=()):
    result = []
    for item in itertools.islice(values, 10001):
        if len(result) >= 10000:
            raise ValueError("golden sequence exceeds limit")
        reserve_allocation(1)
        result.append(item)
    return result


def bounded_tuple(values=()):
    return tuple(bounded_list(values))


def bounded_dict(values=(), **kwargs):
    if isinstance(values, dict):
        if len(values) > 10000:
            raise ValueError("golden mapping exceeds limit")
        reserve_allocation(len(values))
        result = dict(values)
    else:
        result = dict(bounded_list(values))
    result.update(kwargs)
    if len(result) > 10000:
        raise ValueError("golden mapping exceeds limit")
    return result


def bounded_binary(left, right, operation):
    # Python string/bytes % can request an enormous C allocation in one step.
    if operation == "Mod" and (type(left) is not int or type(right) is not int):
        raise ValueError("golden modulo supports only integers")
    if operation in ("LShift", "RShift") and (type(right) is not int or not 0 <= right <= 4096):
        raise ValueError("golden shift exceeds limit")
    if operation == "Mult":
        for sequence, count in ((left, right), (right, left)):
            if isinstance(sequence, (list, tuple, str)) and type(count) is int and len(sequence)*max(0,count) > 10000:
                raise ValueError("golden repetition exceeds limit")
            if isinstance(sequence, (list, tuple, str)) and type(count) is int:
                reserve_allocation(len(sequence)*max(0,count))
    if operation == "Add" and isinstance(left, (list, tuple, str)) and isinstance(right, type(left)):
        if len(left)+len(right) > 10000:
            raise ValueError("golden sequence exceeds limit")
        reserve_allocation(len(left)+len(right))
    functions = {"Add": operator.add, "Sub": operator.sub, "Mult": operator.mul,
                 "FloorDiv": operator.floordiv, "Mod": operator.mod, "BitAnd": operator.and_,
                 "BitOr": operator.or_, "BitXor": operator.xor, "LShift": operator.lshift,
                 "RShift": operator.rshift}
    result = functions[operation](left, right)
    if isinstance(result, int) and result.bit_length() > 4096:
        raise ValueError("golden arithmetic exceeds bit limit")
    return result


def bounded_sum(values, start=0):
    if type(start) is not int:
        raise ValueError("golden sum supports only integers")
    result = start
    for value in values:
        if type(value) is not int:
            raise ValueError("golden sum supports only integers")
        result = bounded_binary(result, value, "Add")
    return result

SAFE_BUILTINS = {name: value for name, value in {
    "abs": abs, "min": min, "max": max, "int": int, "bool": bool,
    "len": len, "range": bounded_range, "enumerate": enumerate, "zip": zip,
    "sum": bounded_sum, "all": all, "any": any, "dict": bounded_dict,
    "list": bounded_list, "tuple": bounded_tuple,
}.items()}
SAFE_METHODS = {"get", "copy", "append", "pop"}
ALLOWED = {
    "Module", "FunctionDef", "arguments", "arg", "Return", "Assign", "AugAssign",
    "If", "IfExp", "For", "While", "Break", "Continue", "Pass", "Expr",
    "Name", "Load", "Store", "Constant", "Dict", "List", "Tuple", "Subscript", "Slice",
    "BinOp", "UnaryOp", "BoolOp", "Compare", "Call", "keyword", "Attribute",
    "Add", "Sub", "Mult", "FloorDiv", "Mod", "BitAnd", "BitOr", "BitXor",
    "LShift", "RShift", "Invert", "Not", "UAdd", "USub", "And", "Or",
    "Eq", "NotEq", "Lt", "LtE", "Gt", "GtE", "In", "NotIn", "Is", "IsNot",
    "GeneratorExp", "comprehension",
}


def validate_source(source: str) -> ast.Module:
    if len(source) > 64000:
        raise ValueError("golden source exceeds 64 KB")
    tree = ast.parse(source)
    funcs = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    if not {"init", "step"} <= funcs:
        raise ValueError("golden model must define init() and step()")
    if len(funcs) != sum(isinstance(node, ast.FunctionDef) for node in tree.body):
        raise ValueError("duplicate golden function")
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            if node.decorator_list or node.args.defaults or node.args.kw_defaults:
                raise ValueError("golden decorators/default arguments are unsupported")
            if node.name == "init" and len(node.args.args) != 0:
                raise ValueError("init must take no arguments")
            if node.name == "step" and len(node.args.args) != 2:
                raise ValueError("step must take state and inputs")
        elif isinstance(node, ast.Assign):
            ast.literal_eval(node.value)  # globals must be inert literals
        elif not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
                  and isinstance(node.value.value, str)):
            raise ValueError("golden top-level execution is unsupported")
    for node in ast.walk(tree):
        if type(node).__name__ not in ALLOWED:
            raise ValueError(f"unsupported golden syntax: {type(node).__name__}")
        if isinstance(node, (ast.Name, ast.arg, ast.FunctionDef)):
            name = node.id if isinstance(node, ast.Name) else node.arg if isinstance(node, ast.arg) else node.name
            if name.startswith("_"):
                raise ValueError("private golden names are unsupported")
        if isinstance(node, ast.Attribute) and node.attr not in SAFE_METHODS:
            raise ValueError(f"unsupported golden attribute: {node.attr}")
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id not in SAFE_BUILTINS and node.func.id not in funcs:
                    raise ValueError(f"unsupported golden call: {node.func.id}")
            elif not isinstance(node.func, ast.Attribute):
                raise ValueError("indirect golden calls are unsupported")
        if isinstance(node, ast.Constant):
            if type(node.value) not in (int, bool, str, type(None)):
                raise ValueError("unsupported golden constant type")
            if isinstance(node.value, int) and node.value.bit_length() > 4096:
                raise ValueError("golden integer literal too large")
            if isinstance(node.value, str) and len(node.value) > 4096:
                raise ValueError("golden string literal too large")
    # Annotations are documentation only; do not evaluate generated expressions.
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            node.returns = None
        if isinstance(node, ast.arg):
            node.annotation = None
    return tree


def execute(source: str, stimulus: list[dict]) -> list[dict]:
    global _allocation_left
    _allocation_left = 100000
    tree = validate_source(source)
    class BoundedArithmetic(ast.NodeTransformer):
        def visit_BinOp(self, node):
            self.generic_visit(node)
            return ast.copy_location(ast.Call(ast.Name("_bounded_binary", ast.Load()),
                                     [node.left, node.right, ast.Constant(type(node.op).__name__)], []), node)

        def visit_AugAssign(self, node):
            # Augmented arithmetic otherwise bypasses the same size guards.
            if not isinstance(node.target, ast.Name):
                raise ValueError("augmented subscript assignment is unsupported; use plain assignment")
            replacement = ast.Assign([node.target], ast.BinOp(
                ast.Name(node.target.id, ast.Load()), node.op, node.value))
            return ast.copy_location(self.visit(replacement), node)

    tree = ast.fix_missing_locations(BoundedArithmetic().visit(tree))
    namespace = {"__builtins__": SAFE_BUILTINS.copy(), "_bounded_binary": bounded_binary}
    remaining = 200000

    def instruction_limit(frame, event, arg):
        nonlocal remaining
        remaining -= 1
        if remaining <= 0:
            raise ValueError("golden instruction budget exhausted")
        return instruction_limit

    sys.settrace(instruction_limit)
    try:
        exec(compile(tree, "<restricted-golden>", "exec"), namespace)
        state = namespace["init"]()
        outputs = []
        for inputs in stimulus:
            state, out = namespace["step"](state, inputs)
            if not isinstance(out, dict) or not all(
                isinstance(k, str) and type(v) is int for k, v in out.items()
            ):
                raise ValueError("golden outputs must map port names to integers")
            outputs.append(dict(out))
        return outputs
    finally:
        sys.settrace(None)


def main() -> None:
    try:
        # Extra OS limits where available; no generated code sees this module.
        try:
            import resource
            resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024,) * 2)
            resource.setrlimit(resource.RLIMIT_CPU, (3, 3))
        except ImportError:
            pass
        request = json.loads(sys.stdin.read(1000001))
        result = execute(request["source"], request["stimulus"])
        encoded = json.dumps({"outputs": result})
        if len(encoded) > 1000000:
            raise ValueError("golden result exceeds size limit")
        print(encoded)
    except Exception as exc:
        print(json.dumps({"error": f"{type(exc).__name__}: {str(exc)[:300]}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
