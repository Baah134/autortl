import json
import pytest
from autortl.spec import DesignSpec, ModuleSpec, Port, ResetSpec, Connection, IOExample


def make_module(name="adder", **kw):
    return ModuleSpec(
        name=name, behavior="adds two numbers",
        ports=[Port("clk", "input", 1), Port("rst", "input", 1),
               Port("a", "input", 8), Port("b", "input", 8),
               Port("y", "output", 9)],
        latency=1, **kw)


def test_valid_module_passes():
    assert make_module().validate() == []


def test_bad_direction_caught():
    m = make_module()
    m.ports[2].direction = "sideways"
    assert any("bad direction" in e for e in m.validate())


def test_bad_width_caught():
    m = make_module()
    m.ports[2].width = 0
    assert any("width" in e for e in m.validate())


def test_duplicate_ports_caught():
    m = make_module()
    m.ports.append(Port("a", "input", 8))
    assert any("duplicate" in e for e in m.validate())


def test_pulse_compare_mode_rejected():
    m = make_module(compare_mode="pulse")
    assert any("unsupported" in e for e in m.validate())


def test_contract_hash_stable_and_sensitive():
    a, b = make_module(), make_module()
    assert a.contract_hash() == b.contract_hash()
    b.ports[2].width = 16
    assert a.contract_hash() != b.contract_hash()
    c = make_module()
    c.behavior = "subtracts two numbers"     # behavior change must change hash
    assert a.contract_hash() != c.contract_hash()


def test_json_roundtrip():
    spec = DesignSpec(top_name="top", modules=[make_module()],
                      connections=[], external_ports=[Port("clk", "input", 1)])
    spec2 = DesignSpec.from_json(spec.to_json())
    assert spec2.top_name == "top"
    assert spec2.modules[0].name == "adder"
    assert spec2.modules[0].ports[2].width == 8


def test_latency_known_defaults_true_for_existing_typed_specs():
    spec = DesignSpec(top_name="top", modules=[make_module()])
    raw = json.loads(spec.to_json())
    raw["modules"][0].pop("latency_known")
    restored = DesignSpec.from_json(json.dumps(raw)).modules[0]
    assert restored.latency_known is True and restored.validate() == []


@pytest.mark.parametrize("known", [False, 0, 1, "false", None])
def test_typed_build_requires_explicitly_known_boolean_latency(known):
    module = make_module(latency_known=known)
    errors = module.validate()
    assert any("latency" in error for error in errors)


def test_latency_known_changes_contract_hash_and_roundtrips_without_coercion():
    known = make_module()
    unknown = make_module(latency_known=False)
    assert known.contract_hash() != unknown.contract_hash()
    restored = DesignSpec.from_json(DesignSpec(top_name="top", modules=[unknown]).to_json())
    assert restored.modules[0].latency_known is False
