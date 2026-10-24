"""Hash-bound critical-path context from real-layout deep timing reports."""
import hashlib
import json
from pathlib import Path
import pytest
from autortl import roles
from autortl.contract_context import flow_evidence
from autortl.report_parser import VivadoMetrics,parse_timing,parse_timing_text
from autortl.timing_doctor import first_violated_path,parse_worst_path,diagnose,TimingCategory,PATH_EXCERPT_CHARS

FIXTURES=Path(__file__).parent/"fixtures"


def copy_fixture(tmp_path,name="fifo_deep_timing.rpt",target="timing_routed.rpt"):
    path=tmp_path/target
    path.write_bytes((FIXTURES/name).read_bytes())
    return path


def test_deep_setup_excerpt_includes_endpoints_and_memory_resource_not_header_only(tmp_path):
    path=copy_fixture(tmp_path)
    raw=path.read_bytes()
    assert raw.index(b"Slack (VIOLATED)")>1800
    evidence=flow_evidence(tmp_path)
    excerpt=evidence["first_violated_path_excerpt"]
    assert excerpt["category"]=="setup" and excerpt["slack_ns"]==-.931
    assert excerpt["source"]=="u_sync_fifo_core/rd_ptr_reg[1]/C"
    assert excerpt["destination"]=="out_data[7]"
    assert excerpt["logic_levels"]==2
    assert "RAMD32" in excerpt["text"] and "Netlist Resource(s)" in excerpt["text"]
    assert "Min Delay Paths" not in excerpt["text"]
    assert excerpt["path"]==str(path.resolve())
    assert excerpt["sha256"]==hashlib.sha256(raw).hexdigest()
    assert excerpt["sha256"]==evidence["report_manifest"][0]["sha256"]
    assert len(excerpt["text"])<=PATH_EXCERPT_CHARS


def test_deep_hold_excerpt_uses_hold_endpoints_not_earlier_setup_met_path(tmp_path):
    copy_fixture(tmp_path,"hold_deep_timing.rpt")
    excerpt=flow_evidence(tmp_path)["first_violated_path_excerpt"]
    assert excerpt["category"]=="hold" and excerpt["slack_ns"]==-.125
    assert excerpt["source"]=="u_sync_fifo_core/wr_ptr_reg[1]/C"
    assert "WADR1" in excerpt["destination"]
    assert excerpt["logic_levels"]==0
    assert "rd_ptr_reg" not in excerpt["text"]
    assert diagnose(tmp_path,False).category==TimingCategory.HOLD


def test_routed_precedes_stale_preroute_and_no_fallback_for_met_or_malformed_routed(tmp_path):
    copy_fixture(tmp_path,target="timing.rpt")
    routed=copy_fixture(tmp_path,"hold_deep_timing.rpt")
    assert flow_evidence(tmp_path)["first_violated_path_excerpt"]["category"]=="hold"
    routed.write_text("malformed timing report")
    assert flow_evidence(tmp_path)["first_violated_path_excerpt"] is None
    routed.write_text("WNS(ns)  WHS(ns)\n1.000 0.100\n")
    assert flow_evidence(tmp_path)["first_violated_path_excerpt"] is None
    routed.unlink()
    assert flow_evidence(tmp_path)["first_violated_path_excerpt"]["path"].endswith("timing.rpt")


@pytest.mark.parametrize("text",["", "Slack (VIOLATED) : -1.0ns", "WNS(ns)  WHS(ns)\n-1.0 0.1\nSlack (VIOLATED) : -1.0ns\nPath Type: Max\n"])
def test_missing_or_incomplete_path_stays_absent(text):
    assert first_violated_path(text) is None


def test_path_level_and_fanout_fields_never_leak_from_another_path():
    text=(FIXTURES/"fifo_deep_timing.rpt").read_bytes().decode("utf-8")
    text=text.replace("Logic Levels:           2", "Other Field:            2",1)
    text=text.replace("Logic Levels:           0", "Logic Levels:           99",1)
    path=first_violated_path(text)
    assert path["logic_levels"] is None
    assert "Logic Levels:           99" not in path["text"]
    assert path["fanout"]==18  # this path's clock/data nets, never another path's maxima


def test_excerpt_limit_is_explicit_and_preserves_metadata():
    text=(FIXTURES/"fifo_deep_timing.rpt").read_bytes().decode("utf-8")
    marker="    Location             Delay type"
    text=text.replace(marker,"    raw-resource-row RAMD32\n"*500+marker,1)
    path=first_violated_path(text)
    assert path["truncated"] and len(path["text"])==PATH_EXCERPT_CHARS
    assert path["source"] and path["destination"]


def test_report_text_parser_matches_path_wrapper_for_exact_decoded_bytes(tmp_path):
    path=copy_fixture(tmp_path)
    a,b=VivadoMetrics(),VivadoMetrics()
    parse_timing(path,a)
    parse_timing_text(path.read_bytes().decode("utf-8",errors="replace"),b)
    assert a.to_dict()==b.to_dict()
    assert (a.wns_ns,a.whs_ns)==(-.931,.091)


def test_report_snapshot_is_read_once_for_hash_header_and_path(tmp_path,monkeypatch):
    path=copy_fixture(tmp_path)
    raw=path.read_bytes()
    original=Path.read_bytes
    reads=[]
    def read_once(candidate):
        if candidate==path:
            reads.append(candidate)
            return raw if len(reads)==1 else b"changed after initial snapshot"
        return original(candidate)
    monkeypatch.setattr(Path,"read_bytes",read_once)
    evidence=flow_evidence(tmp_path)
    assert len(reads)==1
    excerpt=evidence["first_violated_path_excerpt"]
    assert excerpt["sha256"]==hashlib.sha256(raw).hexdigest()
    assert "RAMD32" in excerpt["text"]


def test_actual_planner_prompt_receives_deep_path_evidence(tmp_path,monkeypatch):
    copy_fixture(tmp_path)
    calls=[]
    monkeypatch.setattr(roles,"ask",lambda role,prompt,**kwargs:calls.append(prompt) or "plan")
    planner=roles.Planner()
    planner.run_context=json.dumps(flow_evidence(tmp_path))
    planner.plan(1,"contract","progress",[],VivadoMetrics(),[],None)
    assert "first_violated_path_excerpt" in calls[0]
    assert "RAMD32" in calls[0] and "out_data[7]" in calls[0]


def test_parse_worst_path_reports_global_wns_separately_from_hold_path_metadata():
    path=FIXTURES/"hold_deep_timing.rpt"
    wns,levels,fanout,snippet=parse_worst_path(path)
    assert wns==.931 and levels==0
    assert "wr_ptr_reg" in snippet and "Slack (VIOLATED)" in snippet



def test_doctor_does_not_invent_missing_path_type_from_matching_global_slack(tmp_path):
    path=copy_fixture(tmp_path)
    text=path.read_text(encoding="utf-8")
    text=text.replace("Path Type:              Max at Slow Process Corner", "Unknown Type:           Max at Slow Process Corner",1)
    path.write_text(text,encoding="utf-8")
    wns,levels,fanout,snippet=parse_worst_path(path)
    assert wns==-.931 and (levels,fanout,snippet)==(0,0,"")
    assert flow_evidence(tmp_path)["first_violated_path_excerpt"] is None
