"""An independent reading of a prose request checks the planner-written spec.

Taxonomy: planner_spec_error_shared_by_oracle_and_rtl (VerilogEval Prob066, Prob139,
Prob135): the golden model, generated testbench and RTL all derive from the planner's
spec, so a misreading of the request was verified and accepted. With
spec_cross_check=request_traces a separate role call writes traces from the request
and the port list only; a disagreement with the qualified oracle replans once from
the shared max_fix_attempts counter. A supplied JSON spec is law and never checked.
"""
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

import run
from autortl import cross_check, fsm, roles
from autortl.config import SPEC_CROSS_CHECK_POLICIES, RunConfig
from autortl.golden import GoldenModel, GoldenTimeoutError
from autortl.spec import DesignSpec
from llm.client import ModelCallError
from tests.test_fsm_build import create
from tests.test_spec_dispute import ORACLE, checkpoint, resumed
from tests.test_spec_repair import GOOD, prose, same_name_as_module

FIXTURES = Path(__file__).parent / "fixtures" / "cross_check"
ANSWER = (FIXTURES / "counter8_answer.txt").read_text(encoding="utf-8")
BAD_ANSWER = (FIXTURES / "counter8_bad_answer.txt").read_text(encoding="utf-8")

# A planner misreading: enable LOW increments. Its own examples and oracle agree with
# it, so the v1.0.0 ladder would verify and accept it.
INVERTED = ORACLE.replace('elif inputs["enable"]:', 'elif not inputs["enable"]:')


def wrong():
    spec = json.loads(GOOD)
    module = spec["modules"][0]
    module["behavior"] = module["behavior"].replace("else enable increments", "else enable low increments")
    module["examples"][1]["inputs"]["enable"] = 0
    return json.dumps(spec)


def module(text=GOOD):
    return DesignSpec.from_json(text).modules[0]


def oracle_file(tmp_path, source):
    path = tmp_path / "golden.py"
    path.write_text(source, encoding="utf-8")
    return GoldenModel(path)


def cross_checked_build(tmp_path, monkeypatch, planner_outputs, oracles, answers=(ANSWER,)):
    """A prose build with a generated oracle and the request_traces policy."""
    o, synthesis = create(tmp_path, monkeypatch)
    prose(tmp_path, o)
    o.cfg.testbench_path = None
    assert o.cfg.spec_cross_check == "off"  # the default until ROADMAP V1 measures it
    o.cfg.spec_cross_check = "request_traces"
    planner = Mock(side_effect=planner_outputs)
    traces = Mock(side_effect=list(answers))
    golden = Mock(side_effect=oracles)
    monkeypatch.setattr(o.planner, "make_spec", planner)
    monkeypatch.setattr(o.planner, "request_traces", traces)
    monkeypatch.setattr(o.generator, "golden_model", golden)
    return o, planner, traces, golden, synthesis


def events(o, stage="spec_cross_check"):
    return [e for e in o.state.read_events() if e.get("stage") == stage]


# ------------------------------------------------------------------ parser and comparison
def test_parser_accepts_a_fenced_answer_fixture():
    traces, errors = cross_check.parse_traces(ANSWER, module())
    assert errors == []
    assert [t["index"] for t in traces] == [0, 1]
    assert traces[0]["quote"] == "enable increments count modulo 256, else hold"
    assert traces[1]["rows"][2] == {"inputs": {"rst": 1}, "expected": {"count": 2}}


def test_parser_rejects_bad_traces_one_by_one():
    traces, errors = cross_check.parse_traces(BAD_ANSWER, module())
    assert [t["quote"] for t in traces] == ["count holds"]
    joined = "\n".join(errors)
    assert "trace 0: row 0 inputs enable must be an integer in 0..1" in joined
    assert "trace 1: row 0 inputs: 'clk' is not one of ['enable', 'rst']" in joined
    assert "trace 2: row 0 expected: 'total' is not one of ['count']" in joined
    assert "trace 3: needs a quote" in joined
    assert "trace 4: no row has an expected output" in joined
    assert cross_check.parse_traces("no json here", module())[1] == [
        'answer must be one JSON object {"traces": [...]} with at least one trace']
    assert "not JSON" in cross_check.parse_traces("{traces: [}", module())[1][0]


