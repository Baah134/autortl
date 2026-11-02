"""Out-of-context implementation for a block that is not a chip top.

Taxonomy: chip_top_flow_for_soc_block. Report fixtures (tests/fixtures/ooc) are
real Vivado 2025.2 output of the same out-of-context clock, synthesis and
place/route commands, for the dot4_pipeline winner at 10 ns on
xc7a35tcpg236-1 (evidence/2026-10-29/fmax-characterization-01, sweep
dot4_pipeline/ooc/p10.000; critical_path.rpt is its one-path report_timing).
"""
import json
import shutil
from pathlib import Path

import pytest
import yaml

import run
from autortl import fsm, vivado
from autortl.config import RunConfig
from autortl.contract_context import render_fixed_optimize_contract, run_evidence
from autortl.report_parser import VivadoMetrics, parse_all
from autortl.metrics_gate import validate
from curriculum import runner
from tests.test_curriculum import curriculum  # noqa: F401
from tests.test_doctor_fsm import lineage  # noqa: F401

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "ooc"

# The complete out-of-context script for one source, no promotions, default knobs
# (the synth_design line ends in the empty knob slot's space, written \x20).
OOC_GOLDEN = """\

set_part xc7a35tcpg236-1
read_verilog "S/m.v"
set fp [open "W/timing.xdc" w]
puts $fp {create_clock -period 10.000 -name clk [get_ports clk]}
puts $fp {set_property HD.CLK_SRC BUFGCTRL_X0Y0 [get_ports clk]}
close $fp
read_xdc "W/timing.xdc"
synth_design -top m -flatten_hierarchy rebuilt -mode out_of_context\x20
report_utilization -file "W/utilization.rpt"
report_timing_summary -file "W/timing.rpt"
opt_design
place_design

route_design
report_utilization -file "W/utilization_routed.rpt"
report_timing_summary -file "W/timing_routed.rpt"
catch { if {[llength [all_registers]] > 0} { report_timing -from [all_registers] -to [all_registers] -max_paths 1 -file "W/timing_reg2reg.rpt" } }
report_design_analysis -logic_level_distribution -file "W/design_analysis.rpt"
report_power -file "W/power.rpt"
catch { report_methodology -file "W/methodology.rpt" }
catch { report_qor_suggestions -file "W/qor_suggestions.rpt" }
puts "SYNTH_COMPLETE"
"""


def script(tmp_path, monkeypatch, implementation, **knobs):
    monkeypatch.setattr(vivado, "_run", lambda *a: (0, "SYNTH_COMPLETE"))
    sources = tmp_path / "src"
    work = tmp_path / "work"
    sources.mkdir()
    work.mkdir()
    source = sources / "m.v"
    source.write_text("module m(input clk); endmodule")
    cfg = RunConfig(mode="optimize", implementation=implementation)
    ok, _, _ = vivado.run_synthesis([source], "m", cfg, work, **knobs)
    assert ok
    text = (work / "synth.tcl").read_text()
    # Paths stay forward-slash absolute (CLAUDE.md); normalized here for the golden text.
    assert "\\" not in text and vivado._tcl_path(work).startswith(str(tmp_path.resolve()).replace("\\", "/"))
    return text.replace(vivado._tcl_path(work), "W").replace(vivado._tcl_path(sources), "S")


def test_out_of_context_script_is_exactly_the_golden_template(tmp_path, monkeypatch):
    assert script(tmp_path, monkeypatch, "out_of_context") == OOC_GOLDEN


def test_out_of_context_has_no_io_buffers_or_io_delays(tmp_path, monkeypatch):
    text = script(tmp_path, monkeypatch, "out_of_context")
    assert "set_input_delay" not in text and "set_output_delay" not in text
    assert "timing_io.tcl" not in text  # no I/O constraint file: data ports stay unconstrained
    order = ["synth_design", "opt_design", "place_design", "route_design", "timing_routed.rpt",
             "timing_reg2reg.rpt", "SYNTH_COMPLETE"]
    assert [text.index(step) for step in order] == sorted(text.index(step) for step in order)


