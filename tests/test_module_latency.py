"""Only a selected module's real annotation comments declare its latency."""
from pathlib import Path
import pytest
from autortl.verilog_interface import infer_module,module_declared_latency

FIXTURE=Path(__file__).parent/"fixtures/module_latency_scoped.v"


def test_fixture_scopes_helpers_blocks_strings_and_selected_body_annotation():
    source=FIXTURE.read_text(encoding="utf-8")
    assert module_declared_latency(source,"earlier")==7
    assert module_declared_latency(source,"target")==2
    assert module_declared_latency(source,"later")==4
    assert module_declared_latency(source) is None
    target=infer_module(source,"target")
    assert target.latency_known is True and target.latency==2


@pytest.mark.parametrize("position",["before","after"])
def test_unannotated_top_does_not_inherit_helper_header_or_body(position):
    helper="// @latency 9\nmodule helper;\n// @latency 9\nendmodule\n"
    target="module top(input x,output y); assign y=x; endmodule\n"
    source=helper+target if position=="before" else target+helper
    assert module_declared_latency(source,"top") is None
    inferred=infer_module(source,"top")
    assert inferred.latency_known is False and inferred.latency==0


@pytest.mark.parametrize("prefix",[
    "/*\n// @latency 9\n*/\n",
    "// Example: // @latency 9\n",
    "// The comment @latency 9 is illustrative.\n",
])
def test_block_examples_and_explanatory_mentions_are_not_declarations(prefix):
    assert module_declared_latency(prefix+"module top; endmodule","top") is None


def test_strings_and_escaped_identifiers_do_not_supply_boundaries_or_annotations():
    source=r"""module top;
wire \endmodule ;
wire \module ;
initial $display("endmodule module helper; // @latency 99");
// @latency 3
endmodule
"""
    assert module_declared_latency(source,"top")==3


def test_comment_after_endmodule_on_same_line_cannot_annotate_next_top():
    source="module helper; endmodule // @latency 8\nmodule top; endmodule"
    assert module_declared_latency(source,"top") is None


def test_real_leading_header_can_cross_descriptive_comments_and_timescale():
    source="// @latency 0\n// contract metadata\n`timescale 1ns/1ps\nmodule top; endmodule"
    assert module_declared_latency(source,"top")==0


def test_selected_module_standalone_annotation_supported_anywhere_in_its_body():
    source="module top(input x,output y); assign y=x;\n// @latency 3 trailing explanation\nendmodule"
    assert module_declared_latency(source,"top")==3


def test_same_value_duplicate_annotations_are_unambiguous_but_conflicts_fail():
    source="// @latency 2\nmodule top;\n// @latency 2\nendmodule"
    assert module_declared_latency(source,"top")==2
    with pytest.raises(ValueError,match="conflicting"):
        module_declared_latency(source.replace("// @latency 2\nendmodule","// @latency 3\nendmodule"),"top")


@pytest.mark.parametrize("value",["", "-1", "1.5", "3oops", "two", "1025"])
def test_malformed_and_out_of_range_selected_annotations_fail_actionably(value):
    with pytest.raises(ValueError,match="@latency"):
        module_declared_latency(f"// @latency {value}\nmodule top; endmodule","top")


def test_malformed_annotation_in_unrelated_helper_is_ignored():
    source="// @latency nonsense\nmodule helper; endmodule\nmodule top; endmodule"
    assert module_declared_latency(source,"top") is None


def test_optional_sole_module_client_form_and_explicit_zero():
    assert module_declared_latency("// @latency 0\nmodule m; endmodule")==0
    assert module_declared_latency("// @latency 3\nmodule m; endmodule")==3
    assert module_declared_latency("module m; endmodule") is None
    assert module_declared_latency("// @latency 9") is None


@pytest.mark.parametrize("source",["module top;", "module helper; endmodule", "module top; endmodule module top; endmodule"])
def test_explicit_top_missing_unterminated_or_duplicate_fails(source):
    with pytest.raises(ValueError):
        module_declared_latency(source,"top")