def test_parser_bounds_rows_and_traces():
    row = {"inputs": {"enable": 1}, "expected": {"count": 1}}
    many = json.dumps({"traces": [{"quote": "q", "rows": [row] * (cross_check.MAX_ROWS + 1)}]
                       + [{"quote": "q", "rows": [row]}] * cross_check.MAX_TRACES})
    traces, errors = cross_check.parse_traces(many, module())
    assert len(traces) == cross_check.MAX_TRACES - 1
    assert any(f"at most {cross_check.MAX_ROWS} rows" in e for e in errors)
    assert any(f"only the first {cross_check.MAX_TRACES}" in e for e in errors)


def test_rows_map_to_golden_steps_by_the_spec_latency(tmp_path):
    good, bad = oracle_file(tmp_path, ORACLE), oracle_file(tmp_path, INVERTED)
    traces, _ = cross_check.parse_traces(ANSWER, module())
    assert cross_check.stimulus(module(), traces[0])[3] == {"rst": 0, "enable": 0}
    mismatches, compared = cross_check.run_traces(good, module(), traces)
    assert mismatches == [] and compared == 8  # row 0 precedes the latency-1 observation
    mismatches, _ = cross_check.run_traces(bad, module(wrong()), traces)
    assert mismatches[0] == {"trace": 0, "row": 1, "port": "count", "request_reading": 1, "spec_model": 0}
    # A latency-0 reading of the same oracle is one cycle early: the Prob139 class.
    early = module()
    early.latency = 0
    assert cross_check.run_traces(good, early, traces)[0]


def test_feedback_shows_each_disagreeing_trace_up_to_its_last_mismatch(tmp_path):
    traces, _ = cross_check.parse_traces(ANSWER, module())
    mismatches, _ = cross_check.run_traces(oracle_file(tmp_path, INVERTED), module(wrong()), traces)
    text = cross_check.feedback_text(module(), traces, mismatches)
    assert 'trace 0, relying on the request text: "enable increments count modulo 256, else hold"' in text
    assert "  row 1: inputs {enable=1} -> request reading {count=1}, spec model {count=0}" in text
    assert len(text) <= cross_check.FEEDBACK_MAX_CHARS
    long = cross_check.feedback_text(module(), traces * 40, mismatches * 40)
    assert len(long) <= cross_check.FEEDBACK_MAX_CHARS and long.endswith("[further rows truncated]")


def test_skip_reasons():
    assert cross_check.skip_reason(module()) == ""
    scoreboard = module()
    scoreboard.compare_mode = "scoreboard"
    assert "transactions" in cross_check.skip_reason(scoreboard)


def test_trace_writer_sees_the_request_and_ports_never_the_planner_spec(monkeypatch):
    seen = {}
    monkeypatch.setattr(roles, "ask", lambda name, prompt, **kw: seen.update(name=name, prompt=prompt, **kw) or ANSWER)
    planner = roles.Planner()
    planner.run_context = "AUTHORITATIVE FACTS THAT MUST NOT LEAK"
    m = module()
    interface = cross_check.interface_text(m)
    assert planner.request_traces("Build an 8-bit counter named counter8.", interface, None) == ANSWER
    prompt = seen["prompt"]
    assert seen["name"] == "planner"
    assert "Build an 8-bit counter named counter8." in prompt and "input wire enable" in prompt
    assert "rst (sync, asserted when rst=1)" in prompt
    for leaked in (m.behavior, "latency", "after_cycles", "MUST NOT LEAK", "examples"):
        assert leaked not in prompt


