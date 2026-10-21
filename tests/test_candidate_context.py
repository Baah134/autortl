"""Actual optimization role prompts carry frozen compilation boundary facts."""
import hashlib
import json
from unittest.mock import Mock
import pytest
from autortl import candidate_context,roles
from autortl.spec import ModuleSpec,Port


def facts(text):
    return json.loads(text[text.index("{"):])


def test_scope_identifies_editable_top_and_exact_frozen_file_metadata(tmp_path):
    child=tmp_path/"child.v"
    child.write_text("module child #(parameter W=8)(input [W-1:0] x,output [W-1:0] y); assign y=x; endmodule")
    text=candidate_context.candidate_scope("top",[child])
    scope=facts(text)
    assert scope["editable_top"]=="top"
    companion=scope["frozen_companions"][0]
    assert companion["path"]==str(child.resolve())
    assert companion["sha256"]==hashlib.sha256(child.read_bytes()).hexdigest()
    assert companion["modules"][0]["name"]=="child"
    assert companion["modules"][0]["parameters"]=={"W":8}
    assert companion["source_preview"]==child.read_text()
    assert not companion["preview_truncated"]
    assert "do not redeclare" in text and "INSIDE the editable top" in text
    assert "Do not add clocks or change latency" in text


def test_inventory_ignores_comments_and_string_literals_and_retains_helpers(tmp_path):
    child=tmp_path/"bundle.v"
    child.write_text("""// module fake(input a); endmodule
module child(input a,output y); assign y=a;
initial $display("module string_fake(input x);"); endmodule
/* module comment_fake(input z); endmodule */
module helper(input a,output y); assign y=a; endmodule
""")
    modules=facts(candidate_context.candidate_scope("top",[child]))["frozen_companions"][0]["modules"]
    assert [m["name"] for m in modules]==["child","helper"]


def test_unsupported_interface_keeps_name_and_explicit_warning(tmp_path):
    child=tmp_path/"child.v"
    child.write_text("module child(input [UNKNOWN:0] a); endmodule")
    row=facts(candidate_context.candidate_scope("top",[child]))["frozen_companions"][0]["modules"][0]
    assert row["name"]=="child" and row["interface_warning"]
    assert "ports" not in row and "parameters" not in row


def test_no_companions_is_an_explicit_top_only_boundary():
    text=candidate_context.candidate_scope("top",[])
    assert facts(text)=={"editable_top":"top","frozen_companions":[]}


def test_previews_and_total_json_budget_are_bounded_without_dropping_metadata(tmp_path):
    children=[]
    for i in range(12):
        child=tmp_path/f"child{i}.v"
        child.write_text(f"module child{i}(input x,output y); assign y=x; endmodule\n"+"// preview "+"\t\\\""*4000)
        children.append(child)
    text=candidate_context.candidate_scope("top",children)
    assert len(text)<=candidate_context.MAX_SCOPE_CHARS
    rows=facts(text)["frozen_companions"]
    assert len(rows)==len(children)
    assert all(row["sha256"] and row["modules"] for row in rows)
    assert all(len(row["source_preview"])<=candidate_context.PREVIEW_CHARS_PER_FILE for row in rows)
    assert all(row["preview_truncated"] for row in rows)


def test_metadata_over_budget_fails_actionably_instead_of_omission(tmp_path,monkeypatch):
    child=tmp_path/"child.v";child.write_text("module child(input x); endmodule")
    monkeypatch.setattr(candidate_context,"MAX_SCOPE_CHARS",100)
    with pytest.raises(ValueError,match="metadata exceeds"):
        candidate_context.candidate_scope("top",[child])


def test_duplicate_paths_are_not_repeated_and_top_cannot_be_frozen(tmp_path):
    child=tmp_path/"child.v";child.write_text("module child(input x); endmodule")
    assert len(facts(candidate_context.candidate_scope("top",[child,child]))["frozen_companions"])==1
    with pytest.raises(ValueError,match="editable top is also declared"):
        candidate_context.candidate_scope("child",[child])


@pytest.mark.parametrize("method",["generate","fix","surgery"])
@pytest.mark.parametrize("context",[None,"FROZEN_SCOPE_SENTINEL"])
def test_actual_rtl_role_calls_append_immutable_context_without_signature_changes(monkeypatch,method,context):
    call=Mock(return_value="```verilog\nmodule top(input x,output y); assign y=x; endmodule\n```")
    monkeypatch.setattr(roles,"ask",call)
    role=roles.TimingDoctor() if method=="surgery" else roles.Generator()
    if context is not None:
        role.run_context=context
    module=ModuleSpec("top","pass through",[Port("x","input",1),Port("y","output",1)])
    if method=="generate":
        result=role.generate(module,"source","instruction","mutation",None)
    elif method=="fix":
        result=role.fix("source","diagnosis","error","tb",[],None)
    else:
        result=role.surgery("source","instruction","path",None)
    prompt=call.call_args.args[1]
    assert "module top" in result
    if context:
        assert prompt.count("# AUTHORITATIVE HARNESS FACTS (immutable)")==1
        assert prompt.count(context)==1
    else:
        assert "# AUTHORITATIVE HARNESS FACTS (immutable)" not in prompt
    assert call.call_args.kwargs["budget"] is None
    if method=="surgery":
        assert call.call_args.kwargs["max_turns"]==3
