"""Typed design spec schema. The spec is machine-checkable law.

A design_spec.json describes a module tree. Every field the linter,
testbench generator, and skill loader rely on is REQUIRED and typed here.
"""
from __future__ import annotations
import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path

PROTOCOLS = {"none", "valid_ready", "pulse", "level"}
DIRECTIONS = {"input", "output", "inout"}
RESET_KINDS = {"sync", "async"}
COMPARE_MODES = {"fixed_latency", "scoreboard"}   # pulse mode intentionally stubbed


def valid_identifier(value) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value) is not None


@dataclass
class Port:
    name: str
    direction: str            # input|output|inout
    width: int                # resolved integer width, >=1
    clock_domain: str = "clk"
    protocol: str = "none"
    signed: bool = False
    packed_dimensions: list[list[int]] | None = None

    def validate(self) -> list[str]:
        errs = []
        if not valid_identifier(self.name):
            errs.append(f"invalid Verilog port identifier: {self.name}")
        if self.direction not in DIRECTIONS:
            errs.append(f"port {self.name}: bad direction '{self.direction}'")
        if type(self.width) is not int or not 1 <= self.width <= 65536:
            errs.append(f"port {self.name}: width must be int >= 1 (got {self.width})")
        if type(self.signed) is not bool:
            errs.append(f"port {self.name}: signed must be boolean")
        if self.packed_dimensions is not None:
            dims = self.packed_dimensions
            if not isinstance(dims, list) or not dims or any(
                not isinstance(d, list) or len(d) != 2 or any(type(n) is not int for n in d)
                for d in dims
            ):
                errs.append(f"port {self.name}: packed_dimensions must be nonempty integer bound pairs")
            else:
                size = 1
                for left, right in dims:
                    size *= abs(left - right) + 1
                if size != self.width:
                    errs.append(f"port {self.name}: packed_dimensions do not match width")
        if self.protocol not in PROTOCOLS:
            errs.append(f"port {self.name}: unknown protocol '{self.protocol}'")
        return errs


def port_declaration(port: Port, storage="wire", *, include_direction=False, name=None) -> str:
    """Render a resolved port without losing signedness or packed index order."""
    errors = port.validate()
    if errors:
        raise ValueError("; ".join(errors))
    if storage not in ("wire", "reg", "logic", ""):
        raise ValueError("unsupported declaration storage")
    identifier = port.name if name is None else name
    if not valid_identifier(identifier):
        raise ValueError("invalid declaration identifier")
    dimensions = port.packed_dimensions
    if dimensions is None:
        dimensions = [[port.width - 1, 0]] if port.width > 1 else []
    ranges = "".join(f"[{a}:{b}]" for a, b in dimensions)
    return " ".join(part for part in (
        port.direction if include_direction else "", storage,
        "signed" if port.signed else "", ranges, identifier) if part)


@dataclass
class ResetSpec:
    signal: str = "rst"
    kind: str = "sync"
    active_high: bool = True
    duration_cycles: int = 5

    def validate(self) -> list[str]:
        errors = [] if self.kind in RESET_KINDS else [f"reset kind '{self.kind}' invalid"]
        if not valid_identifier(self.signal): errors.append("invalid reset signal identifier")
        if type(self.active_high) is not bool: errors.append("reset polarity must be boolean")
        if type(self.duration_cycles) is not int or not 1 <= self.duration_cycles <= 1000:
            errors.append("reset duration must be 1..1000 cycles")
        return errors


@dataclass
class IOExample:
    inputs: dict
    expected: dict
    after_cycles: int = 1


@dataclass
class ModuleSpec:
    name: str
    behavior: str
    ports: list[Port]
    latency: int = 0
    compare_mode: str = "fixed_latency"
    reset: ResetSpec = field(default_factory=ResetSpec)
    clock_domains: list[str] = field(default_factory=lambda: ["clk"])
    parameters: dict = field(default_factory=dict)
    examples: list[IOExample] = field(default_factory=list)
    golden_model: str = ""
    interface_signature: dict | None = None
    latency_known: bool = True

    def contract_hash(self) -> str:
        import hashlib
        blob = json.dumps({
            "name": self.name, "behavior": self.behavior,
            "ports": [asdict(p) for p in self.ports],
            "latency": self.latency, "latency_known": self.latency_known, "compare_mode": self.compare_mode,
            "reset": asdict(self.reset), "params": list(self.parameters.items()),
            "interface_signature": self.interface_signature,
        }, sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()[:16]

    def validate(self) -> list[str]:
        errs = []
        if not valid_identifier(self.name):
            errs.append(f"module name '{self.name}' is not a valid identifier")
        if not self.behavior.strip():
            errs.append(f"module {self.name}: behavior description empty")
        if self.compare_mode not in COMPARE_MODES:
            errs.append(f"module {self.name}: compare_mode '{self.compare_mode}' "
                        f"unsupported (pulse mode is stubbed in v4.0)")
        names = [p.name for p in self.ports]
        if len(names) != len(set(names)):
            errs.append(f"module {self.name}: duplicate port names")
        for p in self.ports:
            errs.extend(p.validate())
            if p.clock_domain not in self.clock_domains:
                errs.append(f"module {self.name}: port {p.name} references "
                            f"unknown clock domain '{p.clock_domain}'")
        errs.extend(self.reset.validate())
        if type(self.latency) is not int or not 0 <= self.latency <= 1024:
            errs.append(f"module {self.name}: latency must be an integer in 0..1024")
        if type(self.latency_known) is not bool:
            errs.append(f"module {self.name}: latency_known must be boolean")
        elif not self.latency_known:
            errs.append(f"module {self.name}: typed build specs require a known numeric latency")
        if not all(valid_identifier(name) and type(value) is int for name, value in self.parameters.items()):
            errs.append(f"module {self.name}: parameter names/defaults must be valid identifiers/integers")
        if self.interface_signature is not None:
            try:
                from .verilog_interface import validate_signature
                validate_signature(self.interface_signature)
            except (ValueError, TypeError, KeyError) as exc:
                errs.append(f"module {self.name}: invalid interface signature: {exc}")
        return errs


@dataclass
class Connection:
    src_module: str
    src_port: str
    dst_module: str
    dst_port: str


@dataclass
class DesignSpec:
    top_name: str
    modules: list[ModuleSpec]
    connections: list[Connection] = field(default_factory=list)
    external_ports: list[Port] = field(default_factory=list)

    def module(self, name: str) -> ModuleSpec | None:
        return next((m for m in self.modules if m.name == name), None)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    @staticmethod
    def from_json(text: str) -> "DesignSpec":
        raw = json.loads(text)
        mods = []
        for m in raw["modules"]:
            ports = [Port(**p) for p in m.pop("ports")]
            reset = ResetSpec(**m.pop("reset", {}))
            examples = [IOExample(**e) for e in m.pop("examples", [])]
            mods.append(ModuleSpec(ports=ports, reset=reset, examples=examples, **m))
        conns = [Connection(**c) for c in raw.get("connections", [])]
        ext = [Port(**p) for p in raw.get("external_ports", [])]
        return DesignSpec(top_name=raw["top_name"], modules=mods,
                          connections=conns, external_ports=ext)

    @staticmethod
    def load(path: Path) -> "DesignSpec":
        return DesignSpec.from_json(Path(path).read_text())
