"""Pilot arm runners with model and process doubles; no model, Vivado or Icarus."""
import json
import subprocess
from pathlib import Path

import pytest

from benchmark import artifacts
from benchmark import pilot
from benchmark import verilogeval as ve
from llm import client

DATA = Path(__file__).parent / "fixtures" / "verilogeval" / "dataset"
GOOD = "Here it is:\n```verilog\nmodule TopModule(input a, output y);\n  assign y = ~a;\nendmodule\n```\n"


@pytest.fixture(autouse=True)
def fake_tools(monkeypatch):
    tools = {name: f"C:/Vivado/bin/{name}.bat" for name in ("vivado", "xvlog", "xelab", "xsim")}
    monkeypatch.setattr(pilot, "vivado_tools", lambda: tools)
    return tools


@pytest.fixture
def manifest():
    return ve.build_manifest(DATA, ["Prob900_inv"], dataset_commit="a" * 40, source_commit="b" * 40,
                             runtime_commit="c" * 40, runtime_sha256="d" * 64,
                             requested_model="unobserved-cli-default",
                             budgets=pilot.PROVISIONAL_BUDGETS)


@pytest.fixture
def task():
    return ve.load_task(DATA, "Prob900_inv")


def load(out):
    record = json.loads((out / "run.json").read_text(encoding="utf-8"))
    return record, artifacts.load_artifact(out / "submission", expected_id=record["receipt_id"])


# ------------------------------------------------------------------ arm A
def test_single_call_seals_extracted_module_unverified(manifest, task, tmp_path):
    seen = []

    def ask(role, prompt, system, budget, model):
        seen.append((role, prompt, system, model))
        budget.charge_llm()
        return GOOD

    record, receipt = load_after(pilot.run_single_call(manifest, task, tmp_path / "a", ask=ask), tmp_path / "a")
    assert receipt["kind"] == "candidate" and receipt["internal_status"] == "unverified"
    assert receipt["selection_reason"] == "latest_complete" and receipt["top"] == "TopModule"
    assert seen == [("generator", task.prompt.read_text(encoding="utf-8"), pilot.SINGLE_CALL_SYSTEM, None)]
    assert "RefModule" not in seen[0][1] and "tb" not in seen[0][1].split()  # public prompt only
    rtl = (tmp_path / "a" / "submission" / "rtl" / "TopModule.sv").read_text(encoding="utf-8")
    assert rtl.startswith("module TopModule") and record["accounting"]["llm_calls"] == 1


def load_after(_, out):
    return load(out)


def test_single_call_budget_allows_exactly_one_attempt(manifest, task, tmp_path):
    from autortl.budget import Budget
    calls = []

    def ask(role, prompt, system, budget, model):
        assert isinstance(budget, Budget) and budget.max_llm_calls == 1
        calls.append(1)
        raise RuntimeError("LLM_BUDGET: model call budget exhausted")

    record, receipt = load_after(pilot.run_single_call(manifest, task, tmp_path / "a", ask=ask), tmp_path / "a")
    assert receipt["kind"] == "missing" and receipt["termination"] == "budget" and calls == [1]


def test_single_call_model_block_and_unusable_reply_are_missing(manifest, task, tmp_path):
    def blocked(*args, **kwargs):
        raise client.ModelCallError("generator", "CODEX_QUOTA", message="quota")

    _, receipt = load_after(pilot.run_single_call(manifest, task, tmp_path / "q", ask=blocked), tmp_path / "q")
    assert (receipt["kind"], receipt["termination"]) == ("missing", "model_blocked")
    prose = lambda *a, **k: "I cannot write that module."
    record, receipt = load_after(pilot.run_single_call(manifest, task, tmp_path / "p", ask=prose), tmp_path / "p")
    assert (receipt["kind"], receipt["termination"]) == ("missing", "failed")
    assert (tmp_path / "p" / "work" / "raw_reply.txt").read_text(encoding="utf-8").startswith("I cannot")
    assert "no complete module" in record["accounting"]["error"]


def test_unregistered_or_unimplemented_arm_is_refused(manifest, task, tmp_path):
    with pytest.raises(ve.AdapterError, match="not implemented"):
        pilot._cell(manifest, task.id, "bogus", 0)
    with pytest.raises(ve.AdapterError, match="not registered"):
        pilot.run_single_call(manifest, task, tmp_path / "x", trial=3, ask=lambda *a, **k: GOOD)


