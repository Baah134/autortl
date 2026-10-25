"""Static fixture and stimulus validation; these tests do not simulate RTL."""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
import yaml

from autortl.golden import GoldenModel, qualify_against_examples
from autortl.linter import lint_spec, stub_verilog, top_verilog
from autortl.spec import DesignSpec
from autortl.static_checks import check
from autortl.tbgen import gen_stimulus, generate_scoreboard_tb
from autortl.verilog_interface import infer_module

ROOT = Path(__file__).resolve().parents[1] / "curriculum/tier2/skid_buffer_build"


def spec():
    return DesignSpec.load(ROOT / "design_spec.json")


def qualification():
    loaded = importlib.util.spec_from_file_location("skid_buffer_qualification_cases", ROOT / "qualification/cases.py")
    module = importlib.util.module_from_spec(loaded)
    loaded.loader.exec_module(module)
    return module


def test_fixture_is_discoverable_build_with_independent_top_testbench():
    meta = yaml.safe_load((ROOT / "meta.yaml").read_text())
    assert meta["mode"] == "build" and meta["top"] == "skid_buffer"
    assert "design" not in meta
    assert (ROOT / meta["spec"]).is_file() and (ROOT / meta["tb"]).is_file()
    assert "qualification" not in meta["spec"] and "qualification" not in meta["tb"]
    typed = spec()
    assert lint_spec(typed) == []
    module = typed.modules[0]
    assert module.latency == 1 and module.latency_known is True
    assert module.compare_mode == "scoreboard" and module.reset.kind == "sync"
    assert module.parameters == {}
    assert "combinational ready path" in module.behavior
    assert "oracle ONLY" in module.behavior
    assert DesignSpec.from_json(typed.to_json()).to_json() == typed.to_json()


def test_generated_stub_and_mechanical_wrapper_match_typed_interfaces():
    typed = spec()
    assert check(stub_verilog(typed.modules[0]), typed.modules[0]).passed
    wrapper = top_verilog(typed)
    assert "skid_buffer_core u_skid_buffer_core" in wrapper
    top = infer_module(wrapper, "skid_buffer")
    assert [(p.name, p.direction, p.width, p.signed) for p in top.ports] == [
        (p.name, p.direction, p.width, p.signed) for p in typed.external_ports]


def test_payload_oracle_and_generated_scoreboard_use_transaction_not_queue_time(tmp_path):
    module = spec().modules[0]
    path = tmp_path / "payload_oracle.py"
    path.write_text("def init():\n    return {}\ndef step(state, inputs):\n    return state, {'out_data': inputs['in_data']}\n")
    oracle = GoldenModel(path)
    assert qualify_against_examples(oracle, module) == []
    stimulus = gen_stimulus(module, n_random=5)
    assert all(set(row) == {"in_data"} for row in stimulus)
    expected = oracle.run(stimulus)
    assert expected == [{"out_data": row["in_data"]} for row in stimulus]
    text = generate_scoreboard_tb(module, stimulus, expected)
    assert "BEFORE NBA" in text and "backpressure" in text
    assert "unstable out_data" in text and "TEST PASSED" in text


def test_independent_tb_has_no_hierarchical_dut_or_shared_reference_access():
    text = (ROOT / "skid_buffer_tb.v").read_text()
    assert "dut." not in text
    assert "storage[" not in text and "read_pointer" not in text
    for requirement in ("expected0", "expected1", "queued<2", "check_outputs", "#1;",
                        "BEFORE DUT nonblocking", "for(i=0;i<256", "for(i=0;i<600",
                        "reset_occupied", "discarded", "simultaneous", "last_push",
                        "TEST PASSED", "TEST FAILED: watchdog", "required scenario coverage"):
        assert requirement in text
    assert text.count("step(0,1,8'h30,0)") == 1  # repeated held third word
    assert "repeat(6) step(0,1,8'h30,0)" in text


@pytest.mark.parametrize("name", ["reference", "capacity_one", "overrun_ready", "payload_corruption",
                                  "unstable_stall", "drop_valid_stall", "async_reset", "simultaneous_pop_lost", "combinational_passthrough"])
def test_reference_and_mutants_preserve_static_public_interface(name):
    sources = qualification().case_sources()
    module = spec().modules[0]
    assert check(sources[name], module).passed
    assert "// @latency 1" in sources[name]
    if name != "reference":
        assert sources[name] != sources["reference"]


