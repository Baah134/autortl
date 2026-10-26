"""Mechanical wrapper timescale; no simulator or model invocation."""
import copy

from autortl.linter import top_verilog, lint_spec
from autortl.spec import DesignSpec, ModuleSpec, Port, Connection
from autortl.verilog_interface import infer_module


def spec(children):
    ports = [Port('clk', 'input', 1), Port('rst', 'input', 1),
             Port('data', 'input', 8), Port('result', 'output', 8)]
    modules = [ModuleSpec('child' + str(i), 'registered pass through',
                         copy.deepcopy(ports), latency=1) for i in range(children)]
    connections = [Connection(modules[i].name, 'result', modules[i+1].name, 'data')
                   for i in range(children-1)]
    return DesignSpec('top', modules, connections=connections, external_ports=copy.deepcopy(ports))


def test_transparent_known_latency_after_single_timescale():
    design = spec(1)
    assert lint_spec(design) == []
    text = top_verilog(design)
    assert text.startswith('`timescale 1ns/1ps\n// @latency 1\n')
    assert text.count('`timescale') == 1
    parsed = infer_module(text, 'top')
    assert parsed.latency_known and parsed.latency == 1
    assert 'child0 u_child0' in text
    assert text == top_verilog(design)


def test_three_children_keep_unknown_aggregate_latency_and_wiring():
    design = spec(3)
    text = top_verilog(design)
    assert text.startswith('`timescale 1ns/1ps\nmodule top')
    assert text.count('`timescale') == 1
    assert '@latency' not in text
    assert infer_module(text, 'top').latency_known is False
    assert '.data(w_child0_result)' in text
    assert '.data(w_child1_result)' in text
    assert all('child%d u_child%d' % (i, i) in text for i in range(3))


def test_generator_has_no_prefix_accumulation_or_spec_mutation():
    design = spec(1)
    original = copy.deepcopy(design)
    assert top_verilog(design) == top_verilog(design)
    assert design == original
    design.modules[0].latency_known = False
    text = top_verilog(design)
    assert text.startswith('`timescale 1ns/1ps\nmodule top')
    assert text.count('`timescale') == 1 and '@latency' not in text
