"""Pure proposal evidence snapshots and bounded advisory rendering."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from autortl.bestofn import Candidate, dedupe
from autortl.cache import code_hash
from autortl.proposal_feedback import doctor_summary, record_candidate, render_feedback, source_identity

SOURCE = "module top; wire data; endmodule\n"
OTHER = "module top; wire alternate; endmodule\n"


def candidate(**overrides):
    result = Candidate(SOURCE, "standard", ladder_rungs_passed=5,
                       metrics={"sim_passed": True, "timing_met": True, "lut_used": 23,
                                "ff_used": 31, "wns_ns": 0.078, "whs_ns": 0.106})
    for key, value in overrides.items():
        setattr(result, key, value)
    return result


def record(iteration=1, *, count=1, doctor=None, is_best=False):
    c = candidate()
    return {"iteration": iteration, "instruction": "change the critical arithmetic path",
            "candidates": [record_candidate(c, SOURCE, "proposal", iteration) for _ in range(count)],
            "doctor": doctor, "recommendation": "ACCEPT" if is_best else "REJECT",
            "is_best": is_best, "selected_source_sha256": source_identity(OTHER if doctor else SOURCE)}


def payload(rendered):
    return json.loads(rendered.split("\n", 2)[2])


def test_raw_source_identity_is_full_utf8_sha_and_not_normalized_code_hash():
    unicode_source = SOURCE + "// café\n"
    assert source_identity(unicode_source) == hashlib.sha256(unicode_source.encode("utf-8")).hexdigest()
    assert len(source_identity(SOURCE)) == 64
    assert source_identity(SOURCE) != source_identity(SOURCE.replace("\n", "\r\n"))
    assert source_identity(SOURCE) != source_identity(unicode_source)
    assert code_hash(SOURCE) == code_hash(unicode_source)
    with pytest.raises(TypeError):
        source_identity(None)


def test_snapshot_is_deterministic_and_does_not_mutate_candidate_or_share_metrics():
    c = candidate()
    before = copy.deepcopy(c.__dict__)
    snapshot = record_candidate(c, OTHER, "instruction", 2, cache_hit=True)
    assert c.__dict__ == before
    assert snapshot == record_candidate(c, OTHER, "instruction", 2, cache_hit=True)
    assert snapshot["generated_source_sha256"] == source_identity(OTHER)
    assert snapshot["final_source_sha256"] == source_identity(SOURCE)
    assert snapshot["generated_code_hash"] == code_hash(OTHER)
    assert snapshot["final_code_hash"] == code_hash(SOURCE)
    assert snapshot["cache_hit"] is True
    assert snapshot["status"] == "measured" and snapshot["metrics"]["lut_used"] == 23
    c.metrics["lut_used"] = 999
    c.verilog = OTHER
    assert snapshot["metrics"]["lut_used"] == 23
    assert snapshot["final_source_sha256"] == source_identity(SOURCE)


@pytest.mark.parametrize("alive,rungs,reason,expected", [
    (False, 1, "syntax error", "design_rejected"),
    (False, 4, "synthesis assertion", "design_rejected"),
    (True, 3, "infra: license unavailable", "infra_blocked"),
    (False, 4, "infra: timed out", "infra_blocked"),
    (True, 0, "", "infra_blocked"),
    (True, 5, "", "measured"),
])
def test_infra_is_not_classified_as_design_failure_or_standard_measurement(alive, rungs, reason, expected):
    c = candidate(alive=alive, ladder_rungs_passed=rungs, fail_reason=reason)
    result = record_candidate(c, SOURCE, "proposal", 1)
    assert result["status"] == expected
    assert bool(result["metrics"]) is (expected == "measured")


def test_unmeasured_alive_candidate_with_no_metrics_is_infra_blocked():
    result = record_candidate(candidate(metrics={}), SOURCE, "proposal", 1)
    assert result["status"] == "infra_blocked" and result["metrics"] == {}


def test_metrics_whitelist_excludes_bulk_nonfinite_and_boolean_numbers():
    metrics = {"lut_used": True, "wns_ns": float("nan"), "whs_ns": float("inf"),
               "ff_used": 2, "sim_passed": 1, "timing_met": True, "raw_report": "unbounded",
               "total_power_w": 10**1000}
    result = record_candidate(candidate(metrics=metrics), SOURCE, "i" * 10000, 1)
    assert result["metrics"] == {"ff_used": 2, "timing_met": True}
    assert len(result["instruction"]) == 600
    json.dumps(result, allow_nan=False)


def test_raw_artifact_identities_match_unique_source_and_synth_bytes(tmp_path):
    c = candidate()
    c.artifact_dir = tmp_path
    source = tmp_path / "top.v"
    source.write_bytes(SOURCE.replace("\n", "\r\n").encode("utf-8"))
    (tmp_path / "companion.v").write_text(OTHER, encoding="utf-8")
    script = tmp_path / "synth.tcl"
    script.write_bytes(b"synth_design -top top\r\n")
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    result = record_candidate(c, SOURCE, "instruction", 1)
    assert result["source"]["path"] == str(source.resolve())
    assert result["source"]["sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert result["source"]["sha256"] != result["final_source_sha256"]
    assert result["flow_script"]["sha256"] == hashlib.sha256(script.read_bytes()).hexdigest()
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == before


@pytest.mark.parametrize("mode", ["missing", "unrelated", "ambiguous"])
def test_missing_or_ambiguous_source_never_invents_an_artifact_identity(tmp_path, mode):
    c = candidate()
    c.artifact_dir = tmp_path / "missing" if mode == "missing" else tmp_path
    if mode == "unrelated":
        (tmp_path / "companion.v").write_text(OTHER, encoding="utf-8")
    if mode == "ambiguous":
        for name in ("first.v", "second.v"):
            (tmp_path / name).write_text(SOURCE, encoding="utf-8")
    result = record_candidate(c, SOURCE, "proposal", 1)
    assert "source" not in result and "flow_script" not in result


def test_doctor_projection_keeps_only_bounded_trial_facts_and_identities():
    identity = {"path": "trial/top.v", "sha256": source_identity(OTHER), "text": "PRIVATE_RTL" * 10000}
    feedback = {"status": "ADOPTED", "action": "tool_knobs", "reason": "r" * 10000,
                "tools_ran": True, "measured_metrics": {"lut_used": 26, "raw": "REPORT_BULK"},
                "input_source": identity, "trial_source": identity,
                "prior_flow_script": identity, "trial_flow_script": identity,
                "reports": [{"text": "REPORT_BULK" * 10000}],
                "first_violated_path_excerpt": {"text": "REPORT_BULK"},
                "proposed_source_text_sha256": source_identity(OTHER)}
    before = copy.deepcopy(feedback)
    result = doctor_summary(feedback)
    assert result["adopted"] is True and result["identity_count"] == 4
    assert result["measured_metrics"] == {"lut_used": 26}
    assert result["trial_source"] == {"path": str(Path("trial/top.v").resolve()), "sha256": source_identity(OTHER)}
    assert len(result["reason"]) == 600
    assert "PRIVATE_RTL" not in json.dumps(result) and "REPORT_BULK" not in json.dumps(result)
    assert feedback == before
    assert doctor_summary(result) == result
    assert doctor_summary(None) is None


def test_unknown_doctor_identities_are_not_counted_as_provenance():
    result = doctor_summary({"trial_source": {"path": "x", "sha256": "invalid", "text": SOURCE}})
    assert result["identity_count"] == 0 and "trial_source" not in result


def test_renderer_separates_standard_measurement_from_adopted_doctor_and_selected_source():
    feedback = {"status": "ADOPTED", "action": "tool_knobs", "tools_ran": True,
                "reason": "timing recovered", "measured_metrics": {"lut_used": 26, "wns_ns": 0.12}}
    records = [record(doctor=feedback, is_best=True)]
    before = copy.deepcopy(records)
    rendered = render_feedback(records, OTHER, 2)
    row = payload(rendered)["iterations"][0]
    assert row["standard_candidates"][0]["metrics"]["lut_used"] == 23
    assert row["doctor_trial"]["measured_metrics"]["lut_used"] == 26
    assert row["doctor_trial"]["adopted"] is True and row["is_best"] is True
    assert row["selected_equals_current_seed"] is True
    assert row["standard_candidates"][0]["final_equals_current_seed"] is False
    assert records == before
    assert "advisory" in rendered and "repetition is not prohibited" in rendered
    assert "Same RTL with different physical settings can be valid" in rendered


def test_renderer_retains_nonadopted_doctor_without_replacing_standard_metrics():
    feedback = {"status": "NOT_ADOPTED", "reason": "timing still fails", "tools_ran": True,
                "measured_metrics": {"lut_used": 99, "wns_ns": -0.1}}
    row = payload(render_feedback([record(doctor=feedback)], SOURCE, 2))["iterations"][0]
    assert row["doctor_trial"]["adopted"] is False
    assert row["standard_candidates"][0]["metrics"]["lut_used"] == 23


def test_renderer_exact_and_normalized_seed_equalities_are_distinct():
    generated = SOURCE + "// cosmetic\n"
    c = candidate()
    row = record()
    row["candidates"] = [record_candidate(c, generated, "i", 1)]
    observed = payload(render_feedback([row], SOURCE, 2))["iterations"][0]["standard_candidates"][0]
    assert observed["generated_equals_current_seed"] is False
    assert observed["generated_code_equals_current_seed"] is True
    assert observed["final_equals_current_seed"] is True
    assert observed["final_code_equals_current_seed"] is True


def test_renderer_excludes_current_future_and_noninteger_iterations():
    records = [record(i) for i in range(1, 10)] + [{"iteration": True}, {"iteration": "2"}]
    rows = payload(render_feedback(records, SOURCE, 7))["iterations"]
    assert [row["iteration"] for row in rows] == [4, 5, 6]
    assert render_feedback([record(7), record(8)], SOURCE, 7) == ""
    assert render_feedback([], SOURCE, 2) == ""
    with pytest.raises(ValueError):
        render_feedback(records, SOURCE, True)


def test_renderer_bounds_recent_candidate_count_and_large_input_deterministically():
    records = [record(i, count=50) for i in range(1, 100)]
    instruction, reason, rtl = "INSTRUCTION" * 10000, "REASON" * 10000, "DO_NOT_INCLUDE_RTL" * 10000
    for row in records:
        row["instruction"] = instruction
        for item in row["candidates"]:
            item["reason"] = reason
            item["verilog"] = rtl
    rendered = render_feedback(records, SOURCE, 100)
    assert rendered == render_feedback(records, SOURCE, 100)
    assert len(rendered) <= 16000
    rows = payload(rendered)["iterations"]
    assert [row["iteration"] for row in rows] == [97, 98, 99]
    assert sum(len(row["standard_candidates"]) for row in rows) <= 12
    assert "DO_NOT_INCLUDE_RTL" not in rendered


def test_renderer_reprojects_untrusted_extra_fields_and_invalid_metrics():
    row = record()
    row["candidates"][0].update(source={"path": "x", "sha256": "bad"},
                                  metrics={"wns_ns": float("nan"), "payload": "RTL"},
                                  full_source="SECRET")
    rendered = render_feedback([row], SOURCE, 2)
    assert "SECRET" not in rendered and "NaN" not in rendered
    observed = payload(rendered)["iterations"][0]["standard_candidates"][0]
    assert observed["metrics"] == {} and "source" not in observed


def test_bestofn_duplicate_is_skipped_without_a_design_failure_or_measurement():
    first, duplicate = candidate(), candidate(mutation="wildcard")
    assert dedupe([first, duplicate]) == [first]
    before = copy.deepcopy(duplicate.__dict__)
    result = record_candidate(duplicate, SOURCE, "try another layout", 1)
    assert result["status"] == "duplicate_skipped"
    assert result["reason"] == "duplicate of 'standard' candidate"
    assert result["metrics"] == {}
    assert duplicate.__dict__ == before


def test_long_file_identities_are_full_in_records_and_clipped_only_in_prompts(tmp_path, monkeypatch):
    # No dependence on OS long-path support; mock reads and canonical resolution.
    directory = tmp_path / ("nested_" * 90)
    assert len(str(directory)) > 320
    with monkeypatch.context() as patch:
        patch.setattr(Path, "resolve", lambda self: self)
        patch.setattr(Path, "is_file", lambda self: True)
        patch.setattr(Path, "read_bytes", lambda self: b"synth_design" if self.name == "synth.tcl" else SOURCE.encode("utf-8"))
        patch.setattr(Path, "read_text", lambda self, **kwargs: SOURCE)
        patch.setattr(Path, "glob", lambda self, pattern: iter([self / "top.v"]))
        c = candidate()
        c.artifact_dir = directory
        observed = record_candidate(c, SOURCE, "instruction", 1)
        assert observed["artifact_dir"] == str(directory)
        assert observed["source"]["path"] == str(directory / "top.v")
        assert observed["flow_script"]["path"] == str(directory / "synth.tcl")
        doctor = doctor_summary({"status": "NOT_ADOPTED", "trial_source": observed["source"],
                                 "trial_flow_script": observed["flow_script"]})
        assert doctor["trial_source"]["path"] == str(directory / "top.v")
        assert doctor["trial_flow_script"]["path"] == str(directory / "synth.tcl")
        row = record(doctor=doctor)
        row["candidates"] = [observed]
        original = copy.deepcopy(row)
        rendered = payload(render_feedback([row], SOURCE, 2))["iterations"][0]
        assert len(rendered["standard_candidates"][0]["artifact_dir"]) == 320
        assert len(rendered["standard_candidates"][0]["source"]["path"]) == 320
        assert len(rendered["standard_candidates"][0]["flow_script"]["path"]) == 320
        assert len(rendered["doctor_trial"]["trial_source"]["path"]) == 320
        assert len(rendered["doctor_trial"]["trial_flow_script"]["path"]) == 320
        assert row == original


def test_doctor_identity_requires_a_nonempty_path_as_well_as_hash():
    observed = doctor_summary({"trial_source": {"sha256": source_identity(SOURCE)},
                               "trial_flow_script": {"path": "", "sha256": source_identity(SOURCE)}})
    assert observed["identity_count"] == 0
    assert "trial_source" not in observed and "trial_flow_script" not in observed
