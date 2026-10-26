"""Signed FIR fixture structure and restricted oracle; no vendor/model calls."""
import hashlib
import importlib.util
import json
import re
from pathlib import Path

import pytest
import yaml
from autortl.golden import GoldenModel, qualify_against_examples, validate_examples
from autortl.linter import lint_spec, top_verilog
from autortl.spec import DesignSpec
from autortl.static_checks import check
from autortl.tbgen import expected_outputs
from autortl.verilog_interface import infer_module
from autortl.triage import FailureKind
from scripts.check_build_tbs import verdict

ROOT = Path(__file__).resolve().parents[1] / 'curriculum/tier3/signed_fir4_build'
FAULTS = '''current_coefficient history_coefficient swapped_taps unsigned_input
unsigned_history truncate12 history_on_invalid history_on_blocked history_delay
reverse_history_shift stale_history_reset async_history_reset early_output
late_output accept_full overwrite_stage1 overwrite_stage2 clear_stalled_valid
corrupt_held_output lose_full_replacement throughput_bubble retained_stage1_reset
retained_stage2_reset retained_stage3_reset async_valid_reset
incorrect_downstream_ready combinational_reset_gate'''.split()
ORACLE = '''def init():
    return [0, 0, 0]
def step(state, inputs):
    if inputs.get("rst", 0):
        return init(), {"out_data": 0}
    value = inputs["x"]
    if value >= 128:
        value = value - 256
    result = 3*value - 5*state[0] + 7*state[1] - 2*state[2]
    return [value, state[0], state[1]], {"out_data": result & 8191}
'''


def spec():
    return DesignSpec.load(ROOT / 'design_spec.json')


def cases():
    loader = importlib.util.spec_from_file_location('signed_fir_cases', ROOT/'qualification/cases.py')
    module = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(module)
    return module


@pytest.fixture
def oracle(tmp_path):
    path = tmp_path/'test_only_oracle.py'
    path.write_text(ORACLE, encoding='utf-8')
    model = GoldenModel(path)
    model.work_parent = tmp_path
    return model


def test_metadata_and_signed_contract():
    metadata = yaml.safe_load((ROOT/'meta.yaml').read_text(encoding='utf-8'))
    assert metadata['mode'] == 'build' and metadata['generate_golden'] is True
    assert metadata['top'] == 'signed_fir4' and 'design' not in metadata
    assert 'qualification' not in json.dumps(metadata)
    typed = spec()
    assert lint_spec(typed) == []
    assert DesignSpec.from_json(typed.to_json()).to_json() == typed.to_json()
    assert len(typed.modules) == 1
    module = typed.modules[0]
    assert module.name == 'signed_fir4_core' and module.parameters == {}
    assert module.latency == 3 and module.latency_known is True
    assert module.compare_mode == 'scoreboard' and module.reset.kind == 'sync'
    ports = {p.name:p for p in module.ports}
    assert (ports['x'].width, ports['x'].signed) == (8, True)
    assert (ports['out_data'].width, ports['out_data'].signed) == (13, True)
    top = infer_module(top_verilog(typed), 'signed_fir4')
    assert top.latency_known and top.latency == 3
    assert check(cases().case_sources()['reference'], module).passed


@pytest.mark.parametrize('samples,expected', [
    ([1,0,0,0,0], [3,-5,7,-2,0]),
    ([255,0,0,0,0], [-3,5,-7,2,0]),
    ([128,127,128,127,128], [-384,1021,-1915,2166,-2169]),
])
def test_actual_restricted_oracle_accepted_history(oracle, samples, expected):
    result = expected_outputs(spec().modules[0], oracle, [{'x':value} for value in samples])
    assert result == [{'out_data':value & 8191} for value in expected]


def test_explicit_reset_clears_history_and_run_reinitializes(oracle):
    rows = [{'rst':0,'x':1}, {'rst':0,'x':0}, {'rst':1,'x':127}, {'rst':0,'x':0}, {'rst':0,'x':1}]
    expected = [{'out_data':v & 8191} for v in [3,-5,0,0,3]]
    assert oracle.run(rows) == expected
    assert oracle.run(rows) == expected


def test_examples_are_independent_repeated_sample_anchors(oracle):
    module = spec().modules[0]
    assert validate_examples(module, require_anchors=True) == []
    assert qualify_against_examples(oracle, module) == []
    for example in module.examples:
        value = example.inputs['x']
        value = value-256 if value >= 128 else value
        n = example.after_cycles
        expected = 0 if example.inputs.get('rst',0) else value * [3,-2,5,3][min(n,4)-1]
        assert example.expected == {'out_data': expected & 8191}


def test_mutation_identity_and_materialized_inputs(tmp_path):
    helper = cases()
    variants = helper.case_sources()
    assert set(variants) == {'reference', *FAULTS}
    assert len(set(variants.values())) == 28
    module = spec().modules[0]
    expected_interface = infer_module(variants['reference'], module.name)
    for name, source in variants.items():
        parsed = infer_module(source, module.name)
        assert parsed.interface_signature == expected_interface.interface_signature
        assert parsed.latency_known and parsed.latency == 3
        replay = variants['reference']
        for old, new in helper.MUTATIONS.get(name, []):
            assert old != new and replay.count(old) == 1
            replay = replay.replace(old, new, 1)
        assert replay == source
    output = tmp_path/'prepared'
    manifest = helper.materialize_cases(output)
    assert len(manifest['cases']) == 28
    records = [f for case in manifest['cases'] for f in case['files']]
    assert len(records) == 84
    tb = (ROOT/'signed_fir4_tb.v').read_bytes()
    for record in records:
        path = Path(record['path'])
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256']
        if path.name.endswith('_tb.v'):
            assert path.read_bytes() == tb
    with pytest.raises(FileExistsError):
        helper.materialize_cases(output)


def test_actual_behavior_display_matches_existing_verdict():
    text = (ROOT/'signed_fir4_tb.v').read_text(encoding='utf-8')
    markers = re.findall(r'\$display\("(FAIL BEHAVIOR[^"\n]*)"', text)
    assert markers
    summaries = re.findall(r'\$display\("(TEST FAILED[^"\n]*)"', text)
    assert summaries
    # Exercise the actual errors>0 summary, not a fabricated compatible marker.
    raw = markers[0] + '\n' + summaries[0].replace('%0d', '1') + '\n'
    assert verdict(False, False, 'testbench reported failure', FailureKind.DESIGN, raw)['ok']


@pytest.mark.parametrize('raw', ['BEHAVIOR_FAIL bad\nTEST FAILED: assertion',
    'COVERAGE_FAIL missing\nTEST FAILED: assertions', 'CHECKER_FAIL queue\nTEST FAILED: assertions',
    'FAIL BEHAVIOR wrong\nTEST FAILED: watchdog', 'FAIL BEHAVIOR wrong\nTEST PASSED',
    'FAIL BEHAVIOR wrong'])
def test_nonbehavior_or_incomplete_logs_not_qualification(raw):
    assert not verdict(False, False, 'testbench reported failure', FailureKind.DESIGN, raw)['ok']
