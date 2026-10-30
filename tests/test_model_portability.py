"""Model portability: response formats other models use, and a run-pinned model.

Taxonomy: fence_tag_drops_generated_modules, golden_fence_tag_keeps_prose,
evaluator_verdict_format_rejects_verified_gain, unpinned_model_identity.
"""
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from autortl.config import RunConfig
from autortl.roles import Evaluation, Planner, Generator, Evaluator, TimingDoctor, golden_source
from curriculum import runner
from llm import client
from llm.client import extract_verilog
import run
from tests.test_curriculum import curriculum, records  # noqa: F401  (fixture reuse)

TWO = ("module a(input x, output y);\n  b u(.x(x), .y(y));\nendmodule\n\n"
       "module b(input x, output y);\n  assign y = x;\nendmodule")


@pytest.mark.parametrize("tag", ["verilog", "Verilog", "VERILOG", "v", "sv", "SystemVerilog", ""])
def test_every_hdl_fence_tag_keeps_all_modules(tag):
    response = f"Here is the design.\n\n```{tag}\n{TWO}\n```\n\nThis keeps behavior."
    assert extract_verilog(response) == TWO


def test_crlf_fences_are_read():
    response = "Design:\r\n```Verilog\r\n" + TWO.replace("\n", "\r\n") + "\r\n```\r\n"
    assert extract_verilog(response).replace("\r\n", "\n") == TWO


def test_hdl_fence_wins_over_other_tags_that_mention_modules():
    response = ("```text\nmodule tb; // excerpt from the testbench\nendmodule\n```\n"
                f"```Verilog\n{TWO}\n```")
    assert extract_verilog(response) == TWO


def test_unusual_tag_still_yields_a_module_when_no_hdl_fence_exists():
    response = f"```verilog2001\n{TWO}\n```"
    assert extract_verilog(response) == TWO


CODE = "def init():\n    return 0\n\ndef step(state, inputs):\n    return state, {'y': 0}"


@pytest.mark.parametrize("tag", ["python", "Python", "py", "python3"])
def test_golden_fence_tags(tag):
    assert golden_source(f"Here is the model.\n```{tag}\n{CODE}\n```\nDone.") == CODE


def test_golden_untagged_or_odd_fence_with_init_and_step():
    assert golden_source(f"Model:\n```\n{CODE}\n```") == CODE
    assert golden_source(f"Model:\n```text\nnotes\n```\n```pycon\n{CODE}\n```") == CODE


def test_golden_python_tag_wins_and_raw_text_is_last_resort():
    assert golden_source(f"```\ndef init():\n    pass\n```\n```python\n{CODE}\n```") == CODE
    assert golden_source(CODE) == CODE


VALID = "## Contract check\n- LUT target: PASS - fewer\n- timing: PASS - met\n## Summary\n- Passed: 2 of 2\n- Failed: 0 of 2\n"


@pytest.mark.parametrize("verdict", ["## Recommendation\nACCEPT", "## Recommendation: ACCEPT",
                                     "**Recommendation:** ACCEPT", "## Recommendation\n**ACCEPT**",
                                     "### Recommendation\nACCEPT", "Recommendation: accept",
                                     "## Recommendation\r\nACCEPT", "## Recommendation\nACCEPT - all criteria pass"])
def test_verdict_forms_other_models_write(verdict):
    assert Evaluation.parse(VALID + verdict).recommendation == "ACCEPT"


@pytest.mark.parametrize("verdict", ["## Recommendation\nACCEPT | REJECT | RESTART",
                                     "## Recommendation\nREJECT", "Recommendation: **REJECT**",
                                     "## Recommendation\nACCEPT, though REJECT if timing regresses",
                                     "I recommend ACCEPT", ""])
def test_ambiguous_missing_or_negative_verdicts_reject(verdict):
    assert Evaluation.parse(VALID + verdict).recommendation == "REJECT"


def test_deterministic_vetoes_still_override_a_tolerant_accept():
    failing = VALID.replace("- timing: PASS - met", "- timing: FAIL - missed")
    assert Evaluation.parse(failing + "Recommendation: ACCEPT").recommendation == "REJECT"
    inconsistent = VALID.replace("Passed: 2 of 2", "Passed: 2 of 3")
    assert Evaluation.parse(inconsistent + "Recommendation: ACCEPT").recommendation == "REJECT"


@pytest.fixture
def router(monkeypatch, tmp_path):
    monkeypatch.setattr(client, "_STATS_PATH", tmp_path / "stats.jsonl")
    monkeypatch.setattr(client, "_load_routing", lambda: {
        "roles": {"generator": {"chain": ["codex.default"]}},
        "defaults": {"max_retries_per_backend": 2, "timeout_s": 180}})
    backend = Mock()
    backend.ask.return_value = ("RTL", {})
    monkeypatch.setattr(client, "_BACKENDS", {"codex": backend})
    return backend


