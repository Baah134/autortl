"""Best-of-N generation: objective-weighted mutations, dedupe, deterministic selection.

Same-model candidates converge (Pothole 3), so mutation prompts are the ONLY
diversity mechanism under a single-provider setup. Portfolio is drawn from a
weighted table per objective: mostly objective-aligned, one wildcard always.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from .cache import code_hash

MUTATIONS = {
    "standard":    "Implement using clean, standard sequential logic.",
    "pipeline":    "Implement heavily pipelined to maximise clock frequency; add pipeline registers on long combinational paths and declare the new latency in a '// @latency N' header comment.",
    "share":       "Implement minimising area by sharing resources: reuse one arithmetic operator across cycles with a small FSM where possible.",
    "narrow":      "Implement minimising LUTs by narrowing every comparison and arithmetic operation to the fewest bits mathematically required.",
    "infer":       "Implement using behavioral inference so Vivado maps arithmetic to DSP48 and memories to BRAM (e.g. (* ram_style = \"block\" *)); follow Xilinx inference coding patterns.",
    "wildcard":    "Implement from scratch with a fundamentally different structure than the obvious one; do not reference any provided template.",
}

PORTFOLIO = {
    "minimize_luts":  ["standard", "narrow", "share", "wildcard"],
    "minimize_ffs":   ["standard", "share", "narrow", "wildcard"],
    "maximize_freq":  ["standard", "pipeline", "infer", "wildcard"],
    "minimize_power": ["standard", "share", "narrow", "wildcard"],
}


@dataclass
class Candidate:
    verilog: str
    mutation: str
    ladder_rungs_passed: int = 0
    metrics: dict = field(default_factory=dict)
    alive: bool = True
    fail_reason: str = ""


def mutation_prompts(objective: str, n: int) -> list[tuple[str, str]]:
    names = PORTFOLIO.get(objective, PORTFOLIO["minimize_luts"])[:max(1, n)]
    return [(name, MUTATIONS[name]) for name in names]


def dedupe(cands: list[Candidate]) -> list[Candidate]:
    seen: dict[str, Candidate] = {}
    for c in cands:
        h = code_hash(c.verilog)
        if h not in seen:
            seen[h] = c
        else:
            c.alive = False
            c.fail_reason = f"duplicate of '{seen[h].mutation}' candidate"
    return [c for c in cands if c.alive]


def select(cands: list[Candidate], objective: str) -> Candidate | None:
    """Deterministic: rank by (rungs passed desc, objective metric, code length)."""
    alive = [c for c in cands if c.alive]
    if not alive:
        return None
    key_metric = {
        "minimize_luts":  lambda m: m.get("lut_used", 10**9),
        "minimize_ffs":   lambda m: m.get("ff_used", 10**9),
        "maximize_freq":  lambda m: -m.get("wns_ns", -10**9),
        "minimize_power": lambda m: m.get("dynamic_power_w", 10**9),
    }.get(objective, lambda m: m.get("lut_used", 10**9))
    alive.sort(key=lambda c: (-c.ladder_rungs_passed,
                              key_metric(c.metrics),
                              len(c.verilog)))
    return alive[0]
