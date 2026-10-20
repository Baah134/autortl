"""Regressions from the first bounded live tier0 campaign."""
from pathlib import Path
from unittest.mock import Mock
import pytest
from autortl import fsm, roles, vivado
from autortl.taxonomy import Taxonomy
from autortl.report_parser import extract_message_ids
from llm.client import extract_verilog
from tests.test_fsm_resume import configuration, install_models, install_tools


@pytest.mark.parametrize("reply", ["REJECT: vague", "ACCEPTABLE but unverified", ""])
def test_rejected_contract_never_reaches_generation(tmp_path, monkeypatch, reply):
    o = fsm.Orchestrator(configuration(tmp_path), tmp_path / "run")
    install_models(o)
    install_tools(monkeypatch)
    o.evaluator.review_contract = Mock(return_value=reply)
    o.planner.refine_contract = Mock(return_value="revised contract")
    result = o.run()
    assert result["status"] == "contract_blocked"
    assert o.evaluator.review_contract.call_count == 3
    assert o.planner.refine_contract.call_count == 2
    o.generator.generate.assert_not_called()
    assert not (o.state.run_dir / "m_best.v").exists()


@pytest.mark.parametrize("failure", ["LLM_BUDGET: exhausted", "TOOL_BUDGET: exhausted"])
def test_budget_stop_is_saved_without_promotion(tmp_path, monkeypatch, failure):
    o = fsm.Orchestrator(configuration(tmp_path), tmp_path / "run")
    install_models(o)
    install_tools(monkeypatch)
    o.generator.generate.side_effect = RuntimeError(failure)
    result = o.run()
    assert result["status"] == "budget_exhausted"
    assert result["error"] == failure
    assert o.state.read_designs()[0]["iteration"] == 0
    assert len(o.state.read_designs()) == 1
    assert not (o.state.run_dir / "m_best.v").exists()


@pytest.mark.parametrize("source", ["module m; endmodule", "// `timescale 10ns/1ns\nmodule m; endmodule", "/* `timescale 10ns/1ns */\nmodule m; endmodule"])
def test_generated_sources_get_real_default_timescale(source):
    assert roles.generated_rtl("```verilog\n" + source + "\n```").startswith("`timescale 1ns/1ps\n")


def test_explicit_raw_timescale_and_latency_are_retained():
    source = "`timescale 10ns/1ns\n// @latency 3\nmodule m; endmodule"
    assert extract_verilog(source) == source
    assert roles.generated_rtl(source) == source


def test_timescale_log_has_known_repair():
    root = Path(__file__).resolve().parents[1]
    log = (root / "tests/fixtures/xelab_timescale_error.log").read_text()
    assert "XSIM 43-4099" in extract_message_ids(log)
    assert "timescale" in Taxonomy(root / "data/taxonomy.yaml").repair_instruction("XSIM 43-4099")


def test_unsupported_xdc_control_flow_is_promoted():
    root = Path(__file__).resolve().parents[1]
    log = (root / "tests/fixtures/xdc_unsupported_control.log").read_text()
    assert "Designutils 20-1307" in extract_message_ids(log)
    assert Taxonomy(root / "data/taxonomy.yaml").promotions()["Designutils 20-1307"] == "ERROR"


def test_synthesis_constraints_time_io_without_changing_clock():
    script = vivado.SYNTH_TCL.format(promotions="", part="xc7a35tcpg236-1", sources='"m.v"',
                                    workdir="C:/run", period="10.000", top="m", extra_synth="", phys_opt="")
    assert "create_clock -period 10.000" in script
    assert "DIRECTION == IN && NAME != clk" in script
    assert script.index('source "C:/run/timing_io.tcl"') > script.index("synth_design")
    assert 'read_xdc "C:/run/timing_io' not in script
    for direction in ("input", "output"):
        for corner in ("max", "min"):
            assert f"set_{direction}_delay -clock clk -{corner} 0.000" in script
