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


def test_generator_is_told_the_language_and_the_concatenation_rule():
    # generator_selects_from_concatenation (contract-campaign-20 mux4)
    assert "Verilog-2001" in prompts.GENERATOR_SYSTEM and "concatenation" in prompts.GENERATOR_SYSTEM
    taxonomy = Taxonomy(ROOT / "data" / "taxonomy.yaml")
    assert "concatenation" in taxonomy.repair_instruction("VRFC 10-4982")
    assert "earlier" in taxonomy.repair_instruction("VRFC 10-8530")
