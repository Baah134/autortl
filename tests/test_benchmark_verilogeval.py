"""VerilogEval adapter, pilot selection and grader with fixtures and process doubles.

No model, Vivado, Icarus or network. Real simulator controls run separately
after the user-approved Icarus install (docs/BENCHMARK_PILOT.md).
"""
import shutil
import subprocess
from pathlib import Path

import pytest

from benchmark import artifacts
from benchmark import verilogeval as ve

FIX = Path(__file__).parent / "fixtures" / "verilogeval"
DATA = FIX / "dataset"
COMMIT = "a" * 40


def log(name):
    return (FIX / name).read_text(encoding="utf-8")


# ---------------------------------------------------------------- parser
@pytest.mark.parametrize("name, exit_code, timed_out, status, mismatches, samples", [
    ("sim_pass.log", 0, False, "pass", 0, 439),
    ("sim_fail.log", 0, False, "fail", 336, 439),
    ("sim_no_summary.log", 0, False, "no_result", None, None),
    ("sim_zero_samples.log", 0, False, "fail", 0, 0),
    ("sim_pass.log", 1, False, "runtime_error", 0, 439),
    ("sim_pass.log", None, True, "timeout", 0, 439),
])
def test_parse_sim_output_fixtures(name, exit_code, timed_out, status, mismatches, samples):
    verdict = ve.parse_sim_output(log(name), exit_code, timed_out)
    assert (verdict["status"], verdict["mismatches"], verdict["samples"]) == (status, mismatches, samples)


# Real Icarus 12 logs (pinned c498220, Prob035) and upstream analyze_result rules.
@pytest.mark.parametrize("text, verilog, code", [
    (lambda: log("sim_pass.log"), "", "."),
    (lambda: log("sim_fail.log"), "", "R"),
    (lambda: log("sim_fail.log"), "always @(posedge reset)", "r"),
    (lambda: log("sim_fail.log"), "always @(posedge clk, posedge r)", "r"),
    (lambda: log("compile_syntax.log"), "", "S"),
    (lambda: log("sim_pass.log") + "\nTIMEOUT\n", "", "T"),
    (lambda: "x.sv:3: error: This assignment requires an explicit cast\n", "", "e"),
    (lambda: "x.sv:3: error: Sized numeric constant must have a size greater than zero\n", "", "0"),
    (lambda: "x.sv:9: warning: always_comb process has no sensitivities\n" + log("sim_pass.log"), "", "n"),
    (lambda: "found no sensitivities so it will never trigger\n" + log("sim_pass.log"), "", "n"),
    (lambda: "x.sv:2: : q is declared here as wire.\n", "", "w"),
    (lambda: "x.sv:2: error: Unknown module type: Foo\n", "", "m"),
    (lambda: "Unable to bind wire/reg/memory `clk' in `tb'\n", "", "c"),
    (lambda: "Unable to bind wire/reg/memory `x' in `tb'\n" + log("sim_pass.log"), "", "p"),
    (lambda: "x.sv:4: error: something else\n" + log("sim_pass.log"), "", "C"),
])
def test_upstream_passfail_port(text, verilog, code):
    assert ve.upstream_passfail(text(), verilog) == code


def test_upstream_pass_requires_zero_summary_but_not_sample_count():
    # Upstream accepts "0 in 0"; the strict status does not. Both are recorded.
    assert ve.upstream_passfail(log("sim_zero_samples.log"), "") == "."
    assert ve.parse_sim_output(log("sim_zero_samples.log"), 0)["status"] == "fail"


def test_last_summary_wins_and_count_is_recorded():
    text = "Mismatches: 0 in 20 samples\nMismatches: 3 in 20 samples\n"
    verdict = ve.parse_sim_output(text, 0)
    assert verdict["status"] == "fail" and verdict["summaries_seen"] == 2


def test_summary_text_inside_a_line_is_not_a_summary():
    assert ve.parse_sim_output("note: Mismatches: 0 in 20 samples expected\n", 0)["status"] == "no_result"


# ------------------------------------------------------------- dataset
def test_list_and_load_tasks():
    assert ve.list_tasks(DATA) == ["Prob900_inv", "Prob901_and2", "Prob902_orphan"]
    task = ve.load_task(DATA, "Prob900_inv")
    assert task.test.name == "Prob900_inv_test.sv" and task.ref.name == "Prob900_inv_ref.sv"


def test_missing_task_files_fail_closed():
    with pytest.raises(ve.AdapterError, match="missing test"):
        ve.load_task(DATA, "Prob902_orphan")
    with pytest.raises(ve.AdapterError, match="invalid task id"):
        ve.load_task(DATA, "../Prob900_inv")