# ------------------------------------------------------------------ configuration
def test_policy_default_validation_legacy_and_cli(tmp_path, monkeypatch):
    assert SPEC_CROSS_CHECK_POLICIES == ("request_traces", "off")
    assert RunConfig(mode="build").spec_cross_check == "off"
    with pytest.raises(ValueError, match="spec_cross_check"):
        RunConfig(mode="build", spec_cross_check="maybe").validate()
    cfg = RunConfig(mode="build", spec_cross_check="request_traces", work_dir=tmp_path)
    cfg.save(tmp_path / "config.json")
    saved = json.loads((tmp_path / "config.json").read_text())
    assert RunConfig.from_dict(saved).spec_cross_check == "request_traces"
    saved.pop("spec_cross_check")  # a config.json written before the check existed
    assert RunConfig.from_dict(saved).spec_cross_check == "off"
    seen = []

    class Fake:
        def __init__(self, cfg, run_dir=None):
            seen.append(cfg)
            self.state = Mock(run_dir=tmp_path)

        def run(self):
            return {"status": "done"}

    monkeypatch.setattr(run, "Orchestrator", Fake)
    monkeypatch.setattr("llm.client.check_model", lambda model: None)
    spec = tmp_path / "spec.md"
    spec.write_text("x")
    assert run.main(["build", "--spec", str(spec)]) == 0
    assert run.main(["build", "--spec", str(spec), "--spec-cross-check", "request_traces"]) == 0
    assert [c.spec_cross_check for c in seen] == ["off", "request_traces"]
    design = tmp_path / "d.v"
    design.write_text("module d; endmodule")
    for argv in (["build", "--spec", str(spec), "--spec-cross-check", "sometimes"],
                 ["optimize", "--design", str(design), "--top", "d", "--spec-cross-check", "off"],
                 ["bench", "--tier", "0", "--spec-cross-check", "off"]):
        with pytest.raises(SystemExit):
            run.main(argv)


# ------------------------------------------------------------------ build flow
def test_agreeing_traces_cost_one_call_and_are_recorded(tmp_path, monkeypatch):
    o, planner, traces, golden, synthesis = cross_checked_build(tmp_path, monkeypatch, [GOOD], [ORACLE])
    result = o.run()
    assert result["status"] == "done"
    assert planner.call_count == 1 and traces.call_count == 1 and golden.call_count == 1
    intent, interface = traces.call_args.args[:2]
    assert intent == "Build an 8-bit counter named counter8." and interface == cross_check.interface_text(module())
    state = checkpoint(o)
    assert [(c["revision"], c["outcome"], c["compared"]) for c in state["spec_cross_checks"]] == [(0, "agree", 8)]
    assert result["spec_cross_check"] == {"policy": "request_traces", "checks": state["spec_cross_checks"]}
    assert json.loads((o.state.run_dir / "run_summary.json").read_text())["spec_cross_check"]["checks"][0]["outcome"] == "agree"
    saved = json.loads((o.state.run_dir / "spec_cross_checks/traces.json").read_text())
    assert saved["model_calls"] == 1 and len(saved["traces"]) == 2
    assert [e["outcome"] for e in events(o)] == ["agree"]
    assert "spec_repairs" not in state
    assert synthesis.call_count == 1


def test_a_misread_spec_is_replanned_once_and_the_repair_builds(tmp_path, monkeypatch):
    o, planner, traces, golden, _ = cross_checked_build(tmp_path, monkeypatch, [wrong(), GOOD], [INVERTED, ORACLE])
    result = o.run()
    assert result["status"] == "done"
    assert planner.call_count == 2 and golden.call_count == 2
    assert traces.call_count == 1  # written once, reused for the replanned revision
    feedback = planner.call_args_list[1].kwargs["feedback"]
    assert feedback.startswith("Repair attempt 1.\nmodule counter8_core: " + fsm.SPEC_CROSS_CHECK_INSTRUCTION)
    assert '"enable increments count modulo 256, else hold"' in feedback
    assert "request reading {count=1}, spec model {count=0}" in feedback
    assert "Your previous design_spec was:\n" + wrong() in feedback
    assert len(feedback) < 8000
    run_dir = o.state.run_dir
    assert not (run_dir / "modules/counter8_core/counter8_core.v").exists()  # no RTL for the misread spec
    assert (run_dir / "modules_rev1/counter8_core/counter8_core.v").is_file()
    state = checkpoint(o)
    assert state["spec_repairs"] == 1
    assert [(c["revision"], c["outcome"]) for c in state["spec_cross_checks"]] == [(0, "replanned"), (1, "agree")]
    assert state["spec_cross_checks"][0]["spec_repair"] == 1
    assert json.loads((run_dir / "spec_cross_checks/rev0.json").read_text())["mismatches"][0]["row"] == 1
    assert [r["revision"] for r in state["spec_revisions"]] == [0, 1]
    assert [c["outcome"] for c in result["spec_cross_check"]["checks"]] == ["replanned", "agree"]


