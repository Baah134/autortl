"""A design whose fixed interface exceeds the package is a target failure, not a bug.

Taxonomy: io_overutilization_sent_to_fixer. The fixture is the real Vivado
2025.2 output of explore-tier5-02 axil_regs_build iteration 0: the baseline
passed its independent testbench, then place_design failed with
[Place 30-415] (165 I/O ports, 106 user I/O on xc7a35tcpg236-1) followed by
one [Place 30-68] line per unplaced buffer.
"""
import json
from pathlib import Path

import pytest

from autortl import fsm, vivado
from autortl.config import RunConfig
from autortl.triage import FailureKind, classify, describe_target, target_capacity
from curriculum import runner
from tests.test_curriculum import curriculum, records, successful_metrics  # noqa: F401
from tests.test_fsm_baseline import assert_no_winner, harness  # noqa: F401
from tests.test_infra_not_history import entry_outcomes

LOG = (Path(__file__).resolve().parent / "fixtures" / "place_io_overutilization.log").read_text(
    encoding="utf-8", errors="replace")


def test_real_io_overutilization_log_is_a_target_failure():
    assert classify(LOG) == FailureKind.TARGET
    capacity = target_capacity(LOG)
    assert (capacity["io_ports"], capacity["available_user_io"]) == (165, 106)
    assert (capacity["device"], capacity["package"]) == ("7a35t", "cpg236")
    assert capacity["message_id"] == "Place 30-415"


def test_without_place_30_415_the_same_log_is_still_a_design_failure():
    # The not-placed lines alone have other causes; only 30-415 makes them consequences.
    stripped = "\n".join(line for line in LOG.splitlines() if "Place 30-415" not in line)
    assert classify(stripped) == FailureKind.DESIGN
    assert target_capacity(stripped) is None
    assert classify("ERROR: [Place 30-68] Instance x_IBUF_inst (IBUF) is not placed") == FailureKind.DESIGN


@pytest.mark.parametrize("text", [
    "INFO: [Place 30-415] IO Placement failed due to overutilization. This design contains 165 I/O ports",
    "WARNING: [Synth 8-7129] Port ERROR: [Place 30-415] in module m is unconnected",
    "# puts {ERROR: [Place 30-415]}",
])
def test_only_a_real_error_line_decides(text):
    assert classify(text) != FailureKind.TARGET
    assert target_capacity(text) is None


def test_host_failure_still_outranks_target_capacity():
    host = "ERROR: [Common 17-345] A valid license was not found for feature 'Implementation'"
    assert classify(LOG + "\n" + host) == FailureKind.INFRA


def test_message_parts_it_does_not_state_are_never_guessed():
    capacity = target_capacity("ERROR: [Place 30-415] IO Placement failed due to overutilization. "
                               "This design contains 300 I/O ports")
    assert capacity["io_ports"] == 300
    assert capacity["available_user_io"] is None and capacity["package"] is None
    assert "300 I/O ports" in describe_target(capacity)


def test_synthesis_driver_returns_the_capacity_and_vivado_message(tmp_path, monkeypatch):
    monkeypatch.setattr(vivado, "_run", lambda *a: (1, LOG))
    source = tmp_path / "axil_regs.v"
    source.write_text("module axil_regs(input clk); endmodule")
    ok, error, kind = vivado.run_synthesis([source], "axil_regs", RunConfig(mode="optimize"), tmp_path)
    assert (ok, kind) == (False, FailureKind.TARGET)
    assert error.startswith("target_infeasible: the top has 165 I/O ports but device 7a35t "
                            "package cpg236 has 106 available user I/O")
    # The error text carries Vivado's own two-line message, so it parses back.
    assert target_capacity(error)["available_user_io"] == 106


def target_error():
    capacity = target_capacity(LOG)
    return describe_target(capacity) + "\n" + capacity["excerpt"]


