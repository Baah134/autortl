"""Device budgets loaded from data/parts.yaml.

Injected into planner + contract-negotiation prompts so no plan or contract
can be written that exceeds the physical part. Advisory to the planner;
the metrics gate remains the hard enforcer of used<=total at run time.
"""
from __future__ import annotations
from pathlib import Path
try:
    import yaml
except ImportError:
    yaml = None

_PARTS_PATH = Path(__file__).resolve().parent.parent / "data" / "parts.yaml"


def budget_for(part: str) -> dict | None:
    if not (yaml and _PARTS_PATH.exists()):
        return None
    data = yaml.safe_load(_PARTS_PATH.read_text()) or {}
    return (data.get("parts") or {}).get(part)


def budget_text(part: str) -> str:
    """One-line-per-resource budget block for prompts. Empty if unknown part."""
    b = budget_for(part)
    if not b:
        return ""
    return (f"Device budget for {part}: "
            f"LUTs={b.get('luts','?')}, FFs={b.get('ffs','?')}, "
            f"DSP48={b.get('dsp48','?')}, BRAM36k={b.get('bram_36k','?')}, "
            f"max practical freq ~{b.get('max_practical_freq_mhz','?')} MHz, "
            f"logic-level budget @100MHz ~{b.get('lut_levels_at_100mhz','?')}.")
