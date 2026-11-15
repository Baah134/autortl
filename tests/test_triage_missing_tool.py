import pytest

from autortl.triage import FailureKind, classify

NOT_FOUND = "{} not found: [WinError 2] The system cannot find the file specified"


@pytest.mark.parametrize("tool", ["xvlog", "xelab", "xsim", "vivado", "vivado.bat",
                                  "C:/Program Files/Xilinx/bin/xvlog.bat"])
def test_tool_not_found_is_infra(tool):
    assert classify(NOT_FOUND.format(tool)) == FailureKind.INFRA


def test_tool_launch_permission_error_is_infra():
    assert classify("xsim could not launch: [WinError 5] Access is denied") == FailureKind.INFRA


def test_genuine_xvlog_errors_stay_design():
    log = ('ERROR: [VRFC 10-2063] Module <license_ctrl> not found while processing module instance <u>\n'
           'ERROR: [VRFC 10-4982] syntax error near "endmodule" [top.v:3]\n')
    assert classify(log) == FailureKind.DESIGN
    assert classify("ERROR: [VRFC 10-2989] 'xvlog' is not declared [top.v:4]") == FailureKind.DESIGN


def test_vivado_crash_banner_is_infrastructure():
    """vivado_crash_classified_design: real banner from an out-of-context DFF run (Vivado 2025.2)."""
    log = ('# catch { report_qor_suggestions -file "W/qor_suggestions.rpt" }\n'
           "Command: report_qor_suggestions -file W/qor_suggestions.rpt\n"
           "Abnormal program termination (EXCEPTION_ACCESS_VIOLATION)\n"
           "Please check 'W/hs_err_pid12696.log' for details\n")
    assert classify(log) == FailureKind.INFRA
