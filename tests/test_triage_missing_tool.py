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


XELAB_C_COMPILE = ("ERROR: [XSIM 43-3409] Failed to compile generated C file xsim.dir/fifo_tb_snap/obj/xsim_1.c.\n"
                   "ERROR: [XSIM 43-3915] Encountered a fatal error. Cannot continue. Exiting...\n")


def test_xelab_c_compile_failure_is_infrastructure():
    """xelab_c_compile_failure_classified_design: release-rehold tier 2 (MAX_PATH object path)."""
    assert classify(XELAB_C_COMPILE) == FailureKind.INFRA
    assert classify("INFO: [XSIM 43-3496] Using init file\n" + XELAB_C_COMPILE) == FailureKind.INFRA


def test_the_fatal_error_line_alone_and_real_elaboration_errors_stay_design():
    assert classify("ERROR: [XSIM 43-3915] Encountered a fatal error. Cannot continue. Exiting...\n") \
        == FailureKind.DESIGN
    assert classify("ERROR: [VRFC 10-2063] Module <sub> not found while processing module instance <u>\n"
                    "ERROR: [XSIM 43-3915] Encountered a fatal error. Cannot continue. Exiting...\n") \
        == FailureKind.DESIGN


def test_vivado_crash_banner_is_infrastructure():
    """vivado_crash_classified_design: real banner from an out-of-context DFF run (Vivado 2025.2)."""
    log = ('# catch { report_qor_suggestions -file "W/qor_suggestions.rpt" }\n'
           "Command: report_qor_suggestions -file W/qor_suggestions.rpt\n"
           "Abnormal program termination (EXCEPTION_ACCESS_VIOLATION)\n"
           "Please check 'W/hs_err_pid12696.log' for details\n")
    assert classify(log) == FailureKind.INFRA
