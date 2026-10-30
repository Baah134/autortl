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


def bounded_copy(value):
    # Every .copy attribute load is wrapped, so a bound copy held in a variable
    # and called later is charged too (golden_sandbox_allocation_and_timeout_gaps).
    method = value.copy

    def charged_copy():
        reserve_allocation(len(value))
        return method()
    return charged_copy


def bounded_slice(value, lower=None, upper=None, step=None):
    span = slice(lower, upper, step)
    if isinstance(value, (list, tuple, str)):
        # Charge the result length before the copy exists; range slicing is O(1).
        reserve_allocation(len(range(len(value))[span]))
    return value[span]


def bounded_slice_assign(new, target, lower=None, upper=None, step=None):
    # Slice assignment can grow a list (a[:0] = a doubles it); charge every new element.
    if isinstance(target, list):
        if isinstance(new, (list, tuple, str)):
            reserve_allocation(len(new))
        else:
            new = bounded_list(new)
    target[slice(lower, upper, step)] = new

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


MAX_SYNTAX_DEPTH = 200


def syntax_depth(tree: ast.AST) -> int:
    """Deepest node nesting, computed iteratively so the check itself cannot recurse."""
    deepest, pending = 0, [(tree, 1)]
    while pending:
        node, depth = pending.pop()
        deepest = max(deepest, depth)
        pending.extend((child, depth + 1) for child in ast.iter_child_nodes(node))
    return deepest


def validate_source(source: str) -> ast.Module:
    if len(source) > 64000:
        raise ValueError("golden source exceeds 64 KB")
    # The supervisor parses model text here. Deeply nested or very long expressions
    # make CPython's parser (and recursive AST consumers such as literal_eval) raise
    # MemoryError or RecursionError, which no caller handles; report them as an
    # ordinary invalid model instead (model_text_overflows_supervisor_parser).
    try:
        return _validate_parsed(source)
    except (MemoryError, RecursionError) as exc:
        raise ValueError("golden source is too deeply nested or complex to parse "
                         f"({type(exc).__name__}); split long expressions into separate statements") from None


def _validate_parsed(source: str) -> ast.Module:
    tree = ast.parse(source)
    if syntax_depth(tree) > MAX_SYNTAX_DEPTH:
        raise ValueError(f"golden source nests deeper than {MAX_SYNTAX_DEPTH} syntax levels; "
                         "split long expressions into separate statements")
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
    # A slice store is charged only as the sole target of a plain assignment, where
    # execute() rewrites it; elsewhere (for-targets, chained or tuple targets) reject it.
    charged_slice_stores = {id(node.targets[0]) for node in ast.walk(tree)
                            if isinstance(node, ast.Assign) and len(node.targets) == 1}
    for node in ast.walk(tree):
        if type(node).__name__ not in ALLOWED:
            raise ValueError(f"unsupported golden syntax: {type(node).__name__}")
        if isinstance(node, ast.FunctionDef) and node.decorator_list:
            # A decorator calls an arbitrary held value; nested functions included.
            raise ValueError("golden decorators are unsupported")
        if (isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Slice)
                and not isinstance(node.ctx, ast.Load) and id(node) not in charged_slice_stores):
            raise ValueError("golden slice assignment is supported only as a single plain assignment target")
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

        @staticmethod
        def slice_bounds(span):
            return [part if part is not None else ast.Constant(None)
                    for part in (span.lower, span.upper, span.step)]

        def visit_Subscript(self, node):
            # Slicing copies; charge it to the cumulative allocation cap.
            self.generic_visit(node)
            if isinstance(node.ctx, ast.Load) and isinstance(node.slice, ast.Slice):
                return ast.copy_location(ast.Call(ast.Name("_bounded_slice", ast.Load()),
                                         [node.value, *self.slice_bounds(node.slice)], []), node)
            return node

        def visit_Attribute(self, node):
            # .copy() copies; wrap the attribute itself so an indirect call is charged too.
            self.generic_visit(node)
            if isinstance(node.ctx, ast.Load) and node.attr == "copy":
                return ast.copy_location(ast.Call(ast.Name("_bounded_copy", ast.Load()),
                                         [node.value], []), node)
            return node

        def visit_Assign(self, node):
            self.generic_visit(node)
            target = node.targets[0]
            if (len(node.targets) == 1 and isinstance(target, ast.Subscript)
                    and isinstance(target.slice, ast.Slice)):
                # Argument order keeps Python's order: value, then target, then bounds.
                call = ast.Call(ast.Name("_bounded_slice_assign", ast.Load()),
                                [node.value, target.value, *self.slice_bounds(target.slice)], [])
                return ast.copy_location(ast.Expr(call), node)
            return node

    tree = ast.fix_missing_locations(BoundedArithmetic().visit(tree))
    namespace = {"__builtins__": SAFE_BUILTINS.copy(), "_bounded_binary": bounded_binary,
                 "_bounded_slice": bounded_slice, "_bounded_slice_assign": bounded_slice_assign,
                 "_bounded_copy": bounded_copy}
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