# ------------------------------------------------------------------ arm C
class FakeBuild:
    def __init__(self, status="done", winner=True, timeout=False, kind=None, frozen=False,
                 child=True, timeout_after_done=False):
        self.status, self.winner, self.timeout, self.cmd, self.kind = status, winner, timeout, None, kind
        self.frozen, self.child, self.timeout_after_done = frozen, child, timeout_after_done

    def __call__(self, cmd, cwd, capture_output, text, errors, timeout):
        self.cmd = cmd
        if self.timeout:
            raise subprocess.TimeoutExpired(cmd, timeout)
        run_dir = Path(cmd[cmd.index("--output-dir") + 1])
        run_dir.mkdir(parents=True)
        top = "TopModule_top" if self.frozen else "TopModule"
        if self.status:
            summary = {"status": self.status, "top_module": top}
            if self.kind:
                summary["failure_kind"] = self.kind
            if self.frozen:
                summary["edit_scope"] = "frozen_children"
            (run_dir / "run_summary.json").write_text(json.dumps(summary))
        (run_dir / "budget.json").write_text(json.dumps({"llm_calls": 9, "vivado_seconds": 300.0, "tokens": {}}))
        if self.frozen:
            (run_dir / "design_spec.json").write_text(json.dumps({"top_name": top, "modules": [{"name": "TopModule"}]}))
            if self.child:
                (run_dir / "modules" / "TopModule").mkdir(parents=True)
                (run_dir / "modules" / "TopModule" / "TopModule.v").write_text(
                    "module TopModule(input a, output y); assign y=~a; endmodule\n")
            if self.winner:
                (run_dir / "TopModule_top_best.v").write_text(
                    "module TopModule_top(input a, output y); TopModule u(.a(a),.y(y)); endmodule\n")
        elif self.winner:
            (run_dir / "TopModule_best.v").write_text("module TopModule(input a, output y); assign y=~a; endmodule\n")
        if self.timeout_after_done:
            raise subprocess.TimeoutExpired(cmd, timeout)
        return subprocess.CompletedProcess(cmd, 0 if self.status == "done" else 1, "{}", "")


def test_full_command_uses_public_prompt_only(manifest, task, tmp_path):
    build = FakeBuild()
    pilot.run_full(manifest, task, tmp_path / "c", runner=build, python="py")
    cmd = build.cmd
    assert cmd[2:4] == ["build", "--spec"] and Path(cmd[4]).name == "Prob900_inv_prompt.txt"
    assert Path(cmd[4]).parent == tmp_path / "c" / "work"
    assert "--generate-golden" in cmd and "--tb" not in cmd
    assert not any(part.endswith(("_test.sv", "_ref.sv")) for part in cmd)
    assert cmd[cmd.index("--top") + 1] == "TopModule"
    assert cmd[cmd.index("--max-llm-calls") + 1] == "16"
    assert float(cmd[cmd.index("--max-wall-minutes") + 1]) == 35.0
    assert cmd[cmd.index("--best-of-n") + 1] == "1" and cmd[cmd.index("--iterations") + 1] == "1"
    assert cmd[cmd.index("--implementation") + 1] == "out_of_context"
    for name in ("vivado", "xvlog", "xelab", "xsim"):  # pilot_vivado_tools_unresolved
        assert cmd[cmd.index(f"--{name}") + 1] == f"C:/Vivado/bin/{name}.bat"


def test_full_done_winner_is_sealed_as_accepted_incumbent(manifest, task, tmp_path):
    record, receipt = load_after(pilot.run_full(manifest, task, tmp_path / "c", runner=FakeBuild()), tmp_path / "c")
    assert receipt["internal_status"] == "accepted" and receipt["selection_reason"] == "accepted_incumbent"
    assert [f["path"] for f in receipt["files"]] == ["rtl/TopModule_best.v"]
    assert record["accounting"]["llm_calls"] == 9 and record["accounting"]["run_status"] == "done"


