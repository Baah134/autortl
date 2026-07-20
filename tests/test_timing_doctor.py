from pathlib import Path
from autortl.timing_doctor import diagnose, parse_worst_path, TimingCategory


def write_rpt(tmp_path, wns, levels=4, fanout=8):
    (tmp_path / "timing_routed.rpt").write_text(f"""
Design Timing Summary
| WNS(ns)  TNS(ns)  TNS Failing Endpoints  TNS Total Endpoints
    {wns}    -1.0                      3                   77
Slack (VIOLATED) :        {wns}ns
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
