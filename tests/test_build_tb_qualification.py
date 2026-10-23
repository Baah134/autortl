"""Qualification runner unit tests; no vendor processes are launched here."""
import hashlib
import importlib.util
import json
from pathlib import Path
from unittest.mock import Mock
import pytest
from autortl.triage import FailureKind
from autortl.verilog_interface import infer_module

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("build_tb_checks",ROOT/"scripts/check_build_tbs.py")
cli=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cli)


def test_controls_and_behavior_faults_are_unique_and_keep_top_interfaces():
    cases=cli.cases()
    assert len(cases)==10 and len({c["case"] for c in cases})==10
    for module in ("counter8","priority_encoder8"):
        group=[c for c in cases if c["module"]==module]
        assert len(group)==5 and sum(c["expected_pass"] for c in group)==1
        control=next(c for c in group if c["expected_pass"])
        ports=lambda source:[(p.name,p.direction,p.width) for p in infer_module(source,module).ports]
        for case in group:
            assert ports(case["source"])==ports(control["source"])
            assert case["top"]==module+"_tb"
            if not case["expected_pass"]:
                assert case["source"]!=control["source"]


@pytest.mark.parametrize("passed,error,kind,detected",[
    (False,"Testbench failures: FAIL count",FailureKind.DESIGN,True),
    (False,"testbench reported failure",FailureKind.DESIGN,True),
    (False,"xvlog compile error",FailureKind.DESIGN,False),
    (False,"timed out after 60s",FailureKind.INFRA,False),
    (False,"Testbench failures: watchdog",FailureKind.INFRA,False),
    (False,"missing simulation log",FailureKind.UNKNOWN,False),
    (True,"",FailureKind.DESIGN,False),
])
def test_only_actual_design_assertions_detect_mutants(passed,error,kind,detected):
    result=cli.verdict(False,passed,error,kind,"FAIL count mismatch\nTEST FAILED: 1 errors")
    assert result["ok"] is detected
    assert result["assertion_detected"] is detected


def test_positive_control_must_pass():
    assert cli.verdict(True,True,"",FailureKind.DESIGN,"TEST PASSED")["ok"]
    assert not cli.verdict(True,False,"testbench reported failure",FailureKind.DESIGN)["ok"]


def test_saved_cases_copy_exact_trusted_testbench_bytes_and_hashes(tmp_path):
    cases=cli.save_cases(tmp_path)
    assert json.loads((tmp_path/"cases.json").read_text())==cases
    for case in cases:
        work=tmp_path/case["case"]
        assert (work/"tb.v").read_bytes()==Path(case["trusted_tb_path"]).read_bytes()
        for name,field in (("tb.v","tb_sha256"),("dut.v","source_sha256")):
            assert hashlib.sha256((work/name).read_bytes()).hexdigest()==case[field]


def test_counter_stimulus_establishes_nonzero_reset_priority_and_wrap():
    count=0
    wrap=False
    hold=False
    for i in range(700):
        rst=i<3 or i==420
        enable=i==420 or i<310 or i%7!=0
        if i==420:
            assert count!=0 and enable
        if rst:
            count=0
        elif enable:
            wrap=wrap or count==255
            count=(count+1)&255
        else:
            hold=True
    assert wrap and hold
    tb=(ROOT/"curriculum/tier1/counter8_build/counter8_tb.v").read_text()
    assert "count changed before rising clock edge" in tb
    assert "reset-priority coverage requires nonzero count" in tb