@pytest.mark.parametrize("build, termination", [
    (FakeBuild(status="budget_exhausted", winner=False), "budget"),
    (FakeBuild(status="model_blocked", winner=False), "model_blocked"),
    (FakeBuild(status="infra_blocked", winner=False), "interrupted"),
    (FakeBuild(status="build_blocked", winner=False, kind="infra"), "interrupted"),
    (FakeBuild(status="build_blocked", winner=False), "failed"),
    (FakeBuild(status="baseline_failed", winner=False), "failed"),
    (FakeBuild(status="done", winner=False), "failed"),
    (FakeBuild(status=None, winner=False), "interrupted"),
    (FakeBuild(timeout=True), "interrupted"),
])
def test_full_without_done_winner_is_missing(manifest, task, tmp_path, build, termination):
    _, receipt = load_after(pilot.run_full(manifest, task, tmp_path / "c", runner=build), tmp_path / "c")
    assert (receipt["kind"], receipt["termination"]) == ("missing", termination)


def test_full_refuses_reused_output_directory(manifest, task, tmp_path):
    (tmp_path / "c" / "work").mkdir(parents=True)
    with pytest.raises(FileExistsError):
        pilot.run_full(manifest, task, tmp_path / "c", runner=FakeBuild())


# --------------------------------------------------------------- grading
def test_grade_run_grades_sealed_candidate_and_skips_missing(manifest, task, tmp_path, monkeypatch):
    pilot.run_full(manifest, task, tmp_path / "c", runner=FakeBuild())
    graded = []
    monkeypatch.setattr(ve, "grade", lambda files, t, workdir, **kw: graded.append(files) or
                        (Path(workdir).mkdir(parents=True) or {"task": t.id, "status": "pass"}))
    verdict = pilot.grade_run(manifest, task, tmp_path / "c", tmp_path / "g1")
    assert verdict["status"] == "pass" and verdict["internal_status"] == "accepted"
    assert [p.name for p in graded[0]] == ["TopModule_best.v"]
    pilot.run_full(manifest, task, tmp_path / "m", runner=FakeBuild(status="model_blocked", winner=False))
    missing = pilot.grade_run(manifest, task, tmp_path / "m", tmp_path / "g2")
    assert missing["status"] == "missing" and len(graded) == 1
    assert json.loads((tmp_path / "g2" / "verdict.json").read_text())["termination"] == "model_blocked"


def test_grade_run_rejects_tampered_submission(manifest, task, tmp_path):
    pilot.run_full(manifest, task, tmp_path / "c", runner=FakeBuild())
    (tmp_path / "c" / "submission" / "rtl" / "TopModule_best.v").write_text("module TopModule(); endmodule\n")
    with pytest.raises(artifacts.ArtifactError):
        pilot.grade_run(manifest, task, tmp_path / "c", tmp_path / "g")


def test_cli_select_and_manifest(tmp_path, monkeypatch):
    catalog = {f"{p}{i}": {"category": c, "family": f"{p}{i}"} for c, p in zip(ve.CATEGORIES, "LAQF")
               for i in range(2)}
    (tmp_path / "catalog.json").write_text(json.dumps(catalog))
    assert pilot.main(["select", "--catalog", str(tmp_path / "catalog.json"), "--commit", "e" * 40,
                       "--out", str(tmp_path / "pilot.json")]) == 0
    assert len(json.loads((tmp_path / "pilot.json").read_text())["pilot"]) == 6
    monkeypatch.setattr(pilot, "_git_head", lambda: "f" * 40)
    out = tmp_path / "m.json"
    assert pilot.main(["manifest", "--dataset", str(DATA), "--commit", "a" * 40, "--tasks", "Prob900_inv",
                       "--runtime-sha256", "0" * 64, "--out", str(out)]) == 0
    assert artifacts.load_manifest(out, public_root=DATA, private_root=DATA)["identity"]["source_commit"] == "f" * 40
    with pytest.raises(FileExistsError):
        pilot.main(["manifest", "--dataset", str(DATA), "--commit", "a" * 40, "--tasks", "Prob900_inv",
                    "--runtime-sha256", "0" * 64, "--out", str(out)])


