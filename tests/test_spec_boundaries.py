import pytest

from autortl.linter import lint_spec
from autortl.spec import DesignSpec, ModuleSpec, Port


def design():
    return DesignSpec(
        "top", [ModuleSpec("child", "pass through", [Port("x", "input", 8), Port("y", "output", 8)])],
        external_ports=[Port("x", "input", 8), Port("y", "output", 8)],
    )


@pytest.mark.parametrize("name", ["../outside", "top;exec", "top[cmd]", "top$var", "тop", "top name"])
def test_model_identifiers_cannot_escape_paths_or_tcl(name):
    spec = design()
    spec.top_name = name
    assert lint_spec(spec)
    spec = design()
    spec.modules[0].name = name
    assert lint_spec(spec)


def test_external_widths_drivers_and_missing_reset_are_rejected():
    spec = design()
    spec.external_ports[0].width = 1
    assert any("binding mismatch" in error for error in lint_spec(spec))
    spec = design()
    spec.modules[0].ports.append(Port("rst", "input", 1))
    assert any("dangling input" in error for error in lint_spec(spec))
    spec = design()
    spec.modules[0].name = spec.top_name
    assert any("differ" in error for error in lint_spec(spec))