@pytest.mark.parametrize("broken_case",[None,"counter-saturation","encoder-control"])
def test_runner_records_all_outcomes_without_counting_infrastructure(tmp_path,monkeypatch,broken_case):
    def simulate(files,tb,top,config,work,timeout):
        assert timeout==60
        (work/"xsim.log").write_text("controlled unit fixture")
        (work/"sim_log.txt").write_text("TEST PASSED" if work.name.endswith("control") else "FAIL output mismatch\nTEST FAILED: 1 errors")
        (work/"tool_exit_records.log").write_text("controlled unit fixture")
        if work.name==broken_case:
            return False,"tool launch failed",FailureKind.INFRA
        return (True,"",FailureKind.DESIGN) if work.name.endswith("control") else (False,"testbench reported failure",FailureKind.DESIGN)
    monkeypatch.setattr(cli,"xsim_run",Mock(side_effect=simulate))
    output=tmp_path/"checks"
    assert cli.main(["--bin-dir",str(tmp_path),"--output",str(output)])==(0 if broken_case is None else 1)
    rows=json.loads((output/"results.json").read_text())
    assert len(rows)==10
    assert sum(r["ok"] for r in rows)==(10 if broken_case is None else 9)
    manifest=json.loads((output/"archive-manifest.json").read_text())
    assert any(name.endswith("tool_exit_records.log") for name in manifest)
    for name,digest in manifest.items():
        assert hashlib.sha256((output/name).read_bytes()).hexdigest()==digest
    with pytest.raises(FileExistsError):
        cli.main(["--bin-dir",str(tmp_path),"--output",str(output)])


@pytest.mark.parametrize("raw",[None,"", "TEST FAILED: watchdog", "FAIL watchdog expired\nTEST FAILED", "TEST FAILED: 1 errors"])
def test_watchdog_and_missing_assertion_logs_are_not_fault_detection(raw):
    assert not cli.verdict(False,False,"testbench reported failure",FailureKind.DESIGN,raw)["ok"]


def test_control_cannot_pass_without_raw_standalone_verdict():
    assert not cli.verdict(True,True,"",FailureKind.DESIGN,None)["ok"]
    assert not cli.verdict(True,True,"",FailureKind.DESIGN,"prefix TEST PASSED suffix")["ok"]


@pytest.mark.parametrize("raw",["FAIL output mismatch", "FAIL output mismatch\nTEST FAILED: 1 errors\nTEST PASSED", "TEST PASSED\nFAIL output mismatch\nTEST FAILED"])
def test_detection_requires_failure_verdict_without_contradictory_pass(raw):
    assert not cli.verdict(False,False,"testbench reported failure",FailureKind.DESIGN,raw)["ok"]


def test_contradictory_control_is_not_success():
    assert not cli.verdict(True,True,"",FailureKind.DESIGN,"TEST PASSED\nTEST FAILED: 1 errors")["ok"]


def test_skid_suite_materializes_wrapper_child_and_independent_tb(tmp_path):
    cases=cli.save_skid_cases(tmp_path)
    assert len(cases)==9
    assert sum(c["expected_pass"] for c in cases)==1
    for case in cases:
        work=tmp_path/case["work_dir"]
        assert case["top"]=="skid_buffer_tb"
        assert case["design_files"]==["skid_buffer_core.v","skid_buffer.v"]
        assert case["testbench"]=="skid_buffer_tb.v"
        for source,digest in case["source_sha256"].items():
            assert hashlib.sha256((work/source).read_bytes()).hexdigest()==digest
        assert hashlib.sha256((work/case["testbench"]).read_bytes()).hexdigest()==case["tb_sha256"]


def test_skid_suite_runs_nine_serial_cases_with_complete_source_lists(tmp_path,monkeypatch):
    invocations=[]
    def simulate(files,tb,top,config,work,timeout):
        assert [p.name for p in files]==["skid_buffer_core.v","skid_buffer.v"]
        assert tb.name=="skid_buffer_tb.v" and top=="skid_buffer_tb" and timeout==60
        invocations.append(work.name)
        good=work.name=="reference"
        (work/"sim_log.txt").write_text("TEST PASSED" if good else "FAIL behavioral mismatch\nTEST FAILED: 1 errors")
        (work/"tool_exit_records.log").write_text("controlled unit fixture")
        return good,"" if good else "testbench reported failure",FailureKind.DESIGN
    monkeypatch.setattr(cli,"xsim_run",Mock(side_effect=simulate))
    output=tmp_path/"skid-run"
    assert cli.main(["--bin-dir",str(tmp_path),"--output",str(output),"--suite","skid"])==0
    rows=json.loads((output/"results.json").read_text())
    assert len(rows)==len(invocations)==9 and all(r["ok"] for r in rows)
    manifest=json.loads((output/"archive-manifest.json").read_text())
    assert "skid_cases/reference/skid_buffer.v" in manifest
    assert "skid_cases/reference/skid_buffer_core.v" in manifest
    assert "skid_cases/reference/tool_exit_records.log" in manifest



