"""Roles are told to infer, not instantiate, device primitives; the message IDs carry repair hints.

Taxonomy: generator_instantiates_unsimulated_primitive (tier1-campaign-02 pwm).
"""
from pathlib import Path

from autortl import prompts
from autortl.taxonomy import Taxonomy

ROOT = Path(__file__).resolve().parents[1]


def test_generator_and_doctor_forbid_named_primitives():
    for system in (prompts.GENERATOR_SYSTEM, prompts.DOCTOR_SYSTEM):
        assert "CARRY4" in system and "never instantiate" in system


def test_missing_module_message_names_the_primitive_cause():
    taxonomy = Taxonomy(ROOT / "data" / "taxonomy.yaml")
    hint = taxonomy.repair_instruction("VRFC 10-2063")
    assert "primitive" in hint and "UNISIM" in hint
    assert "VRFC" in taxonomy.repair_instruction("XSIM 43-3322")
