"""Fixture/schema/oracle/preparation validation only; never simulate vendor RTL."""
import hashlib
import importlib.util
import json
import re
from pathlib import Path

import pytest
import yaml

from autortl.golden import GoldenModel, qualify_against_examples, validate_examples
from autortl.linter import lint_spec, stub_verilog, top_verilog
from autortl.spec import DesignSpec
from autortl.static_checks import check
from autortl.tbgen import gen_stimulus, expected_outputs, generate
from autortl.verilog_interface import infer_module

ROOT = Path(__file__).resolve().parents[1] / "curriculum/tier2/sync_fifo_build"
MATRIX = [(8,3),(1,1),(8,2),(8,4),(13,5),(16,8)]


def spec():
    return DesignSpec.load(ROOT / "design_spec.json")


def qualification():
    loaded = importlib.util.spec_from_file_location("sync_fifo_qualification_cases", ROOT / "qualification/cases.py")
    module = importlib.util.module_from_spec(loaded)
    loaded.loader.exec_module(module)
    return module


def test_build_fixture_uses_combined_independent_mode_without_reference_seed():
    meta = yaml.safe_load((ROOT / "meta.yaml").read_text())
    assert meta["mode"] == "build" and meta["generate_golden"] is True
    assert meta["top"] == "sync_fifo" and "design" not in meta
    assert meta["spec"] == "design_spec.json" and meta["tb"] == "sync_fifo_tb.v"
    assert "qualification" not in json.dumps(meta)
    assert lint_spec(spec()) == []
    assert DesignSpec.from_json(spec().to_json()).to_json() == spec().to_json()


def test_public_symbolic_shape_defaults_and_mechanical_bindings_are_exact():
    typed = spec()
    module = typed.modules[0]
    assert list(module.parameters.items()) == [("WIDTH",8),("DEPTH",3)]
    assert module.latency_known is True and module.latency == 1
    assert module.compare_mode == "scoreboard" and module.reset.kind == "sync"
    assert all(type(p.width) is int for p in module.ports)
    symbols = {p["name"]:p["dimensions"] for p in module.interface_signature["ports"]}
    assert symbols["in_data"] == symbols["out_data"] == [["WIDTH - 1","0"]]
    stub = stub_verilog(module)
    assert "[WIDTH - 1:0]" in stub and check(stub,module).passed
    wrapper = top_verilog(typed)
    assert ".WIDTH(8)" in wrapper and ".DEPTH(3)" in wrapper
    top = infer_module(wrapper,"sync_fifo")
    assert top.parameters == {}
    assert {p.name:p.width for p in top.ports}["in_data"] == 8
    reference = qualification().case_sources()["reference"]
    assert infer_module(reference,"sync_fifo_core").interface_signature == module.interface_signature
    assert not check(reference.replace("input [WIDTH-1:0] in_data", "input [7:0] in_data"),module).passed


def test_actual_payload_oracle_and_generated_scoreboard_support_parameterized_module(tmp_path):
    module = spec().modules[0]
    assert validate_examples(module,require_anchors=True) == []
    path = tmp_path / "identity.py"
    path.write_text("def init():\n    return {}\ndef step(state, inputs):\n    if inputs.get('rst',0):\n        return {}, {'out_data':0}\n    return state, {'out_data':inputs['in_data'] & 255}\n")
    oracle = GoldenModel(path)
    assert qualify_against_examples(oracle,module) == []
    rows = gen_stimulus(module,n_random=7)
    assert all(set(row)=={"in_data"} for row in rows)
    assert expected_outputs(module,oracle,rows) == [{"out_data":row["in_data"]} for row in rows]
    tb = generate(module,oracle,tmp_path / "generated",n_random=7)
    text = tb.read_text()
    assert ".WIDTH(8)" in text and ".DEPTH(3)" in text
    assert "output before minimum transfer latency" in text
    assert "unstable out_data" in text and "TEST PASSED" in text


def test_matrix_cases_are_explicit_and_only_top_owns_final_verdict():
    tb = (ROOT / "sync_fifo_tb.v").read_text()
    configured = [(int(w),int(d)) for w,d in re.findall(r"sync_fifo_case #\(\.WIDTH\((\d+)\),\.DEPTH\((\d+)\)",tb)]
    assert configured == MATRIX == qualification().MATRIX
    assert ".USE_TOP(1),.CASE_ID(0)" in tb
    assert "wire [5:0] finished, failed" in tb and "wait(&finished)" in tb
    assert tb.count('$display("TEST PASSED")') == 1
    checker, enclosing = tb.split("module sync_fifo_tb;",1)
    assert "TEST PASSED" not in checker and "TEST FAILED" not in checker
    assert "COVERAGE case=%0d WIDTH=%0d DEPTH=%0d" in checker
    assert "failed===6'b000000" in enclosing and "watchdog" in enclosing
    assert "dut." not in tb
    assert "expected_queue[shift_index]=expected_queue[shift_index+1]" in tb
    for marker in ("queued<DEPTH", "before capture", "before DUT NBA", "last_push", "resets_occupied",
                   "max_queued!=DEPTH", "accepted!=retired+discarded", "(1 << (WIDTH-1))|1"):
        assert marker in tb


@pytest.mark.parametrize("name", ["reference","hardcoded_depth_three","hardcoded_memory_width_eight",
    "power_of_two_wrap","early_full","late_full","full_simultaneous_blocked","simultaneous_occupancy_lost",
    "simultaneous_retirement_lost","output_truncated_eight","unstable_stalled_payload","incorrect_data_order",
    "asynchronous_reset","combinational_bypass"])
