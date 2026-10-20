"""Contract linter + stub elaboration (Pothole 1 defence).

Runs BEFORE any Verilog generation. Catches bad blueprints:
dangling ports, width mismatches, protocol incompatibilities,
and wiring that Vivado itself cannot elaborate (via black-box stubs).
"""
from __future__ import annotations
from pathlib import Path
from .spec import DesignSpec, ModuleSpec, valid_identifier, port_declaration


def _packed_shape(port):
    return port.packed_dimensions if port.packed_dimensions is not None else ([[port.width - 1, 0]] if port.width > 1 else [])


def _parameter_header(module):
    if not module.parameters:
        return ""
    return " #( " + ", ".join(f"parameter {name} = {value}" for name, value in module.parameters.items()) + " )"


def lint_spec(spec: DesignSpec) -> list[str]:
    """Pure-python structural checks. Returns list of problems (empty = clean)."""
    errs: list[str] = []
    if not valid_identifier(spec.top_name): errs.append("invalid top module identifier")
    module_names = [m.name for m in spec.modules]
    if not spec.modules or len(module_names) != len(set(module_names)):
        errs.append("design must have uniquely named child modules")
    if spec.top_name in module_names: errs.append("top module must differ from child module names")
    external = {p.name: p for p in spec.external_ports}
    if len(external) != len(spec.external_ports): errs.append("duplicate external ports")
    for port in spec.external_ports: errs.extend(port.validate())
    for m in spec.modules:
        errs.extend(m.validate())
    for c in spec.connections:
        src = spec.module(c.src_module)
        dst = spec.module(c.dst_module)
        if src is None:
            errs.append(f"connection: unknown src module '{c.src_module}'"); continue
        if dst is None:
            errs.append(f"connection: unknown dst module '{c.dst_module}'"); continue
        sp = next((p for p in src.ports if p.name == c.src_port), None)
        dp = next((p for p in dst.ports if p.name == c.dst_port), None)
        if sp is None:
            errs.append(f"connection: {c.src_module} has no port '{c.src_port}'"); continue
        if dp is None:
            errs.append(f"connection: {c.dst_module} has no port '{c.dst_port}'"); continue
        if sp.direction != "output":
            errs.append(f"connection: {c.src_module}.{c.src_port} is not an output")
        if dp.direction != "input":
            errs.append(f"connection: {c.dst_module}.{c.dst_port} is not an input")
        if sp.width != dp.width:
            errs.append(f"width mismatch: {c.src_module}.{c.src_port}[{sp.width}] -> "
                        f"{c.dst_module}.{c.dst_port}[{dp.width}]")
        if sp.signed != dp.signed:
            errs.append(f"signedness mismatch: {c.src_module}.{c.src_port} -> {c.dst_module}.{c.dst_port}")
        if _packed_shape(sp) != _packed_shape(dp):
            errs.append(f"packed shape mismatch: {c.src_module}.{c.src_port} -> {c.dst_module}.{c.dst_port}")
        if sp.protocol != dp.protocol:
            errs.append(f"protocol mismatch: {c.src_module}.{c.src_port} ({sp.protocol}) "
                        f"-> {c.dst_module}.{c.dst_port} ({dp.protocol})")
        if sp.clock_domain != dp.clock_domain:
            errs.append(f"clock-domain crossing without CDC module: "
                        f"{c.src_module}.{c.src_port} ({sp.clock_domain}) -> "
                        f"{c.dst_module}.{c.dst_port} ({dp.clock_domain})")
    driven = {(c.dst_module, c.dst_port) for c in spec.connections}
    if len(driven) != len(spec.connections): errs.append("multiple drivers for a module input")
    ext_names = {p.name for p in spec.external_ports}
    for m in spec.modules:
        for p in m.ports:
            if p.direction == "input" and (m.name, p.name) not in driven \
               and p.name not in ext_names:
                errs.append(f"dangling input: {m.name}.{p.name} is never driven "
                            f"and is not an external port")
            if p.name in external and (m.name, p.name) not in driven:
                ext = external[p.name]
                if (p.direction, p.width, p.protocol, p.signed, _packed_shape(p)) != (ext.direction, ext.width, ext.protocol, ext.signed, _packed_shape(ext)):
                    errs.append(f"external binding mismatch: {m.name}.{p.name}")
    for port in spec.external_ports:
        matches = [p for m in spec.modules for p in m.ports if p.name == port.name and p.direction == port.direction]
        if not matches or (port.direction == "output" and len(matches) != 1):
            errs.append(f"external port {port.name} has missing or multiple bindings")
    return errs