@pytest.mark.parametrize("suite,module", [("fifo","sync_fifo"), ("packet","packet_fifo")])
def test_fifo_materializer_adapter_preserves_wrapper_child_tb_and_plan(tmp_path,suite,module):
    def materialize(output):
        output.mkdir()
        rows=[]
        for name in ("reference","fault"):
            work=output/name
            work.mkdir()
            files=[]
            for filename in (module+"_core.v",module+".v",module+"_tb.v"):
                path=work/filename
                path.write_text("// controlled materializer unit fixture "+name+filename)
                files.append({"path":str(path.resolve()),"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
            rows.append({"name":name,"expected_verdict":"TEST PASSED" if name=="reference" else "TEST FAILED",
                         "required_failure_kind":None if name=="reference" else "behavioral_assertion","files":files})
        return {"cases":rows}
    cases=cli._save_materialized_cases(tmp_path,suite,module,materialize)
    assert len(cases)==2 and sum(row["expected_pass"] for row in cases)==1
    for row in cases:
        assert row["work_dir"]==suite+"_cases/"+row["case"]
        assert row["design_files"]==[module+"_core.v",module+".v"]
        assert row["testbench"]==module+"_tb.v" and row["top"]==module+"_tb"
        for filename,digest in row["source_sha256"].items():
            assert hashlib.sha256((tmp_path/row["work_dir"]/filename).read_bytes()).hexdigest()==digest


@pytest.mark.parametrize("suite,module,preparer", [("fifo","sync_fifo","save_fifo_cases"),
    ("packet","packet_fifo","save_packet_cases")])
@pytest.mark.parametrize("infrastructure_failure",[False,True])
def test_fifo_driver_dispatches_serially_and_never_counts_infrastructure(tmp_path,monkeypatch,infrastructure_failure,suite,module,preparer):
    def prepare(output):
        result=[]
        for name,expected in (("reference",True),("mutant",False)):
            work=output/(suite+"_cases")/name
            work.mkdir(parents=True)
            for filename in (module+"_core.v",module+".v",module+"_tb.v"):
                (work/filename).write_text("// controlled unit fixture")
            result.append({"case":name,"expected_pass":expected,"work_dir":suite+"_cases/"+name,
                           "design_files":[module+"_core.v",module+".v"],"testbench":module+"_tb.v","top":module+"_tb"})
        return result
    monkeypatch.setattr(cli,preparer,prepare)
    calls=[]
    def simulate(files,tb,top,config,work,timeout):
        calls.append(work.name)
        assert [p.name for p in files]==[module+"_core.v",module+".v"]
        assert tb.name==module+"_tb.v" and top==module+"_tb" and timeout==60
        (work/"sim_log.txt").write_text("TEST PASSED" if work.name=="reference" else "FAIL FIFO order\nTEST FAILED: 1 errors")
        if work.name=="reference":
            return True,"",FailureKind.DESIGN
        if infrastructure_failure:
            return False,"tool launch failed",FailureKind.INFRA
        return False,"testbench reported failure",FailureKind.DESIGN
    monkeypatch.setattr(cli,"xsim_run",Mock(side_effect=simulate))
    output=tmp_path/(suite+"-run")
    assert cli.main(["--suite",suite,"--bin-dir",str(tmp_path),"--output",str(output)])==int(infrastructure_failure)
    assert calls==["reference","mutant"]
    rows=json.loads((output/"results.json").read_text())
    assert rows[1]["assertion_detected"] is (not infrastructure_failure)