def test_manifest_marks_prompt_public_and_tests_private(tmp_path):
    budgets = {"single_call": {"model_calls": 1, "tool_seconds": 1.0, "wall_seconds": 2100},
               "full": {"model_calls": 16, "tool_seconds": 1500.0, "wall_seconds": 2100}}
    manifest = ve.build_manifest(DATA, ["Prob900_inv", "Prob901_and2"], dataset_commit=COMMIT,
                                 source_commit="b" * 40, runtime_commit="c" * 40,
                                 runtime_sha256="d" * 64, requested_model="unpinned-default",
                                 budgets=budgets)
    task = manifest["tasks"][0]
    assert [f["path"] for f in task["public_files"]] == ["Prob900_inv_prompt.txt"]
    assert [f["path"] for f in task["private_files"]] == ["Prob900_inv_test.sv", "Prob900_inv_ref.sv"]
    assert manifest["identity"]["dataset"]["format"] == "verilogeval"
    assert {(c["task"], c["arm"]) for c in manifest["cells"]} == {
        (t, a) for t in ("Prob900_inv", "Prob901_and2") for a in ("single_call", "full")}
    path = tmp_path / "frozen.json"
    import json
    path.write_text(json.dumps(manifest), encoding="utf-8")
    assert artifacts.load_manifest(path, public_root=DATA, private_root=DATA) == manifest
    exported = artifacts.export_public(manifest, public_root=DATA, destination=tmp_path / "public")
    copied = {p.name for p in (tmp_path / "public").rglob("*") if p.is_file()}
    assert copied == {"receipt.json", "Prob900_inv_prompt.txt", "Prob901_and2_prompt.txt"}
    assert exported["kind"] == "public"


def test_manifest_rejects_short_commit_and_bad_single_call_budget():
    good = {"single_call": {"model_calls": 1, "tool_seconds": 1.0, "wall_seconds": 10}}
    kwargs = dict(source_commit="b" * 40, runtime_commit="c" * 40, runtime_sha256="d" * 64,
                  requested_model="m")
    with pytest.raises(ve.AdapterError, match="40-character"):
        ve.build_manifest(DATA, ["Prob900_inv"], dataset_commit="abc", budgets=good, **kwargs)
    bad = {"single_call": {"model_calls": 2, "tool_seconds": 1.0, "wall_seconds": 10}}
    with pytest.raises(artifacts.ArtifactError):
        ve.build_manifest(DATA, ["Prob900_inv"], dataset_commit=COMMIT, budgets=bad, **kwargs)


# ------------------------------------------------------------ selection
def catalog():
    entries = {}
    for category, prefix in zip(ve.CATEGORIES, "LAQF"):
        for family in range(3):
            for member in range(2):
                entries[f"{prefix}{family}_{member}"] = {"category": category, "family": f"{prefix}fam{family}"}
    return entries


def test_pilot_selection_is_deterministic_and_covers_categories():
    first = ve.select_pilot(catalog(), COMMIT)
    assert first == ve.select_pilot(dict(reversed(list(catalog().items()))), COMMIT)
    pilot = first["pilot"]
    assert len(pilot) == 6 and len({p["family"] for p in pilot}) == 6
    assert {p["category"] for p in pilot} == set(ve.CATEGORIES)
    assert first["slots"] == ve.PILOT_SLOTS
    assert [p["category"] for p in pilot] == [c for c in ve.CATEGORIES for _ in range(ve.PILOT_SLOTS[c])]
    assert first["excluded_families"] == sorted(p["family"] for p in pilot)
    for p in pilot:  # best-ranked family of its category not chosen earlier
        members = [t for t, e in catalog().items() if e["family"] == p["family"]]
        assert p["task"] == min(members, key=lambda t: (ve.rank(COMMIT, t), t))


def test_custom_slots_and_best_ranked_families():
    slots = {"combinational_logic": 3, "combinational_arithmetic": 1, "sequential": 1, "fsm_control": 1}
    picked = ve.select_pilot(catalog(), COMMIT, slots=slots)["pilot"]
    logic = [p["family"] for p in picked if p["category"] == "combinational_logic"]
    every = sorted({e["family"] for e in catalog().values() if e["category"] == "combinational_logic"},
                   key=lambda f: (ve.rank(COMMIT, f), f))
    assert logic == every[:3]


def test_pilot_selection_changes_with_commit():
    picks = {tuple(p["task"] for p in ve.select_pilot(catalog(), c * 40)["pilot"]) for c in "abcdef"}
    assert len(picks) > 1


def test_pilot_selection_rejects_bad_catalogs():
    entries = catalog()
    missing = {t: e for t, e in entries.items() if e["category"] != "fsm_control"}
    with pytest.raises(ve.AdapterError, match="fsm_control"):
        ve.select_pilot(missing, COMMIT)
    split = dict(entries, L0_1={"category": "sequential", "family": "Lfam0"})
    with pytest.raises(ve.AdapterError, match="spans categories"):
        ve.select_pilot(split, COMMIT)
    with pytest.raises(ve.AdapterError, match="unknown category"):
        ve.select_pilot({"x": {"category": "misc", "family": "f"}}, COMMIT)
    with pytest.raises(ve.AdapterError, match="too few families"):
        ve.select_pilot(entries, COMMIT, slots=dict(ve.PILOT_SLOTS, sequential=4))
    with pytest.raises(ve.AdapterError, match="positive integer"):
        ve.select_pilot(entries, COMMIT, slots=dict(ve.PILOT_SLOTS, sequential=0))


