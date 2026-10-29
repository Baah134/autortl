"""An optimize seed without a timescale is verified without a model repair.

Taxonomy: seed_without_timescale_costs_model_repair (tier1-campaign-01 pwm).
"""
from pathlib import Path
from unittest.mock import Mock

from autortl import fsm
from autortl.roles import default_timescale
from autortl.triage import FailureKind
from tests.test_fsm_resume import SOURCE, configuration, install_models, install_tools


def test_default_timescale_only_when_none_is_declared():
    assert default_timescale(SOURCE) == "`timescale 1ns/1ps\n" + SOURCE
    explicit = "`timescale 1ns/100ps\n" + SOURCE
    assert default_timescale(explicit) == explicit
    commented = "// `timescale 1ns/1ps\n" + SOURCE
    assert default_timescale(commented).startswith("`timescale 1ns/1ps\n")


def test_seed_without_timescale_reaches_baseline_without_a_repair_call(tmp_path, monkeypatch):
    cfg = configuration(tmp_path)  # SOURCE declares no timescale
    o = fsm.Orchestrator(cfg, tmp_path / "run")
    install_models(o)
    monkeypatch.setattr(o.generator, "fix", Mock(side_effect=AssertionError("no model repair for a timescale")))
    install_tools(monkeypatch)
    passing = fsm.vivado.xsim_run

    def xelab_like(files, tb, top, config, work, **kwargs):
        # Mocked candidates skip generated_rtl (which adds the default), so only
        # the baseline is held to xelab's rule here.
        if "iter_000" in str(work) and not all("`timescale" in Path(f).read_text(encoding="utf-8") for f in files):
            return False, "ERROR: [XSIM 43-4099] Module m doesn't have a timescale", FailureKind.DESIGN
        return passing(files, tb, top, config, work, **kwargs)

    monkeypatch.setattr(fsm.vivado, "xsim_run", xelab_like)
    summary = o.run()
    assert summary["status"] == "done"
    baseline = (o.state.run_dir / "iter_000" / "m.v").read_text(encoding="utf-8")
    assert baseline == "`timescale 1ns/1ps\n" + SOURCE
