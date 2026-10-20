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


def test_all_selected_skills_exist_and_fit_default_budget():
    spec = ModuleSpec(name="fifo_mac", behavior="memory multiply buffer",
                      ports=[Port("wr_clk", "input", 1)],
                      clock_domains=["wr_clk", "rd_clk"])
    names = list(dict.fromkeys(["autortl-conventions", "fpga-methodology"] +
                               select_for_module(spec) + select_for_timing()))
    for name in names:
        assert load_skill(name).strip(), name
    expertise = [name for name in names if name != "autortl-conventions"]
    combined = inject(expertise)
    assert len(combined) <= 12000
    for name in expertise:
        assert f"Reference: {name}" in combined


def test_injected_guidance_preserves_fixed_contract():
    names = ["autortl-conventions", "verilog-idioms", "cdc", "xilinx-inference",
             "timing-closure", "vivado-messages", "fpga-methodology"]
    for name in names:
        body = " ".join(load_skill(name).lower().split())
        for required in ("contract", "latency", "reset", "parameter", "registered outputs"):
            assert required in body, (name, required)
        for obsolete in ("update `// @latency`", "zero code risk", "-0.5 ns",
                         "reset every state-holding register", "tie unused inputs low"):
            assert obsolete not in body, (name, obsolete)
    assert "hold" in load_skill("timing-closure").lower()
    assert "high bits" in conventions().lower()


def test_dormant_tool_and_testbench_guidance_does_not_weaken_checks():
    assert "2-cycle settle margin" not in load_skill("testbench-craft")
    assert "latency becomes irrelevant" not in load_skill("testbench-craft").lower()
    assert "file delete -force" not in load_skill("vivado-driving")
    assert "compile failures are not mutant detections" in load_skill("testbench-craft").lower()


def test_fifo_reference_and_behavioral_mutants(tmp_path):
    import hashlib
    import json
    from pathlib import Path
    from tests.fifo_live_cases import save

    root = Path(__file__).resolve().parents[1]
    source = root / ".claude/skills/cdc/snippets/async_fifo_skeleton.v"
    rtl = source.read_text()
    assert "assign full = (wptr_gray ==" in rtl
    assert "assign full = (wptr_gray_n ==" not in rtl
    assert "AW >= 2, DW >= 1" in rtl
    assert "Coordinated reset" in rtl
    manifest = save(tmp_path)
    assert len(manifest) == 6
    assert sum(case["expected_pass"] for case in manifest) == 2
    assert json.loads((tmp_path / "manifest.json").read_text()) == manifest
    for case in manifest:
        folder = tmp_path / case["case"]
        assert hashlib.sha256((folder / "async_fifo.v").read_bytes()).hexdigest() == case["source_sha256"]
        assert hashlib.sha256((folder / "async_fifo_tb.v").read_bytes()).hexdigest() == case["tb_sha256"]
        aw = case["case"][2]
        assert f"localparam AW = {aw};" in (folder / "async_fifo_tb.v").read_text()
        assert "dut." not in (folder / "async_fifo_tb.v").read_text()


def test_fifo_legacy_loop_is_not_qualified_as_behavioral_mutant(tmp_path):
    import pytest
    from pathlib import Path
    from tests.fifo_live_cases import save

    root = Path(__file__).resolve().parents[1]
    rtl = (root / ".claude/skills/cdc/snippets/async_fifo_skeleton.v").read_text()
    source = tmp_path / "legacy.v"
    source.write_text(rtl.replace("assign full = (wptr_gray ==", "assign full = (wptr_gray_n =="))
    with pytest.raises(ValueError, match="combinational"):
        save(tmp_path / "cases", source)


def test_skill_loader_uses_explicit_utf8(monkeypatch, tmp_path):
    from pathlib import Path
    from autortl import skill_loader
    root=tmp_path / "skills"
    path=root / "encoding" / "SKILL.md"
    path.parent.mkdir(parents=True)
    body="Unicode guidance: \u201cprecise\u201d \u2014 \u03bb\n"
    path.write_text("---\nname: encoding\n---\n"+body, encoding="utf-8")
    original=Path.read_text
    def require_encoding(self, *args, **kwargs):
        if self == path:
            assert kwargs.get("encoding") == "utf-8"
        return original(self,*args,**kwargs)
    monkeypatch.setattr(skill_loader,"SKILLS_DIR",root)
    monkeypatch.setattr(Path,"read_text",require_encoding)
    assert skill_loader.load_skill("encoding") == body