# --------------------------------------------------------------- grader
class FakeTools:
    """Process double: records commands, writes the image, prints a sim log."""

    def __init__(self, compile_exit=0, sim_text="", sim_exit=0, sim_timeout=False, missing=None):
        self.calls, self.compile_exit, self.sim_text = [], compile_exit, sim_text
        self.sim_exit, self.sim_timeout, self.missing = sim_exit, sim_timeout, missing

    def __call__(self, cmd, cwd, capture_output, text, errors, timeout):
        self.calls.append((cmd, timeout))
        if self.missing == cmd[0]:
            raise FileNotFoundError(cmd[0])
        if "-o" in cmd:
            if self.compile_exit == 0:
                Path(cmd[cmd.index("-o") + 1]).write_bytes(b"image")
            return subprocess.CompletedProcess(cmd, self.compile_exit, "", "syntax error\n" if self.compile_exit else "")
        if self.sim_timeout:
            raise subprocess.TimeoutExpired(cmd, timeout, output=b"partial\n")
        return subprocess.CompletedProcess(cmd, self.sim_exit, self.sim_text, "")


def candidate(tmp_path):
    path = tmp_path / "TopModule.sv"
    path.write_text("module TopModule(input a, output y); assign y = ~a; endmodule\n", encoding="utf-8")
    return path


def test_grade_pass_records_commands_hashes_and_logs(tmp_path):
    tools = FakeTools(sim_text=log("sim_pass.log"))
    task = ve.load_task(DATA, "Prob900_inv")
    verdict = ve.grade([candidate(tmp_path)], task, tmp_path / "g", runner=tools)
    assert verdict["status"] == "pass" and verdict["samples"] == 439
    assert verdict["upstream_code"] == "." and verdict["upstream_pass"] and verdict["agree"]
    compile_cmd, sim_cmd = tools.calls[0][0], tools.calls[1][0]
    assert compile_cmd[:5] == ["iverilog", *ve.COMPILE_FLAGS] and compile_cmd[5:7] == ["-s", "tb"]
    assert compile_cmd[-2:] == [str(task.test), str(task.ref)]
    assert sim_cmd[:2] == ["vvp", "-n"] and tools.calls[1][1] == ve.SIM_TIMEOUT_S
    assert verdict["inputs"]["test"]["sha256"] == ve.sha256_file(task.test)
    assert (tmp_path / "g" / "sim.log").read_text(encoding="utf-8") == log("sim_pass.log")


def test_grade_compile_error_skips_simulation(tmp_path):
    tools = FakeTools(compile_exit=2)
    verdict = ve.grade([candidate(tmp_path)], ve.load_task(DATA, "Prob900_inv"), tmp_path / "g", runner=tools)
    assert verdict["status"] == "compile_error" and verdict["simulate"] is None and len(tools.calls) == 1
    assert "syntax error" in (tmp_path / "g" / "compile.log").read_text(encoding="utf-8")


def test_grade_timeout_and_runtime_error(tmp_path):
    task = ve.load_task(DATA, "Prob900_inv")
    hung = ve.grade([candidate(tmp_path)], task, tmp_path / "g1", runner=FakeTools(sim_timeout=True))
    assert hung["status"] == "timeout" and hung["simulate"]["timed_out"] and hung["upstream_code"] == "T"
    crashed = ve.grade([candidate(tmp_path)], task, tmp_path / "g2",
                       runner=FakeTools(sim_text=log("sim_pass.log"), sim_exit=3))
    # Upstream cannot see the exit code; the disagreement is recorded, not resolved.
    assert crashed["status"] == "runtime_error" and crashed["upstream_pass"] and not crashed["agree"]


def test_missing_simulator_is_infrastructure_not_a_verdict(tmp_path):
    with pytest.raises(ve.GraderUnavailable):
        ve.grade([candidate(tmp_path)], ve.load_task(DATA, "Prob900_inv"), tmp_path / "g",
                 runner=FakeTools(missing="iverilog"))


def test_grade_refuses_reused_workdir(tmp_path):
    (tmp_path / "g").mkdir()
    with pytest.raises(FileExistsError):
        ve.grade([candidate(tmp_path)], ve.load_task(DATA, "Prob900_inv"), tmp_path / "g", runner=FakeTools())


@pytest.mark.skipif(not (shutil.which("iverilog") and shutil.which("vvp")), reason="Icarus not installed")
def test_real_icarus_reference_control(tmp_path):
    task = ve.load_task(DATA, "Prob900_inv")
    good = ve.grade([candidate(tmp_path)], task, tmp_path / "good")
    assert good["status"] == "pass"
    broken = tmp_path / "broken.sv"
    broken.write_text("module TopModule(input a, output y); assign y = a; endmodule\n", encoding="utf-8")
    assert ve.grade([broken], task, tmp_path / "bad")["status"] == "fail"
