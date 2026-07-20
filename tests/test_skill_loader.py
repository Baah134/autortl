from autortl.skill_loader import (load_skill, conventions, select_for_module,
                                  select_for_timing, inject)
from autortl.spec import ModuleSpec, Port


def test_conventions_nonempty_and_lawful():
    c = conventions()
    assert "@latency" in c and "law" in c.lower()


def test_protocol_first_selection_cdc():
    m = ModuleSpec(name="x", behavior="moves data between clocks",
                   ports=[Port("clk", "input", 1)],
                   clock_domains=["wr_clk", "rd_clk"])
    assert "cdc" in select_for_module(m)


def test_behavior_selects_inference():
    m = ModuleSpec(name="x", behavior="multiply accumulate filter",
                   ports=[Port("clk", "input", 1)])
    assert "xilinx-inference" in select_for_module(m)


def test_timing_selection():
    s = select_for_timing()
    assert "timing-closure" in s and "vivado-messages" in s


def test_inject_respects_limit():
    out = inject(["verilog-idioms", "cdc", "timing-closure"], limit_chars=50)
    assert len(out) <= 60      # header overhead tolerance on an empty-ish fit