def test_chip_top_script_is_unchanged(tmp_path, monkeypatch):
    text = script(tmp_path, monkeypatch, "chip_top")
    expected = vivado.SYNTH_TCL.format(promotions="", part="xc7a35tcpg236-1", sources='"S/m.v"', workdir="W",
                                       period="10.000", top="m", extra_synth="", phys_opt="")
    assert text == expected
    assert "out_of_context" not in text and "HD.CLK_SRC" not in text
    assert "puts $fp {if {[llength [all_outputs]] > 0} {set_output_delay -clock clk -max 0.000" in text


@pytest.mark.parametrize("knobs,synth,phys", [
    ({"retiming": True, "phys_opt": True}, "-mode out_of_context -retiming", "phys_opt_design"),
    ({"hold_fix": True}, "-mode out_of_context \n", "phys_opt_design -hold_fix"),
])
def test_doctor_knobs_apply_out_of_context(tmp_path, monkeypatch, knobs, synth, phys):
    text = script(tmp_path, monkeypatch, "out_of_context", **knobs)
    assert synth in text
    assert "\n" + phys + "\n" in text


def test_out_of_context_reports_still_parse_into_valid_metrics(tmp_path):
    shutil.copy(FIXTURES / "timing_routed.rpt", tmp_path / "timing_routed.rpt")
    shutil.copy(FIXTURES / "utilization_routed.rpt", tmp_path / "utilization_routed.rpt")
    shutil.copy(FIXTURES / "critical_path.rpt", tmp_path / "timing_reg2reg.rpt")
    m = parse_all(tmp_path)
    assert (m.wns_ns, m.whs_ns, m.timing_met) == (7.267, 0.346, True)
    assert (m.lut_used, m.lut_total, m.ff_used, m.ff_total) == (17, 20800, 18, 41600)
    assert m.reg2reg_wns_ns == 7.267  # no pad paths: the worst path is register to register
    validate(m, synthesis_ran=True)
    # Utilization excludes I/O buffers: no IOB is used out of context.
    assert "| Bonded IOB                  |    0 |" in (FIXTURES / "utilization_routed.rpt").read_text()


def test_config_default_validation_and_old_checkpoints():
    assert RunConfig(mode="optimize").implementation == "chip_top"
    with pytest.raises(ValueError, match="implementation"):
        RunConfig(mode="optimize", implementation="ooc").validate()
    old = RunConfig(mode="optimize").to_dict()
    del old["implementation"]  # saved before the flow existed: it implemented a chip top
    assert RunConfig.from_dict(old).implementation == "chip_top"
    saved = RunConfig(mode="build", implementation="out_of_context").to_dict()
    assert RunConfig.from_dict(saved).implementation == "out_of_context"


@pytest.fixture
def orchestrator(monkeypatch):
    from unittest.mock import Mock
    cls = Mock()
    cls.return_value.run.return_value = {"status": "done"}
    monkeypatch.setattr(run, "Orchestrator", cls)
    return cls


@pytest.mark.parametrize("command", [["optimize", "--design", "d.v", "--top", "d"], ["build", "--spec", "s.json"]])
def test_cli_flag_reaches_the_saved_config(orchestrator, command):
    assert run.main(command + ["--implementation", "out_of_context"]) == 0
    assert orchestrator.call_args.args[0].implementation == "out_of_context"
    assert run.main(command) == 0
    assert orchestrator.call_args.args[0].implementation == "chip_top"


def test_cli_refuses_any_other_flow_name(orchestrator):
    with pytest.raises(SystemExit):
        run.main(["optimize", "--design", "d.v", "--top", "d", "--implementation", "x; rm -rf"])
    with pytest.raises(SystemExit):  # a bench takes it from each entry's meta.yaml, never a flag
        run.main(["bench", "--tier", "0", "--implementation", "out_of_context"])
    orchestrator.assert_not_called()


def test_resume_refuses_a_changed_flow(tmp_path, monkeypatch):
    from tests.test_fsm_resume import configuration
    cfg = configuration(tmp_path)
    first = fsm.Orchestrator(cfg, tmp_path / "run")
    first._prepare_inputs()
    changed = RunConfig.load(tmp_path / "run" / "config.json")
    changed.implementation = "out_of_context"
    with pytest.raises(ValueError, match="Resume configuration changed: implementation"):
        fsm.Orchestrator(changed, tmp_path / "run")._prepare_inputs()