def test_a_disagreement_the_planner_keeps_is_recorded_and_never_fails_the_build(tmp_path, monkeypatch):
    o, planner, traces, golden, synthesis = cross_checked_build(
        tmp_path, monkeypatch, [wrong(), wrong()], [INVERTED, INVERTED])
    o.cfg.max_fix_attempts = 3
    result = o.run()
    assert result["status"] == "done"
    assert planner.call_count == 2  # one cross-check replan per run, however many repairs remain
    outcomes = [c["outcome"] for c in checkpoint(o)["spec_cross_checks"]]
    assert outcomes == ["replanned", "disagreement_kept"]
    assert result["spec_cross_check"]["checks"][1]["mismatches"]
    assert checkpoint(o)["spec_repairs"] == 1 and synthesis.call_count == 1


def test_cross_check_shares_the_planner_repair_counter(tmp_path, monkeypatch):
    # max_fix_attempts is 1: the lint repair spends it, so the disagreement cannot replan.
    o, planner, traces, golden, _ = cross_checked_build(
        tmp_path, monkeypatch, [same_name_as_module(wrong()), wrong()], [INVERTED])
    result = o.run()
    assert result["status"] == "done"
    assert planner.call_count == 2 and golden.call_count == 1
    state = checkpoint(o)
    assert state["spec_repairs"] == 1
    assert [c["outcome"] for c in state["spec_cross_checks"]] == ["repairs_exhausted"]
    assert state["spec_cross_checks"][0].get("spec_repair") is None


def test_an_oracle_dispute_and_a_cross_check_replan_share_the_counter(tmp_path, monkeypatch):
    from tests.test_spec_dispute import disputed
    o, planner, traces, golden, _ = cross_checked_build(
        tmp_path, monkeypatch, [disputed(), wrong(), GOOD], [ORACLE, ORACLE, INVERTED, ORACLE])
    o.cfg.max_fix_attempts = 2
    result = o.run()
    assert result["status"] == "done"
    assert planner.call_count == 3
    state = checkpoint(o)
    assert state["spec_repairs"] == 2
    assert [d["outcome"] for d in state["spec_disputes"]] == ["replanned"]
    assert [(c["revision"], c["outcome"]) for c in state["spec_cross_checks"]] == [(1, "replanned"), (2, "agree")]
    assert "Repair attempt 2." in planner.call_args_list[2].kwargs["feedback"]


def test_unusable_traces_get_one_repair_then_the_build_continues(tmp_path, monkeypatch):
    o, planner, traces, golden, _ = cross_checked_build(
        tmp_path, monkeypatch, [GOOD], [ORACLE], answers=["no json", "still no json"])
    result = o.run()
    assert result["status"] == "done"
    assert traces.call_count == 2
    assert "at least one trace" in traces.call_args_list[1].kwargs["feedback"]
    check = checkpoint(o)["spec_cross_checks"][0]
    assert check["outcome"] == "unusable" and check["trace_model_calls"] == 2


def test_supplied_json_spec_is_never_cross_checked(tmp_path, monkeypatch):
    o, _ = create(tmp_path, monkeypatch)  # make_spec and request_traces raise if called
    supplied = tmp_path / "spec.json"
    supplied.write_text(wrong(), encoding="utf-8")
    o.cfg.spec_path = supplied
    o.cfg.testbench_path = None
    monkeypatch.setattr(o.generator, "golden_model", Mock(return_value=INVERTED))
    result = o.run()
    assert result["status"] == "done"  # the supplied spec is law, misreading or not
    assert "spec_cross_check" not in result and "spec_cross_checks" not in checkpoint(o)
    assert events(o) == []


def test_policy_off_skips_and_records_it(tmp_path, monkeypatch):
    o, planner, traces, golden, _ = cross_checked_build(tmp_path, monkeypatch, [wrong()], [INVERTED])
    o.cfg.spec_cross_check = "off"
    result = o.run()
    assert result["status"] == "done"  # the v1.0.0 false acceptance, reproducible as an arm
    traces.assert_not_called()
    assert result["spec_cross_check"] == {"policy": "off", "checks": []}
    assert [(e["outcome"], e["policy"]) for e in events(o)] == [("skipped_by_policy", "off")]
    assert json.loads((o.state.run_dir / "config.json").read_text())["spec_cross_check"] == "off"


