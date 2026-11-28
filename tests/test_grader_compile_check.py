"""grader_rejects_vendor_attribute: optional pre-seal compile with the grader's Icarus flags.

Icarus is faked (vivado._run or icarus_check doubles); the fixture log is real
Icarus 12.0 output for the final-02 Prob027_fadd attribute. One test runs the
real compiler when AUTORTL_IVERILOG or PATH provides it, and skips otherwise.
"""
import os
import shutil
from pathlib import Path
from unittest.mock import Mock

import pytest

from autortl import fsm, vivado
from autortl.config import RunConfig
from autortl.triage import FailureKind
from benchmark import campaign, pilot
from benchmark import verilogeval as ve
from tests.test_fsm_build import create

FIXTURE = Path(__file__).parent / "fixtures" / "icarus" / "lutnm_invalid_module_item.log"
ATTRIBUTED = ("// @latency 1\nmodule counter8_core(input clk,input rst,input enable,output reg [7:0] count);"
              " wire step; (* LUTNM = \"inc\" *) assign step = enable;"
              " always @(posedge clk) if(rst) count<=0; else if(step) count<=count+1'b1; endmodule")
CLEAN = ("// @latency 1\nmodule counter8_core(input clk,input rst,input enable,output reg [7:0] count);"
         " always @(posedge clk) if(rst) count<=0; else if(enable) count<=count+1'b1; endmodule")


# ------------------------------------------------------------ compile check
def test_flags_match_the_official_grader():
    assert vivado.GRADER_COMPILE_FLAGS == ve.COMPILE_FLAGS


def fake_run(rc, output, seen=None):
    def run(cmd, cwd, timeout, log_path):
        if seen is not None:
            seen.append((cmd, cwd, timeout))
        Path(log_path).write_text(output, encoding="utf-8")
        return rc, output
    return run