def test_baseline_target_failure_never_reaches_the_fixer_or_retries(harness):  # noqa: F811
    o = harness
    o.cfg.max_infra_retries = 2
    design_before = o.cfg.design_path.read_bytes()
    fsm.vivado.xsim_run.side_effect = None
    fsm.vivado.xsim_run.return_value = (True, "", FailureKind.DESIGN)
    fsm.vivado.run_synthesis.side_effect = None
    fsm.vivado.run_synthesis.return_value = (False, target_error(), FailureKind.TARGET)
    result = o.run()
    assert result["status"] == "target_infeasible"
    assert result["failure_kind"] == "target"
    assert result["target_capacity"] == {"message_id": "Place 30-415", "io_ports": 165,
                                         "available_user_io": 106, "device": "7a35t",
                                         "package": "cpg236", "part": "xc7a35tcpg236-1"}
    assert_no_winner(o, result)
    o.generator.fix.assert_not_called()   # never a fix attempt
    o.doctor.surgery.assert_not_called()  # never the Timing Doctor
    assert fsm.vivado.run_synthesis.call_count == 1  # not retried like infrastructure
    assert o.cfg.design_path.read_bytes() == design_before
    events = [json.loads(line) for line in (o.state.run_dir / "events.jsonl").read_text().splitlines()]
    synthesis = [e for e in events if ":tool:run_synthesis:" in str(e.get("stage"))]
    assert [e["outcome"] for e in synthesis] == ["RUNNING", "COMPLETE"]  # committed, not INFRA_FAIL
    # A resume replays the committed outcome; the tool does not run again.
    again = fsm.Orchestrator(o.cfg, o.state.run_dir)
    assert again.run() == result
    assert fsm.vivado.run_synthesis.call_count == 1


def test_candidate_target_failure_stops_the_run_and_keeps_the_verified_incumbent(tmp_path, monkeypatch):
    from tests.test_fsm_resume import configuration, install_models, install_tools
    o = fsm.Orchestrator(configuration(tmp_path), tmp_path / "run")
    install_models(o)
    calls = install_tools(monkeypatch)
    real_synth = fsm.vivado.run_synthesis
    def synth(files, top, cfg, work, **kwargs):
        if "cand_" in str(work):
            calls.append(("synthesis", str(work)))
            return False, target_error(), FailureKind.TARGET
        return real_synth(files, top, cfg, work, **kwargs)
    monkeypatch.setattr(fsm.vivado, "run_synthesis", synth)
    monkeypatch.setattr(o.generator, "fix", lambda *a, **k: (_ for _ in ()).throw(AssertionError("fixer")))
    result = o.run()
    assert result["status"] == "target_infeasible" and result["failure_kind"] == "target"
    assert result["best_iteration"] == 0  # the verified baseline stays the incumbent; nothing promoted
    assert result["target_capacity"]["io_ports"] == 165
    assert [c for c in calls if c[0] == "synthesis" and "cand_" in c[1]] == [calls[-1]]  # once, no retry


def test_curriculum_counts_target_infeasible_as_a_failed_entry_configuration(curriculum):  # noqa: F811
    _, orch, output = curriculum
    entry_outcomes(orch, lambda name: {
        "status": "target_infeasible", "failure_kind": "target", "error": target_error(),
        "target_capacity": {"io_ports": 165, "available_user_io": 106, "part": "xc7a35tcpg236-1"}}
        if name == "b" else {"status": "done", "best_metrics": successful_metrics()})
    assert runner.run_tier(0, output_root=output) == 0  # not infrastructure: the campaign has a verdict
    record = records()[-1]
    assert "infra_blocked_entries" not in record
    failed = next(r for r in record["results"] if r["entry"] == "b")
    assert failed["ok"] is False
    assert failed["reason"] == ("target_infeasible: the entry configuration does not fit the target "
                                "(165 I/O ports, 106 available user I/O on xc7a35tcpg236-1); "
                                "not a model or infrastructure outcome")
