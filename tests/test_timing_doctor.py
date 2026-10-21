from pathlib import Path
import shutil
from autortl.timing_doctor import diagnose, parse_worst_path, TimingCategory


def write_rpt(tmp_path, wns, levels=4, fanout=8):
    (tmp_path / "timing_routed.rpt").write_text(f"""
Design Timing Summary
| WNS(ns)  TNS(ns)  TNS Failing Endpoints  TNS Total Endpoints
    {wns}    -1.0                      3                   77
WHS(ns)  THS(ns)  THS Failing Endpoints  THS Total Endpoints
    0.100    0.0                      0                   77
Slack ({'VIOLATED' if wns < 0 else 'MET'}) :        {wns}ns
  Source:                 data_source_reg/C
  Destination:            data_destination_reg/D
  Path Type:              Max at Slow Process Corner
  Logic Levels:           {levels}
  net (fo=1) fanout={fanout}
""")


def test_timing_met_no_action(tmp_path):
    write_rpt(tmp_path, 1.5)
    d = diagnose(tmp_path, False)
    assert d.action == "none"


def test_small_deficit_gets_knobs(tmp_path):
    write_rpt(tmp_path, -0.3)
    d = diagnose(tmp_path, already_tried_knobs=False)
    assert d.action == "tool_knobs"


def test_small_deficit_after_knobs_gets_surgery(tmp_path):
    write_rpt(tmp_path, -0.3)
    d = diagnose(tmp_path, already_tried_knobs=True)
    assert d.action == "rtl_surgery"


def test_deep_logic_categorised_pipeline(tmp_path):
    write_rpt(tmp_path, -1.2, levels=11)
    d = diagnose(tmp_path, False)
    assert d.category == TimingCategory.LOGIC_DEPTH
    assert "pipeline" in d.instruction.lower()


def test_high_fanout_categorised(tmp_path):
    write_rpt(tmp_path, -1.2, levels=3, fanout=120)
    d = diagnose(tmp_path, False)
    assert d.category == TimingCategory.HIGH_FANOUT
    assert "replicate" in d.instruction.lower()


def test_hold_only_violation_uses_physical_knobs_then_replan(tmp_path):
    fixture = Path(__file__).parent / "fixtures" / "timing_hold_violation.rpt"
    shutil.copyfile(fixture, tmp_path / "timing_routed.rpt")
    first = diagnose(tmp_path, False)
    assert first.category == TimingCategory.HOLD
    assert first.wns_ns == 1.250
    assert "-0.125" in first.detail
    assert first.action == "tool_knobs"
    retry = diagnose(tmp_path, True)
    assert retry.category == TimingCategory.HOLD
    assert retry.action == "replan"
    assert "real clock and I/O constraints" in retry.instruction
    assert "Do not relax the clock" in retry.instruction
    assert "add RTL delay chains" in retry.instruction


def test_canonical_parser_preserves_path_metadata():
    fixture = Path(__file__).parent / "fixtures" / "timing_hold_violation.rpt"
    wns, levels, fanout, snippet = parse_worst_path(fixture)
    assert (wns, levels, fanout) == (1.250, 2, 72)
    assert "Slack (VIOLATED)" in snippet
    assert "hold_endpoint" in snippet


def test_missing_hold_is_not_timing_met(tmp_path):
    (tmp_path / "timing_routed.rpt").write_text("WNS(ns)  TNS(ns)\n 1.5  0.0\n")
    result = diagnose(tmp_path, False)
    assert result.action == "replan"
    assert "missing or invalid" in result.detail


def test_missing_report_requires_evidence_before_rtl_changes(tmp_path):
    assert parse_worst_path(tmp_path / "absent.rpt") == (-999.0, 0, 0, "")
    result = diagnose(tmp_path, False)
    assert result.action == "replan"
    assert "Do not change RTL" in result.instruction


def test_setup_surgery_preserves_latency_for_all_path_shapes(tmp_path):
    for levels, fanout in ((12, 3), (3, 120), (3, 2)):
        write_rpt(tmp_path, -1.2, levels, fanout)
        result = diagnose(tmp_path, False)
        assert result.action == "rtl_surgery"
        assert "Preserve observable latency, throughput, interface, reset semantics, and parameter behavior" in result.instruction
        assert "Do not add pipeline stages" in result.instruction
        assert "across two cycles" not in result.instruction


def test_hold_violation_takes_priority_over_setup_surgery(tmp_path):
    fixture = Path(__file__).parent / "fixtures" / "timing_hold_violation.rpt"
    (tmp_path / "timing_routed.rpt").write_text(fixture.read_text().replace("1.250", "-1.250"))
    result = diagnose(tmp_path, False)
    assert result.category == TimingCategory.HOLD
    assert result.action == "tool_knobs"