def test_pinned_model_replaces_the_alias_and_keeps_the_backend(router):
    assert client.ask("generator", "request", model="gpt-5.6-luna") == "RTL"
    assert router.ask.call_args.args[0] == "gpt-5.6-luna"


def test_no_model_keeps_the_routing_default(router):
    client.ask("generator", "request")
    assert router.ask.call_args.args[0] == "default"


def test_every_role_call_carries_the_run_model(monkeypatch):
    seen = []
    monkeypatch.setattr("autortl.roles.ask", lambda role, prompt, **kw: seen.append((role, kw.get("model"))) or "ok")
    planner, evaluator = Planner(), Evaluator()
    planner.model = evaluator.model = "gpt-6.1-sol"
    evaluator.review_contract("contract", None)
    planner.refine_contract("contract", "feedback", None)
    assert seen == [("evaluator", "gpt-6.1-sol"), ("planner", "gpt-6.1-sol")]


def test_orchestrator_hands_the_model_to_every_role(tmp_path):
    from autortl.fsm import Orchestrator
    cfg = RunConfig(mode="optimize", model="gpt-5.6-luna")
    orch = Orchestrator(cfg, run_dir=tmp_path / "run")
    assert [r.model for r in (orch.planner, orch.generator, orch.evaluator, orch.doctor)] == ["gpt-5.6-luna"] * 4
    assert isinstance(orch.generator, Generator) and isinstance(orch.doctor, TimingDoctor)


@pytest.mark.parametrize("bad", ["", "gpt 5", "--model", "a;b", "x" * 121, "../x", 5])
def test_model_alias_is_validated(bad):
    with pytest.raises(ValueError, match="model"):
        RunConfig(mode="optimize", model=bad).validate()


def test_model_round_trips_and_older_configs_migrate(tmp_path):
    cfg = RunConfig(mode="optimize", model="gpt-6.1-sol", work_dir=tmp_path)
    cfg.save(tmp_path / "config.json")
    assert RunConfig.load(tmp_path / "config.json").model == "gpt-6.1-sol"
    data = cfg.to_dict()
    del data["model"]
    assert RunConfig.from_dict(data).model is None


def test_cli_model_option_reaches_the_config(tmp_path, monkeypatch):
    orch = Mock()
    orch.return_value.run.return_value = {"status": "done"}
    monkeypatch.setattr(run, "Orchestrator", orch)
    assert run.main(["optimize", "--design", "d.v", "--top", "d", "--output-dir", str(tmp_path),
                     "--model", "gpt-5.6-luna"]) == 0
    assert orch.call_args.args[0].model == "gpt-5.6-luna"


def test_bench_records_a_requested_model_and_separates_cohorts(curriculum):  # noqa: F811
    _, orch, output = curriculum
    assert runner.run_tier(0, output_root=output) == 0
    assert runner.run_tier(0, output_root=output, model="gpt-5.6-luna") == 0
    default, pinned = records()[-2:]
    assert default["runtime_identity"]["model_identity_status"] == "unobserved_cli_default"
    assert pinned["runtime_identity"]["model_identity"] == "gpt-5.6-luna"
    assert pinned["runtime_identity"]["model_identity_status"] == "requested"
    assert default["cohort"] != pinned["cohort"]
    assert pinned["consecutive_qualifying_runs"] == 1
    assert orch.call_args.args[0].model == "gpt-5.6-luna"


def test_a_later_contradicting_verdict_rejects():
    # evaluator_verdict_conflict_or_blank_line (independent review)
    assert Evaluation.parse(VALID + "Recommendation: ACCEPT\n## Recommendation\nREJECT").recommendation == "REJECT"
    assert Evaluation.parse(VALID + "Recommendation: ACCEPT\n**Recommendation:** ACCEPT").recommendation == "ACCEPT"


def test_blank_lines_after_the_heading_are_allowed():
    assert Evaluation.parse(VALID + "## Recommendation\n\nACCEPT").recommendation == "ACCEPT"
    assert Evaluation.parse(VALID + "## Recommendation\r\n\r\n**ACCEPT**").recommendation == "ACCEPT"


def test_modules_in_separate_fences_are_joined_when_names_are_distinct():
    a, b = TWO.split("\n\n")
    assert extract_verilog(f"Top:\n```verilog\n{a}\n```\nChild:\n```Verilog\n{b}\n```") == TWO


def test_repeated_module_names_across_fences_keep_the_first_block():
    a = TWO.split("\n\n")[0]
    later = a.replace("b u(", "b v(")
    assert extract_verilog(f"Before:\n```verilog\n{a}\n```\nAfter:\n```verilog\n{later}\n```") == a
