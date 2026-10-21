"""Best-of-N generation: objective-weighted mutations, dedupe, deterministic selection.

Same-model candidates converge (Pothole 3), so mutation prompts are the ONLY
diversity mechanism under a single-provider setup. Portfolio is drawn from a
weighted table per objective: mostly objective-aligned, one wildcard always.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from .cache import code_hash
from .objectives import timing_feasible
import math

MUTATIONS = {
    "standard":    "Implement using clean, standard sequential logic.",
    "pipeline":    "Improve frequency by balancing logic within the existing pipeline stages, retiming existing registers only where cycle behavior is preserved, and factoring the critical path within the current cycle budget. Keep the existing @latency declaration unchanged.",
    "share":       "Minimise area by factoring common expressions or sharing mutually exclusive operations within the current cycle budget. Share across cycles only when the original schedule already permits it without changing any accepted input or output cycle.",
    "narrow":      "Minimise LUTs using mathematically proven width reductions across the full legal input and parameter range. Preserve high-bit effects on comparisons, signedness, wraparound, and overflow.",
    "infer":       "Implement using behavioral inference so Vivado maps arithmetic to DSP48 and memories to BRAM (e.g. (* ram_style = \"block\" *)); follow Xilinx inference coding patterns.",
    "wildcard":    "Implement from scratch with a fundamentally different structure than the obvious one; do not reference any provided template.",
}

TRANSFORMATION_CONTRACT = (
    " Preserve observable latency, throughput, interface, reset semantics, and parameter behavior."
    " Preserve registered versus combinational outputs and cycle-by-cycle control priorities."
    " Do not add pipeline stages, extra cycles, new clock domains, or RTL delay chains."
)

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
    return [(name, MUTATIONS[name] + TRANSFORMATION_CONTRACT) for name in names]


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
    """Rank by completed rungs, timing feasibility, objective, then code length."""
    alive = [c for c in cands if c.alive]
    if not alive:
        return None
    key_metric = {
        "minimize_luts":  lambda m: m.get("lut_used", 10**9),
        "minimize_ffs":   lambda m: m.get("ff_used", 10**9),
        "maximize_freq":  lambda m: -m.get("wns_ns", -10**9),
        "minimize_power": lambda m: m.get("dynamic_power_w", 10**9),
    }.get(objective, lambda m: m.get("lut_used", 10**9))
    def objective_score(metrics):
        try:
            value = key_metric(metrics)
            return value if type(value) in (int, float) and math.isfinite(value) else float("inf")
        except (TypeError, ValueError, OverflowError):
            return float("inf")
    alive.sort(key=lambda c: (-c.ladder_rungs_passed,
                              not timing_feasible(c.metrics),
                              objective_score(c.metrics),
                              len(c.verilog)))
    return alive[0]