def test_accepts_rtl_the_grader_compiles(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(vivado, "_run", fake_run(0, "", seen))
    source = tmp_path / "TopModule.v"
    assert vivado.icarus_check([source], "C:/tools/iverilog.exe", tmp_path, timeout=30) == (
        True, "", FailureKind.DESIGN)
    cmd, cwd, timeout = seen[0]
    # Design RTL only: no -s testbench top, no official test or reference file.
    assert cmd == ["C:/tools/iverilog.exe", *ve.COMPILE_FLAGS, "-o", str(tmp_path / "icarus_check.vvp"),
                   str(source)]
    assert cwd == tmp_path and timeout == 30


def test_rejection_is_a_design_error_with_the_compiler_message(tmp_path, monkeypatch):
    log = FIXTURE.read_text(encoding="utf-8")
    monkeypatch.setattr(vivado, "_run", fake_run(2, log))
    ok, error, kind = vivado.icarus_check([tmp_path / "TopModule.v"], "iverilog", tmp_path)
    assert not ok and kind == FailureKind.DESIGN
    assert error.startswith(vivado.GRADER_REJECTION)
    assert "TopModule.v:9: error: Invalid module item." in error
    assert "LUTNM" not in vivado.GRADER_REJECTION  # general wording, not this task's attribute


@pytest.mark.parametrize("rc,output", [
    (127, "iverilog not found: [WinError 2] The system cannot find the file specified"),
    (124, "partial\ntimed out after 60s"),
])
def test_launch_failure_or_timeout_is_infrastructure(tmp_path, monkeypatch, rc, output):
    monkeypatch.setattr(vivado, "_run", fake_run(rc, output))
    ok, error, kind = vivado.icarus_check([tmp_path / "TopModule.v"], "iverilog", tmp_path, timeout=60)
    assert not ok and kind == FailureKind.INFRA and "could not complete" in error


def real_iverilog():
    name = os.environ.get("AUTORTL_IVERILOG") or "iverilog"
    return shutil.which(name)


@pytest.mark.skipif(real_iverilog() is None, reason="Icarus Verilog not installed")
def test_real_icarus_rejects_the_attribute_vivado_accepted(tmp_path):
    source = tmp_path / "TopModule.v"
    source.write_text("module TopModule(input a, input b, input cin, output cout, output sum);\n"
                      "  (* LUTNM = \"full_adder\" *)\n  assign {cout, sum} = a + b + cin;\nendmodule\n",
                      encoding="utf-8")
    ok, error, kind = vivado.icarus_check([source], real_iverilog(), tmp_path)
    assert not ok and kind == FailureKind.DESIGN and "Invalid module item" in error
    source.write_text("module TopModule(input a, input b, input cin, output cout, output sum);\n"
                      "  assign {cout, sum} = a + b + cin;\nendmodule\n", encoding="utf-8")
    assert vivado.icarus_check([source], real_iverilog(), tmp_path)[0]


# ---------------------------------------------------------------- harness
def test_config_defaults_off_and_old_saved_configs_load(tmp_path):
    cfg = RunConfig(mode="build", spec_path=tmp_path / "s.json", work_dir=tmp_path)
    assert cfg.grader_iverilog is None
    data = cfg.to_dict()
    del data["grader_iverilog"]  # a run saved before the option existed
    assert RunConfig.from_dict(data).grader_iverilog is None
    cfg.grader_iverilog = "  "
    with pytest.raises(ValueError, match="grader_iverilog"):
        cfg.validate()


def icarus_double(reject):
    def check(files, iverilog, work, timeout=60):
        text = "\n".join(Path(f).read_text(encoding="utf-8") for f in files)
        if reject(text):
            return False, vivado.GRADER_REJECTION + FIXTURE.read_text(encoding="utf-8"), FailureKind.DESIGN
        return True, "", FailureKind.DESIGN
    return Mock(side_effect=check)


def test_off_by_default_runs_no_extra_compiler(tmp_path, monkeypatch):
    o, _ = create(tmp_path, monkeypatch)
    check = Mock(side_effect=AssertionError("grader compile check must be opt-in"))
    monkeypatch.setattr(fsm.vivado, "icarus_check", check)
    assert o.run()["status"] == "done"
    check.assert_not_called()


def test_rejection_reaches_the_bounded_repair_loop(tmp_path, monkeypatch):
    o, _ = create(tmp_path, monkeypatch)
    o.cfg.grader_iverilog = "C:/tools/iverilog.exe"
    check = icarus_double(lambda text: "(*" in text)
    monkeypatch.setattr(fsm.vivado, "icarus_check", check)
    monkeypatch.setattr(o.generator, "generate", Mock(return_value=ATTRIBUTED))
    fix = Mock(return_value=CLEAN)
    monkeypatch.setattr(o.generator, "fix", fix)
    result = o.run()
    assert result["status"] == "done"
    assert fix.call_count == 1
    assert "Invalid module item" in str(fix.call_args)
    assert "(*" not in (o.state.run_dir / "counter8_best.v").read_text(encoding="utf-8")
    assert all(call.args[1] == "C:/tools/iverilog.exe" for call in check.call_args_list)


def test_persistent_rejection_stops_after_max_fix_attempts(tmp_path, monkeypatch):
    o, synthesis = create(tmp_path, monkeypatch)  # max_fix_attempts=1
    o.cfg.grader_iverilog = "iverilog"
    monkeypatch.setattr(fsm.vivado, "icarus_check", icarus_double(lambda text: "(*" in text))
    monkeypatch.setattr(o.generator, "generate", Mock(return_value=ATTRIBUTED))
    fix = Mock(return_value=ATTRIBUTED)
    monkeypatch.setattr(o.generator, "fix", fix)
    result = o.run()
    assert result["status"] == "module_failed" and "Invalid module item" in result["error"]
    assert fix.call_count == o.cfg.max_fix_attempts
    synthesis.assert_not_called()


def test_compiler_infrastructure_failure_never_costs_a_repair(tmp_path, monkeypatch):
    o, synthesis = create(tmp_path, monkeypatch)
    o.cfg.grader_iverilog = "iverilog"
    monkeypatch.setattr(fsm.vivado, "icarus_check", Mock(
        return_value=(False, "icarus check could not complete (exit 127): not found", FailureKind.INFRA)))
    fix = Mock(side_effect=AssertionError("infrastructure is not a fix attempt"))
    monkeypatch.setattr(o.generator, "fix", fix)
    result = o.run()
    assert result["status"] != "done"
    fix.assert_not_called()
    synthesis.assert_not_called()


# -------------------------------------------------------------- benchmark
def test_full_command_passes_the_compiler_only_when_enabled(tmp_path):
    budget = pilot.PROVISIONAL_BUDGETS["full"]
    plain = pilot.full_command(tmp_path / "p.txt", tmp_path / "run", budget, python="py")
    assert "--grader-iverilog" not in plain
    checked = pilot.full_command(tmp_path / "p.txt", tmp_path / "run", budget, python="py",
                                 grader_iverilog="C:/tools/iverilog.exe")
    assert checked[-2:] == ["--grader-iverilog", "C:/tools/iverilog.exe"]


def test_run_py_accepts_the_option_and_defaults_off():
    import run
    seen = {}

    class Stop(Exception):
        pass

    def orchestrator(cfg, run_dir=None):
        seen["cfg"] = cfg
        raise Stop
    original = run.Orchestrator
    run.Orchestrator = orchestrator
    try:
        for extra, expected in (([], None), (["--grader-iverilog", "C:/tools/iverilog.exe"],
                                             "C:/tools/iverilog.exe")):
            with pytest.raises(Stop):
                run.main(["build", "--spec", "spec.md", *extra])
            assert seen["cfg"].grader_iverilog == expected
    finally:
        run.Orchestrator = original


def test_grader_compiler_resolves_or_stops_as_infrastructure(monkeypatch, tmp_path):
    monkeypatch.delenv("AUTORTL_IVERILOG", raising=False)
    monkeypatch.setattr(pilot.shutil, "which", lambda name: None)
    with pytest.raises(ve.GraderUnavailable):
        pilot.grader_compiler()
    exe = tmp_path / "iverilog.exe"
    monkeypatch.setattr(pilot.shutil, "which", lambda name: str(exe) if name == "iverilog" else None)
    assert pilot.grader_compiler() == str(exe.resolve())


def test_run_cell_enables_the_check_for_harness_arms_only(monkeypatch):
    calls = []
    monkeypatch.setattr(pilot, "run_full", lambda *a, **k: calls.append(("full", k)) or {})
    monkeypatch.setattr(pilot, "run_single_call", lambda *a, **k: calls.append(("single", k)) or {})
    campaign.run_cell({}, None, ("T", "full", 0), Path("x"))
    campaign.run_cell({}, None, ("T", "full", 0), Path("x"), grader_check=True, iverilog="/i")
    campaign.run_cell({}, None, ("T", "single_call", 0), Path("x"), grader_check=True, iverilog="/i")
    assert "grader_check" not in calls[0][1]
    assert calls[1][1]["grader_check"] is True and calls[1][1]["iverilog"] == "/i"
    assert calls[2] == ("single", {"trial": 0, "model": None})


def test_campaign_resolves_the_compiler_before_any_cell(monkeypatch, tmp_path):
    monkeypatch.setattr(campaign.artifacts, "load_manifest", lambda *a, **k: {})
    monkeypatch.setattr(pilot, "grader_compiler", Mock(side_effect=ve.GraderUnavailable("missing")))
    started = Mock()
    monkeypatch.setattr(campaign, "run_campaign", started)
    with pytest.raises(ve.GraderUnavailable):
        campaign.main(["--manifest", "m.json", "--dataset", str(tmp_path), "--attempt", str(tmp_path / "a"),
                       "--no-probe", "--grader-check"])
    started.assert_not_called()


def test_run_full_records_the_check_in_the_cell_command(monkeypatch, tmp_path):
    from tests.test_benchmark_pilot import DATA, FakeBuild
    manifest = ve.build_manifest(DATA, ["Prob900_inv"], dataset_commit="a" * 40, source_commit="b" * 40,
                                 runtime_commit="c" * 40, runtime_sha256="d" * 64,
                                 requested_model="unobserved-cli-default", budgets=pilot.PROVISIONAL_BUDGETS)
    task = ve.load_task(DATA, "Prob900_inv")
    monkeypatch.setattr(pilot, "grader_compiler", lambda iverilog=None: "C:/tools/iverilog.exe")
    build = FakeBuild()
    record = pilot.run_full(manifest, task, tmp_path / "c", runner=build, tools={}, grader_check=True)
    assert build.cmd[-2:] == ["--grader-iverilog", "C:/tools/iverilog.exe"]
    assert record["accounting"]["command"] == build.cmd and record["kind"] == "candidate"
    plain = FakeBuild()
    pilot.run_full(manifest, task, tmp_path / "d", runner=plain, tools={})
    assert "--grader-iverilog" not in plain.cmd