def stub_verilog(m: ModuleSpec) -> str:
    if m.interface_signature is not None:
        from .verilog_interface import validate_signature
        signature = m.interface_signature
        validate_signature(signature)
        # Non-ANSI declarations allow interface-dependent localparams to appear
        # before the symbolic port declarations without flattening their shape.
        lines = [f"module {m.name} (" + ", ".join(p["name"] for p in signature["ports"]) + ");"]
        for kind, key in (("parameter", "parameters"), ("localparam", "localparams")):
            for entry in signature[key]:
                prefix = (entry["type"] + " ") if entry["type"] else ""
                lines.append(f"{kind} {prefix}{entry['name']} = {entry['default']};")
        for entry in signature["ports"]:
            ranges = "".join(f"[{left}:{right}]" for left, right in entry["dimensions"])
            dtype = entry["value_type"] if entry["value_type"] in ("int", "integer", "bit") else ""
            declaration = " ".join(part for part in (entry["direction"], "wire", dtype,
                "signed" if entry["signed"] else ("unsigned" if dtype in ("int", "integer") else ""),
                ranges, entry["name"]) if part)
            lines.append(declaration + ";")
        lines.append("endmodule\n")
        return "\n".join(lines)
    ports = ",\n".join(
        "    " + port_declaration(p, include_direction=True)
        for p in m.ports
    )
    return f"module {m.name}{_parameter_header(m)} (\n{ports}\n);\nendmodule\n"


def top_verilog(spec: DesignSpec) -> str:
    """Deterministic, mechanical top-level wiring. Zero LLM involvement."""
    lines = []
    ext = ",\n".join(
        "    " + port_declaration(p, include_direction=True)
        for p in spec.external_ports
    )
    lines.append(f"module {spec.top_name} (\n{ext}\n);")
    declared = set()
    for c in spec.connections:
        src = spec.module(c.src_module)
        sp = next(p for p in src.ports if p.name == c.src_port)
        wname = f"w_{c.src_module}_{c.src_port}"
        if wname not in declared:
            lines.append("    " + port_declaration(sp, name=wname) + ";")
            declared.add(wname)
    for m in spec.modules:
        conns = []
        for p in m.ports:
            as_dst = next((c for c in spec.connections
                           if c.dst_module == m.name and c.dst_port == p.name), None)
            as_src = next((c for c in spec.connections
                           if c.src_module == m.name and c.src_port == p.name), None)
            if as_dst:
                conns.append(f".{p.name}(w_{as_dst.src_module}_{as_dst.src_port})")
            elif as_src:
                conns.append(f".{p.name}(w_{m.name}_{p.name})")
                if any(ext.name == p.name and ext.direction == "output" for ext in spec.external_ports):
                    lines.append(f"    assign {p.name} = w_{m.name}_{p.name};")
            else:
                value = p.name if any(ext.name == p.name for ext in spec.external_ports) else ""
                conns.append(f".{p.name}({value})")
        params = " #( " + ", ".join(f".{name}({value})" for name, value in m.parameters.items()) + " )" if m.parameters else ""
        lines.append(f"    {m.name}{params} u_{m.name} (\n        "
                     + ",\n        ".join(conns) + "\n    );")
    lines.append("endmodule\n")
    return "\n".join(lines)


def write_stub_project(spec: DesignSpec, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    files = []
    for m in spec.modules:
        f = out_dir / f"{m.name}_stub.v"
        f.write_text(stub_verilog(m))
        files.append(f)
    top = out_dir / f"{spec.top_name}.v"
    top.write_text(top_verilog(spec))
    files.append(top)
    return files