def test_cache_context_binds_the_flow(tmp_path):
    chip = fsm.Orchestrator(RunConfig(mode="optimize", top_module="m"), tmp_path / "a")._cache_context(None, [])
    ooc = fsm.Orchestrator(RunConfig(mode="optimize", top_module="m", implementation="out_of_context"),
                           tmp_path / "b")._cache_context(None, [])
    assert (chip["implementation"], ooc["implementation"]) == ("chip_top", "out_of_context")
    assert chip["synthesis_template"] != ooc["synthesis_template"]


@pytest.mark.parametrize("implementation", ["chip_top", "out_of_context"])
def test_contract_states_the_flow(tmp_path, implementation):
    design, tb = tmp_path / "m.v", tmp_path / "m_tb.v"
    design.write_text("module m(input clk, output y); assign y = 1'b0; endmodule")
    tb.write_text("module m_tb; endmodule")
    cfg = RunConfig(mode="optimize", top_module="m", design_path=design, testbench_path=tb,
                    implementation=implementation)
    facts = run_evidence(cfg, VivadoMetrics(), [design], tb, tmp_path, {})
    assert facts["implementation"]["mode"] == implementation
    contract = render_fixed_optimize_contract(facts)
    assert f"## Implementation flow\n\nMode {implementation}, fixed by the harness." in contract
    if implementation == "out_of_context":
        assert "synth_design -mode out_of_context" in contract
        assert "Utilization excludes I/O buffers" in contract
        assert "cover the internal clocked paths only" in contract
    else:
        assert "zero input and output delay" in contract and "include pad delay" in contract
    assert f'"mode": "{implementation}"' in contract  # also in the fixed measurement authority JSON


def test_metadata_flow_reaches_the_entry_config_and_cohort(curriculum):  # noqa: F811
    root, orch, output = curriculum
    meta_path = root / "tier0" / "a" / "meta.yaml"
    meta = yaml.safe_load(meta_path.read_text())
    meta_path.write_text(yaml.safe_dump({**meta, "implementation": "out_of_context"}))
    runner.run_tier(0, output_root=output)
    flows = {call.args[0].implementation for call in orch.call_args_list}
    assert flows == {"chip_top", "out_of_context"}
    record = [json.loads(line) for line in runner.RESULTS.read_text().splitlines()][-1]
    entry = next(r for r in record["results"] if r["entry"] == "a")
    assert entry["config"]["implementation"] == "out_of_context"
    meta_path.write_text(yaml.safe_dump({**meta, "implementation": "partial"}))
    with pytest.raises(ValueError, match="implementation must be one of"):
        runner._metadata(meta_path.parent)


def test_doctor_default_flow_proof_follows_the_run_flow(lineage, monkeypatch):  # noqa: F811
    from unittest.mock import Mock
    from tests.test_doctor_feedback import surgery
    from tests.test_fsm_resume import write_mock_tool_receipts
    o, parent, origin, source, tb, metric = lineage
    o.cfg.implementation = "out_of_context"
    monkeypatch.setattr(o.doctor, "surgery", Mock(return_value=source))
    write_mock_tool_receipts(origin, ("vivado",))
    ooc = vivado.synthesis_tcl([origin / "m.v"], "m", o.cfg, origin, promotions=o.taxonomy.promotions())
    (origin / "synth.tcl").write_text(ooc, encoding="utf-8")
    assert o._doctor_default_flow(origin, source, [], tb)  # an unchanged OOC flow is proven
    chip = RunConfig.from_dict({**o.cfg.to_dict(), "implementation": "chip_top"})
    (origin / "synth.tcl").write_text(
        vivado.synthesis_tcl([origin / "m.v"], "m", chip, origin, promotions=o.taxonomy.promotions()),
        encoding="utf-8")
    assert not o._doctor_default_flow(origin, source, [], tb)  # a chip-top script proves nothing here


def test_axil_regs_entry_is_an_out_of_context_block():
    entry = Path(__file__).resolve().parents[1] / "curriculum" / "tier5" / "axil_regs_build"
    assert runner._metadata(entry)["implementation"] == "out_of_context"
