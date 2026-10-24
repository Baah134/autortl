"""Bounded mutation portfolios retain misses and never retry infrastructure as design."""
import hashlib
import json
from pathlib import Path
import pytest
from autortl import tbqual
from autortl.config import RunConfig
from autortl.triage import FailureKind
from autortl.verilog_interface import infer_module

SOURCE="module m(input [7:0] a,output [7:0] y); assign y=a+1'b1; endmodule"
FAIL="FAIL output expected=7 actual=0\nTEST FAILED: 1 errors\n"


def install_simulation(monkeypatch,outcomes):
    calls=[]
    def simulate(files,tb,top,cfg,work):
        calls.append(work.name)
        passed,error,kind,raw=outcomes[work.name]
        if raw is not None: (work/"sim_log.txt").write_text(raw)
        return passed,error,kind
    monkeypatch.setattr(tbqual,"xsim_run",simulate)
    return calls


def run_portfolio(tmp_path,source=SOURCE):
    tb=tmp_path/"tb.v"; tb.write_text("// unchanged independent testbench")
    result=tbqual.qualify(source,tb,"m",RunConfig(mode="build"),tmp_path)
    report=json.loads((tmp_path/"tbqual/qualification.json").read_text())
    return result,report


PASS=(True,"",FailureKind.DESIGN,"TEST PASSED\n")
DETECTED=(False,"testbench reported failure",FailureKind.DESIGN,FAIL)


def test_first_missed_probe_then_stuck_zero_detection_retains_both(monkeypatch,tmp_path):
    calls=install_simulation(monkeypatch,{"control":PASS,"mutant":PASS,"stuck_zero":DETECTED})
    (qualified,_),report=run_portfolio(tmp_path)
    assert qualified and calls==["control","mutant","stuck_zero"]
    assert [r["outcome"] for r in report["attempts"]]==["missed","detected"]
    assert report["qualified"] is True and report["outcome"]=="qualified"
    for record in [report["control"],*report["attempts"]]:
        for key in ("source","raw_log"):
            item=record[key]
            assert hashlib.sha256(Path(item["path"]).read_bytes()).hexdigest()==item["sha256"]
    assert report["testbench"]["sha256"]==hashlib.sha256((tmp_path/"tb.v").read_bytes()).hexdigest()
    assert (tmp_path/"tbqual/mutant/sim_log.txt").read_text()=="TEST PASSED\n"


def test_all_missed_probes_reject_without_regenerating_tb(monkeypatch,tmp_path):
    calls=install_simulation(monkeypatch,{name:PASS for name in ("control","mutant","stuck_zero","stuck_one")})
    (qualified,reason),report=run_portfolio(tmp_path)
    assert not qualified and "exhausted" in reason
    assert calls==["control","mutant","stuck_zero","stuck_one"]
    assert report["qualified"] is False and all(r["outcome"]=="missed" for r in report["attempts"])
    assert (tmp_path/"tb.v").read_text()=="// unchanged independent testbench"


@pytest.mark.parametrize("kind",[FailureKind.INFRA,FailureKind.UNKNOWN])
def test_infrastructure_stops_portfolio_without_alternate_probe(monkeypatch,tmp_path,kind):
    calls=install_simulation(monkeypatch,{"control":PASS,"mutant":(False,"tool unavailable",kind,None)})
    (qualified,_),report=run_portfolio(tmp_path)
    assert not qualified and calls==["control","mutant"]
    assert report["outcome"]=="infra_blocked"


@pytest.mark.parametrize("raw",["TEST FAILED: watchdog\n","FAIL watchdog expired\nTEST FAILED: 1 errors\n",
    "FAIL mismatch\nTEST FAILED: 1 errors\nTEST PASSED\n",None])
def test_false_assertion_proof_is_not_detection_but_next_behavior_probe_can_qualify(monkeypatch,tmp_path,raw):
    calls=install_simulation(monkeypatch,{"control":PASS,"mutant":(False,"testbench reported failure",FailureKind.DESIGN,raw),"stuck_zero":DETECTED})
    (qualified,_),report=run_portfolio(tmp_path)
    assert qualified and calls==["control","mutant","stuck_zero"]
    assert report["attempts"][0]["assertion_detected"] is False


def test_constant_zero_reference_reaches_one_probe(monkeypatch,tmp_path):
    source="module m(output [7:0] y); assign y=0; endmodule"
    calls=install_simulation(monkeypatch,{"control":PASS,"stuck_zero":PASS,"stuck_one":DETECTED})
    (qualified,_),report=run_portfolio(tmp_path,source)
    assert qualified and calls==["control","stuck_zero","stuck_one"]
    assert "assign y = -1;" in Path(report["attempts"][-1]["source"]["path"]).read_text()


def test_fallbacks_preserve_symbolic_parameters_signed_packed_shape_and_local_dependencies():
    source="""// @latency 1
module m #(parameter integer W=8,N=W+1)(a,y);
localparam L=N+1;
input signed [L-1:0] a;
output reg signed [0:L-1] y;
always @(posedge a[0]) y<=a;
endmodule"""
    original=infer_module(source,"m")
    probes=[probe for probe in tbqual.qualification_mutations(source,"m") if probe[0]!="mutant"]
    assert [label for label,_,_ in probes]==["stuck_zero","stuck_one"]
    for _,mutant,_ in probes:
        actual=infer_module(mutant,"m")
        assert actual.interface_signature==original.interface_signature
        assert actual.parameters==original.parameters
        assert actual.ports[-1].signed and actual.ports[-1].packed_dimensions==[[0,9]]
        assert actual.latency==1 and actual.latency_known


def test_portfolio_is_bounded_and_deduplicates_exact_bytes(monkeypatch):
    probes=tbqual.qualification_mutations(SOURCE,"m")
    zero=next(source for label,source,_ in probes if label=="stuck_zero")
    monkeypatch.setattr(tbqual,"mutate",lambda source:(zero,"duplicate zero probe"))
    result=tbqual.qualification_mutations(SOURCE,"m")
    assert [label for label,_,_ in result]==["mutant","stuck_one"]
    assert len({source.encode() for _,source,_ in result})==len(result)<=3


def test_invalid_snippets_and_no_outputs_have_no_fallbacks():
    assert tbqual.qualification_mutations("assign y=a;","m")==[]
    assert [label for label,_,_ in tbqual.qualification_mutations("assign y=a+1;","m")]==["mutant"]
    assert tbqual.qualification_mutations("module m(input a); endmodule","m")==[]


def test_endmodule_substring_in_identifier_does_not_corrupt_stub():
    source="module m_endmodule(input a,output y); assign y=a; endmodule"
    probes=tbqual.qualification_mutations(source,"m_endmodule")
    assert len(probes)==2
    assert all(infer_module(mutant,"m_endmodule").name=="m_endmodule" for _,mutant,_ in probes)