def test_qualification_variants_keep_public_contract_and_are_distinct(name):
    sources = qualification().case_sources()
    assert len(sources) == len(set(sources.values())) == 14
    assert check(sources[name],spec().modules[0]).passed
    assert "// @latency 1" in sources[name]
    if name != "reference":
        assert sources[name] != sources["reference"]


def test_mutation_targets_are_unique_and_cover_parameter_specific_faults():
    helper = qualification()
    reference = helper.case_sources()["reference"]
    assert len(helper.MUTATIONS)>=10
    for targets in helper.MUTATIONS.values():
        assert targets
        for old,new in targets:
            assert old != new and reference.count(old)==1
    assert "reg [7:0] memory" in helper.case_sources()["hardcoded_memory_width_eight"]
    assert "& 8'hff" in helper.case_sources()["output_truncated_eight"]
    assert "(1 << $clog2(DEPTH))-1" in helper.case_sources()["power_of_two_wrap"]
    bypass = helper.case_sources()["combinational_bypass"]
    assert "always" not in bypass
    assert infer_module(bypass,"sync_fifo_core").latency == 1  # annotation is not behavioral proof


def test_materializer_exports_runner_contract_and_exact_matrix_input_hashes(tmp_path):
    result = qualification().materialize_cases(tmp_path / "cases")
    assert result["status"] == "prepared_not_simulated" and result["top"] == "sync_fifo_tb"
    assert [(row["width"],row["depth"]) for row in result["matrix"]] == MATRIX
    assert result["domain"] == dict(width_min=1,width_max=16,depth_min=1,depth_max=8)
    assert len(result["cases"]) == 14
    expected_tb = hashlib.sha256((ROOT / "sync_fifo_tb.v").read_bytes()).hexdigest()
    for case in result["cases"]:
        files = {Path(item["path"]).name:item for item in case["files"]}
        assert set(files)=={"sync_fifo_core.v","sync_fifo.v","sync_fifo_tb.v"}
        for item in files.values():
            assert hashlib.sha256(Path(item["path"]).read_bytes()).hexdigest()==item["sha256"]
        assert files["sync_fifo_tb.v"]["sha256"]==expected_tb
        assert case["expected_verdict"] == ("TEST PASSED" if case["name"]=="reference" else "TEST FAILED")
        assert case["required_failure_kind"] == (None if case["name"]=="reference" else "behavioral_assertion")
    with pytest.raises(FileExistsError):
        qualification().materialize_cases(tmp_path / "cases")


@pytest.mark.parametrize("width,depth,case_id", [(w,d,i) for i,(w,d) in enumerate(MATRIX)])
def test_independent_spec_schedule_reaches_each_matrix_coverage_requirement(width,depth,case_id):
    # Python list validates stimulus reachability; this does NOT execute the RTL.
    queue=[]
    c=dict(checked=0,accepted=0,retired=0,discarded=0,full=0,stalled=0,simultaneous=0,empty=0,bubbles=0,resets=0,max_queued=0)
    last_push=False
    mask=(1<<width)-1
    def step(reset,valid,data,ready):
        nonlocal last_push
        count=len(queue)
        push=bool(valid and (count<depth or ready));pop=bool(count and ready)
        last_push=False;c["checked"]+=1
        if reset:
            c["resets"]+=bool(queue);c["discarded"]+=count;queue.clear()
        else:
            c["full"]+=count==depth;c["stalled"]+=bool(count and not ready)
            c["simultaneous"]+=push and pop;c["empty"]+=count==0;c["bubbles"]+=not valid
            if pop:queue.pop(0);c["retired"]+=1
            if push:queue.append(data&mask);c["accepted"]+=1;last_push=True
        c["max_queued"]=max(c["max_queued"],len(queue))
        assert len(queue)<=depth
    def payload(i):return (i*137+case_id*53+0x1a35)&mask
    step(1,0,0,0);step(1,0,0,0)
    for i in range(depth):step(0,1,payload(i),0)
    for _ in range(6):step(0,1,mask,0)
    step(0,1,mask,1)
    for i in range(4*depth+8):step(0,1,payload(i+32),1)
    for _ in range(depth+3):step(0,0,0,1)
    step(0,1,(1<<(width-1))|1,1);step(0,1,mask,1)
    for i in range(256):step(0,1,payload(i),1)
    for _ in range(depth+3):step(0,0,0,1)
    for i in range(depth):step(0,1,payload(i+100),0)
    step(1,1,mask,0);step(0,1,mask,0)
    for _ in range(depth+3):step(0,0,0,1)
    pending=False;data=0;seed=0x9e3779b9^case_id
    for i in range(400):
        seed^=(seed<<13)&0xffffffff;seed^=seed>>17;seed^=(seed<<5)&0xffffffff
        if not pending or last_push:pending=bool(seed&1 or seed&8);data=seed&mask
        step(i in(131,317),pending,data,bool(seed&4 or seed&128))
    if pending and not last_push:step(0,1,data,1)
    for _ in range(depth+5):step(0,0,0,1)
    assert not queue and c["accepted"]==c["retired"]+c["discarded"]
    assert c["checked"]>=650 and c["accepted"]>=300 and c["retired"]>=290
    assert c["max_queued"]==depth and c["full"]>=6 and c["stalled"]>=6
    assert c["simultaneous"]>=200 and c["empty"]>=4 and c["bubbles"]>=2 and c["resets"]>=1
