"""Inspect actual assembled role calls, not just individual template fragments."""
from unittest.mock import Mock
import pytest
from autortl import roles
from autortl.config import RunConfig
from autortl.report_parser import VivadoMetrics
from autortl.skill_loader import inject, load_skill
from autortl.spec import ModuleSpec, Port

CALLS = ['make_spec', 'propose_contract', 'refine_contract', 'plan', 'restart_plan',
         'generate', 'fix', 'golden_model', 'review_contract', 'evaluate', 'surgery']

@pytest.mark.parametrize('method', CALLS)
def test_every_role_receives_contract_conventions(monkeypatch, method):
    call = Mock(return_value='```verilog\nmodule m; endmodule\n```')
    monkeypatch.setattr(roles, 'ask', call)
    cfg = RunConfig(mode='optimize', top_module='m')
    m = ModuleSpec(name='m', behavior='counter', ports=[Port('clk','input',1),Port('y','output',1)])
    metric = VivadoMetrics(sim_passed=True)
    p,g,e,d = roles.Planner(),roles.Generator(),roles.Evaluator(),roles.TimingDoctor()
    calls = {
      'make_spec': lambda:p.make_spec('counter',cfg,None),
      'propose_contract':lambda:p.propose_contract('optimize',cfg,metric,'source',None),
      'refine_contract':lambda:p.refine_contract('contract','feedback',None),
      'plan':lambda:p.plan(1,'contract','progress',[],metric,[],None),
      'restart_plan':lambda:p.restart_plan('contract',3,'tried',metric,None),
      'generate':lambda:g.generate(m,'source','instruction','mutation',None),
      'fix':lambda:g.fix('source','diagnosis','error','tb',[],None),
      'golden_model':lambda:g.golden_model(m,None),
      'review_contract':lambda:e.review_contract('contract',None),
      'evaluate':lambda:e.evaluate(1,'contract','ladder',metric,'',0,3,None),
      'surgery':lambda:d.surgery('source','instruction','path',None),
    }
    calls[method]()
    system = call.call_args.kwargs['system']
    assert system.count('# AutoRTL Conventions') == 1
    assert 'contract' in system.lower()
    if method == 'plan':
        assert 'Reference: fpga-methodology' in call.call_args.args[1]
    if method == 'surgery':
        prompt = call.call_args.args[1]
        assert 'hold' in prompt.lower()
        assert 'insert a register mid-path' not in prompt


def test_injection_budget_includes_reference_headers():
    body = load_skill('verilog-idioms')
    heading = '### Reference: verilog-idioms\n'
    assert inject(['verilog-idioms'],limit_chars=len(body)) == ''
    assert inject(['verilog-idioms'],limit_chars=len(body)+len(heading)) == heading+body
    for size in (0,1,50,1000,12000):
        assert len(inject(['verilog-idioms','cdc','timing-closure'],size)) <= size


def test_actual_conventions_distinguish_unknown_latency():
    from autortl.skill_loader import conventions
    guidance = conventions()
    assert "known numeric latency" in guidance
    assert "Unknown does not mean zero or combinational" in guidance
    assert "module contracts require an explicit numeric latency" in guidance
    assert "declared_latency.known=true" in guidance
    assert "unannotated aggregate top" in guidance
    assert "minimum accepted" in guidance
    assert "Every generated module declares" not in guidance