_job_handle = None  # kept open for the life of the worker


def limit_windows_process_memory(limit_bytes: int) -> bool:
    """Put this process in a Windows Job Object capping its committed memory.

    Windows has no RLIMIT_AS. The worker assigns itself before it reads the
    request, so no generated code runs outside the limit. Returns False, without
    raising, when the platform or the job API refuses (for example, a parent job
    that forbids nesting); the instruction and allocation budgets still apply.
    """
    global _job_handle
    if sys.platform != "win32":
        return False
    try:
        import ctypes
        from ctypes import wintypes

        class IO_COUNTERS(ctypes.Structure):
            _fields_ = [(name, ctypes.c_ulonglong) for name in (
                "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

        class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong),
                        ("PerJobUserTimeLimit", ctypes.c_longlong),
                        ("LimitFlags", wintypes.DWORD),
                        ("MinimumWorkingSetSize", ctypes.c_size_t),
                        ("MaximumWorkingSetSize", ctypes.c_size_t),
                        ("ActiveProcessLimit", wintypes.DWORD),
                        ("Affinity", ctypes.c_size_t),
                        ("PriorityClass", wintypes.DWORD),
                        ("SchedulingClass", wintypes.DWORD)]

        class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
                        ("IoInfo", IO_COUNTERS),
                        ("ProcessMemoryLimit", ctypes.c_size_t),
                        ("JobMemoryLimit", ctypes.c_size_t),
                        ("PeakProcessMemoryUsed", ctypes.c_size_t),
                        ("PeakJobMemoryUsed", ctypes.c_size_t)]

        job_object_extended_limit_information = 9
        job_object_limit_process_memory = 0x00000100
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        kernel32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int,
                                                     ctypes.c_void_p, wintypes.DWORD]
        kernel32.SetInformationJobObject.restype = wintypes.BOOL
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        job = kernel32.CreateJobObjectW(None, None)
        if not job:
            return False
        info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.BasicLimitInformation.LimitFlags = job_object_limit_process_memory
        info.ProcessMemoryLimit = limit_bytes
        if not (kernel32.SetInformationJobObject(job, job_object_extended_limit_information,
                                                 ctypes.byref(info), ctypes.sizeof(info))
                and kernel32.AssignProcessToJobObject(job, kernel32.GetCurrentProcess())):
            kernel32.CloseHandle(job)
            return False
        _job_handle = job
        return True
    except Exception:
        return False


def main() -> None:
    try:
        # Extra OS limits where available; no generated code sees this module.
        try:
            import resource
            resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024,) * 2)
            resource.setrlimit(resource.RLIMIT_CPU, (3, 3))
        except ImportError:
            limit_windows_process_memory(256 * 1024 * 1024)
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