def test_prepared_qualification_cases_hash_exact_sources_and_same_tb(tmp_path):
    manifest = qualification().materialize_cases(tmp_path / "cases")
    assert manifest["status"] == "prepared_not_simulated"
    assert len(manifest["cases"]) == 9
    tb_hashes = set()
    for case in manifest["cases"]:
        for item in case["files"]:
            path = Path(item["path"])
            assert item["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
            if path.name == "skid_buffer_tb.v":
                tb_hashes.add(item["sha256"])
        if case["name"] == "reference":
            assert case["expected_verdict"] == "TEST PASSED"
        else:
            assert case["expected_verdict"] == "TEST FAILED"
            assert case["required_failure_kind"] == "behavioral_assertion"
    assert tb_hashes == {hashlib.sha256((ROOT / "skid_buffer_tb.v").read_bytes()).hexdigest()}
    with pytest.raises(FileExistsError):
        qualification().materialize_cases(tmp_path / "cases")


def test_directed_and_seeded_stimulus_can_reach_required_queue_coverage():
    # Exercise the SPEC with a Python list, not the RTL or the TB implementation.
    queue, counters = [], dict(accepted=0, retired=0, discarded=0, checked=0,
                              full=0, stalled=0, simultaneous=0, bubbles=0, empty=0, reset_occupied=0)
    last_push = False
    def step(reset, valid, data, ready):
        nonlocal last_push
        before = len(queue)
        push = bool(valid and (before < 2 or ready))
        pop = bool(before and ready)
        last_push = False
        counters["checked"] += 1
        if reset:
            counters["reset_occupied"] += bool(queue)
            counters["discarded"] += len(queue)
            queue.clear()
        else:
            counters["full"] += before == 2
            counters["stalled"] += before > 0 and not ready
            counters["simultaneous"] += push and pop
            counters["bubbles"] += not valid
            counters["empty"] += before == 0
            if pop:
                queue.pop(0)
                counters["retired"] += 1
            if push:
                queue.append(data)
                counters["accepted"] += 1
                last_push = True
        assert len(queue) <= 2
    step(1,0,0,0); step(1,0,0,0)
    step(0,1,0x10,0); step(0,1,0x20,0)
    for _ in range(6): step(0,1,0x30,0)
    step(0,1,0x30,1); step(0,1,0x40,1)
    step(0,0,0,0); step(0,0,0,1); step(0,0,0,1)
    for _ in range(4): step(0,0,0,1)
    for data in range(256): step(0,1,data,1)
    for _ in range(4): step(0,0,0,1)
    step(0,1,0x91,0); step(0,1,0x92,0)
    step(1,1,0x93,0); step(0,1,0x93,0)
    for _ in range(4): step(0,0,0,1)
    pending, data, seed = False, 0, 0x793ac4e1
    for i in range(600):
        seed ^= (seed << 13) & 0xffffffff
        seed ^= seed >> 17
        seed ^= (seed << 5) & 0xffffffff
        if not pending or last_push:
            pending = bool(seed & 1 or seed & 8)
            data = (seed >> 8) & 255
        step(i in (173,421),pending,data,bool(seed & 4 or seed & 128))
    if pending and not last_push: step(0,1,data,1)
    for _ in range(6): step(0,0,0,1)
    assert not queue and counters["accepted"] == counters["retired"] + counters["discarded"]
    assert counters["checked"] >= 850 and counters["accepted"] >= 300 and counters["retired"] >= 300
    assert counters["full"] >= 4 and counters["stalled"] >= 4 and counters["simultaneous"] >= 200
    assert counters["bubbles"] >= 2 and counters["empty"] >= 4 and counters["reset_occupied"] >= 1


def test_latency_annotation_is_not_proof_against_passthrough_mutant():
    mutant = qualification().case_sources()["combinational_passthrough"]
    inferred = infer_module(mutant, "skid_buffer_core")
    assert inferred.latency_known is True and inferred.latency == 1
    assert check(mutant, spec().modules[0]).passed
    assert "always" not in mutant
    assert "assign out_valid = in_valid && !rst" in mutant
    # The independently checked empty-queue output is zero BEFORE capture.
    # A static tag match deliberately does not count as a simulated mutant kill.
    tb = (ROOT / "skid_buffer_tb.v").read_text()
    assert "out_valid !== (queued!=0)" in tb
    assert tb.index("if(model_started) check_outputs;") < tb.index("@(posedge clk);")