def test_full_command_passes_real_run_py_validation(manifest, task, tmp_path):
    """pilot_runner_double_hid_cli_rejection: execute the real parser and config.

    A zero model-call budget stops the run at its first model call, after every
    argument and RunConfig check, so no model or Vivado tool runs.
    """
    import sys
    request = tmp_path / task.prompt.name
    request.write_bytes(task.prompt.read_bytes())
    budget = dict(manifest["cells"][0]["budget"], model_calls=0)
    cmd = pilot.full_command(request, tmp_path / "run", budget, python=sys.executable)
    done = subprocess.run(cmd, cwd=str(pilot.REPO), capture_output=True, text=True, timeout=120)
    assert "must be positive" not in done.stderr and "error:" not in done.stderr, done.stderr
    summary = json.loads((tmp_path / "run" / "run_summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "budget_exhausted"


def test_unresolved_vivado_stops_before_the_cell_directory(manifest, task, tmp_path, monkeypatch):
    def missing():
        raise ve.GraderUnavailable("Vivado tools not found on PATH: xvlog")
    monkeypatch.setattr(pilot, "vivado_tools", missing)
    with pytest.raises(ve.GraderUnavailable):
        pilot.run_full(manifest, task, tmp_path / "c", runner=FakeBuild())
    assert not (tmp_path / "c").exists()


def test_frozen_children_submission_includes_verified_children(manifest, task, tmp_path):
    """pilot_submission_missing_children: the official test instantiates TopModule."""
    _, receipt = load_after(pilot.run_full(manifest, task, tmp_path / "c", runner=FakeBuild(frozen=True)), tmp_path / "c")
    assert [f["path"] for f in receipt["files"]] == ["rtl/modules/TopModule/TopModule.v", "rtl/TopModule_top_best.v"]
    assert receipt["top"] == "TopModule_top" and receipt["internal_status"] == "accepted"


def test_frozen_children_without_child_source_is_missing(manifest, task, tmp_path):
    _, receipt = load_after(pilot.run_full(manifest, task, tmp_path / "c", runner=FakeBuild(frozen=True, child=False)),
                            tmp_path / "c")
    assert (receipt["kind"], receipt["termination"]) == ("missing", "failed")


def test_done_summary_survives_outer_wall_clock_timeout(manifest, task, tmp_path):
    """pilot_outer_timeout_discarded_done: the safety net counts sleep; DONE is final."""
    record, receipt = load_after(pilot.run_full(manifest, task, tmp_path / "c",
                                                runner=FakeBuild(timeout_after_done=True)), tmp_path / "c")
    assert receipt["kind"] == "candidate" and record["accounting"]["outer_timeout"] is True



def test_ablation_arm_skips_only_mutation_qualification(manifest, task, tmp_path):
    """ablation_policy_seam_absent: arm B is arm C plus one recorded policy flag."""
    cell = next(c for c in manifest["cells"] if c["arm"] == "ablation")
    assert cell["verification_policy"] == "skip_generated_tb_mutations"
    full, ablation = FakeBuild(), FakeBuild()
    pilot.run_full(manifest, task, tmp_path / "c", runner=full)
    pilot.run_full(manifest, task, tmp_path / "b", runner=ablation, arm="ablation")
    assert "--verification-policy" not in full.cmd
    flag = ablation.cmd.index("--verification-policy")
    assert ablation.cmd[flag + 1] == "skip_generated_tb_mutations"
    rest = ablation.cmd[:flag] + ablation.cmd[flag + 2:]
    assert len(rest) == len(full.cmd)  # nothing else differs in shape
    _, receipt = load_after(None, tmp_path / "b")
    assert receipt["cell"]["arm"] == "ablation"


def test_run_full_refuses_single_call_arm(manifest, task, tmp_path):
    with pytest.raises(ve.AdapterError, match="full or ablation"):
        pilot.run_full(manifest, task, tmp_path / "x", runner=FakeBuild(), arm="single_call")


def test_ablation_command_passes_real_run_py_validation(manifest, task, tmp_path):
    import sys
    request = tmp_path / task.prompt.name
    request.write_bytes(task.prompt.read_bytes())
    budget = dict(manifest["cells"][0]["budget"], model_calls=0)
    cmd = pilot.full_command(request, tmp_path / "run", budget, python=sys.executable,
                             verification_policy="skip_generated_tb_mutations")
    done = subprocess.run(cmd, cwd=str(pilot.REPO), capture_output=True, text=True, timeout=120)
    assert "error:" not in done.stderr, done.stderr
    summary = json.loads((tmp_path / "run" / "run_summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "budget_exhausted"