def test_trusted_testbench_build_writes_no_oracle_and_no_traces(tmp_path, monkeypatch):
    o, _ = create(tmp_path, monkeypatch)
    prose(tmp_path, o)
    monkeypatch.setattr(o.planner, "make_spec", Mock(return_value=GOOD))
    o.cfg.spec_cross_check = "request_traces"
    result = o.run()  # request_traces raises if called
    assert result["status"] == "done"
    assert result["spec_cross_check"] == {"policy": "request_traces", "checks": []}


def test_oracle_timeout_during_the_check_is_infra(tmp_path, monkeypatch):
    o, planner, traces, golden, synthesis = cross_checked_build(tmp_path, monkeypatch, [wrong(), GOOD], [INVERTED])
    monkeypatch.setattr(fsm.cross_check, "run_traces", Mock(side_effect=GoldenTimeoutError("timed out")))
    result = o.run()
    assert result["status"] == "build_blocked" and result["failure_kind"] == "infra"
    assert "spec_cross_checks" not in checkpoint(o) and "spec_repairs" not in checkpoint(o)
    assert planner.call_count == 1
    synthesis.assert_not_called()


def test_trace_writer_unavailable_is_infra(tmp_path, monkeypatch):
    o, planner, traces, golden, synthesis = cross_checked_build(
        tmp_path, monkeypatch, [GOOD], [ORACLE], answers=[ModelCallError("planner", "CODEX_UNAVAILABLE")])
    result = o.run()
    assert result["status"] == "model_blocked" and result["error_code"] == "CODEX_UNAVAILABLE"
    assert result["spec_cross_check"]["checks"] == []
    synthesis.assert_not_called()


def test_resume_replays_traces_and_the_replan_then_finishes(tmp_path, monkeypatch):
    unavailable = ModelCallError("planner", "CODEX_UNAVAILABLE")
    o, planner, traces, golden, _ = cross_checked_build(tmp_path, monkeypatch, [wrong(), unavailable], [INVERTED])
    assert o.run()["status"] == "model_blocked"
    state = checkpoint(o)
    assert state["spec_repairs"] == 1 and [c["outcome"] for c in state["spec_cross_checks"]] == ["replanned"]
    planner2, golden2 = Mock(return_value=GOOD), Mock(return_value=ORACLE)
    traces2 = Mock(side_effect=AssertionError("traces replay from the journal"))
    again = resumed(o, monkeypatch, planner__make_spec=planner2, generator__golden_model=golden2,
                    planner__request_traces=traces2)
    result = again.run()
    assert result["status"] == "done"
    assert planner2.call_count == 1 and golden2.call_count == 1
    assert fsm.SPEC_CROSS_CHECK_INSTRUCTION in planner2.call_args.kwargs["feedback"]
    state = checkpoint(again)
    assert state["spec_repairs"] == 1
    assert [c["outcome"] for c in state["spec_cross_checks"]] == ["replanned", "agree"]
    assert [r["revision"] for r in state["spec_revisions"]] == [0, 1]


def test_resume_refuses_a_cross_check_that_differs_from_the_checkpoint(tmp_path, monkeypatch):
    unavailable = ModelCallError("planner", "CODEX_UNAVAILABLE")
    o, planner, traces, golden, _ = cross_checked_build(tmp_path, monkeypatch, [wrong(), unavailable], [INVERTED])
    assert o.run()["status"] == "model_blocked"
    state = checkpoint(o)
    state["spec_cross_checks"][0]["outcome"] = "agree"
    (o.state.run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
    again = resumed(o, monkeypatch, planner__make_spec=Mock(return_value=GOOD),
                    generator__golden_model=Mock(return_value=ORACLE))
    result = again.run()
    assert result["status"] == "infra_blocked" and "cross-check 0" in result["error"]


def test_resume_refuses_a_policy_change(tmp_path, monkeypatch):
    o, *_ = cross_checked_build(tmp_path, monkeypatch, [GOOD], [ORACLE])
    assert o.run()["status"] == "done"
    cfg = RunConfig.load(o.state.run_dir / "config.json")
    cfg.spec_cross_check = "off"
    with pytest.raises(ValueError, match="Resume configuration changed: spec_cross_check"):
        fsm.Orchestrator(cfg, o.state.run_dir).run()
