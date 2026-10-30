"""Triage on real Vivado output (triage_misreads_license_info_as_infra)."""
from pathlib import Path

from autortl.triage import FailureKind, classify

LOG = next(Path(__file__).resolve().parents[1].glob(
    "../autortl-work/evidence/2026-10-29/tier1-campaign-02/run/*/counter8_build/iter_000/vivado_synth_output.log"), None)
INFO_LICENSE = "INFO: [Common 17-349] Got license for feature 'Synthesis' and/or device 'xc7a35t'\n"


def test_a_routine_license_info_line_is_not_infrastructure():
    assert classify(INFO_LICENSE + "ERROR: [Synth 8-439] module 'sub' not found\n") == FailureKind.DESIGN
    assert classify(INFO_LICENSE + "something inexplicable happened") == FailureKind.UNKNOWN


def test_a_tool_design_error_beats_infrastructure_words_in_names():
    assert classify("ERROR: [VRFC 10-2063] Module <license_ctrl> not found while processing module instance <u>\n") \
        == FailureKind.DESIGN


def test_real_license_and_lock_failures_stay_infrastructure():
    assert classify(INFO_LICENSE + "ERROR: [Common 17-345] A valid license was not found for feature 'Synthesis'") \
        == FailureKind.INFRA
    assert classify("ERROR: [XSIM 43-3225] Cannot open file xsim.dir/work/x.pb: used by another process") \
        == FailureKind.INFRA
    assert classify(INFO_LICENSE + "\ntimed out after 900s") == FailureKind.INFRA
