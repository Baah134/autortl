"""Prepare unsigned divider admission inputs; never launch models or simulators."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = [8, 1, 2, 4, 13, 16]
DOMAIN = {"width_min": 1, "width_max": 16}

# Twenty distinct source mutations; observable failure classes may overlap.
MUTATIONS = {'strict_subtraction_compare': [("trial_remainder >= {1'b0, divisor_saved}",
                                 "trial_remainder > {1'b0, divisor_saved}")],
 'addition_instead_of_subtraction': [("trial_remainder - {1'b0, divisor_saved}",
                                      "trial_remainder + {1'b0, divisor_saved}")],
 'quotient_shift_right': [('(quotient_work << 1) | subtract_divisor',
                           '(quotient_work >> 1) | subtract_divisor')],
 'wrong_dividend_shift_bit': [('| quotient_work[WIDTH-1]', '| quotient_work[0]')],
 'trial_data_msb_cleared': [('(remainder_work << 1) | quotient_work[WIDTH-1]',
                             "((remainder_work << 1) | quotient_work[WIDTH-1]) & ({WIDTH{1'b1}} >> 1)")],
 'zero_divisor_quotient_zero': [("(divisor_saved == 0) ? {WIDTH{1'b1}} : next_quotient",
                                 "(divisor_saved == 0) ? {WIDTH{1'b0}} : next_quotient")],
 'zero_divisor_remainder_zero': [('(divisor_saved == 0) ? dividend_saved : next_remainder[WIDTH-1:0]',
                                  "(divisor_saved == 0) ? {WIDTH{1'b0}} : next_remainder[WIDTH-1:0]")],
 'captured_dividend_truncated_eight': [('dividend_saved <= dividend;', "dividend_saved <= dividend & 8'hff;"),
                                       ('quotient_work <= dividend;', "quotient_work <= dividend & 8'hff;")],
 'captured_divisor_truncated_eight': [('divisor_saved <= divisor;', "divisor_saved <= divisor & 8'hff;")],
 'hardcoded_eight_iterations': [('steps_left <= WIDTH;', 'steps_left <= 8;')],
 'early_completion': [('if(steps_left == 1) begin', 'if(steps_left == ((WIDTH > 1) ? 2 : 1)) begin')],
 'trivial_operand_shortcut': [('steps_left <= WIDTH;',
                               'steps_left <= ((dividend == 0) || (divisor == 0) || (divisor == 1) || '
                               '(dividend == divisor)) ? 1 : WIDTH;')],
 'ready_while_busy': [('assign in_ready = !busy && !out_valid;', 'assign in_ready = !out_valid;')],
 'ready_on_retirement_edge': [('assign in_ready = !busy && !out_valid;',
                               'assign in_ready = !busy && (!out_valid || out_ready);')],
 'current_divisor_not_captured': [("trial_remainder >= {1'b0, divisor_saved}",
                                   "trial_remainder >= {1'b0, divisor}"),
                                  ("trial_remainder - {1'b0, divisor_saved}",
                                   "trial_remainder - {1'b0, divisor}")],
 'current_dividend_during_computation': [('quotient_work <= next_quotient;', 'quotient_work <= dividend;')],
 'stalled_quotient_drift': [('if(out_valid && out_ready) out_valid <= 0;',
                             'if(out_valid && out_ready) out_valid <= 0;\n'
                             "            if(out_valid && !out_ready) quotient <= quotient ^ 1'b1;")],
 'stalled_remainder_drift': [('if(out_valid && out_ready) out_valid <= 0;',
                              'if(out_valid && out_ready) out_valid <= 0;\n'
                              "            if(out_valid && !out_ready) remainder <= remainder ^ 1'b1;")],
 'asynchronous_reset': [('always @(posedge clk) begin', 'always @(posedge clk or posedge rst) begin')],
 'reset_preserves_held_result': [('if(rst) begin', "if(rst && (out_valid !== 1'b1)) begin")]}

MUTATION_NOTES = {'trial_data_msb_cleared': 'Clear the highest dividend-data bit of the trial value, not merely its extra '
                           'guard bit. Dropping only the WIDTH+1 guard bit can be equivalent for this '
                           'unsigned WIDTH-bit operand domain.',
 'captured_dividend_truncated_eight': 'Effective operand capture truncation only; symbolic register and '
                                      'public port widths remain unchanged.',
 'captured_divisor_truncated_eight': 'Effective operand capture truncation only; symbolic register and '
                                     'public port widths remain unchanged.',
 'reset_preserves_held_result': 'Suppress reset only for a known held-valid result. Case inequality '
                                'deliberately permits initial unknown out_valid to reset normally, isolating '
                                'held-result abort behavior.'}

def mutation_targets(reference):
    """Exact edits shared with provenance export; sources are never regenerated."""
    return MUTATIONS


def case_sources(reference=None):
    """Reject missing/ambiguous targets and duplicate or unchanged variants."""
    if reference is None:
        reference = (ROOT / "qualification/reference.v").read_text(encoding="utf-8")
    result = {"reference": reference}
    for name, targets in mutation_targets(reference).items():
        source = reference
        for old, new in targets:
            if not old or old == new or reference.count(old) != 1 or source.count(old) != 1:
                raise ValueError("qualification target no longer unique: " + name)
            source = source.replace(old, new, 1)
        result[name] = source
    if len(set(result.values())) != len(result):
        raise ValueError("qualification source variants are not distinct")
    return result


def materialize_cases(output):
    """Write fresh complete inputs and exact byte hashes, not measured verdicts.

    Selected matrix configurations do not prove the complete declared domain.
    Every faulty case requires a real behavioral assertion, never a compile
    error, infrastructure failure or watchdog expiration.
    """
    from autortl.linter import top_verilog
    from autortl.spec import DesignSpec

    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    wrapper = top_verilog(DesignSpec.load(ROOT / "design_spec.json"))
    sources = case_sources()
    targets = mutation_targets(sources["reference"])
    manifest = {
        "schema_version": 1,
        "status": "prepared_not_simulated",
        "top": "iterative_divider_tb",
        "domain": DOMAIN,
        "matrix": [{"width": width, "default_wrapper": index == 0}
                   for index, width in enumerate(MATRIX)],
        "cases": [],
    }
    for name, source in sources.items():
        directory = output / name
        directory.mkdir()
        files = {
            "iterative_divider_core.v": source.encode("utf-8"),
            "iterative_divider.v": wrapper.encode("utf-8"),
            "iterative_divider_tb.v": (ROOT / "iterative_divider_tb.v").read_bytes(),
        }
        for filename, data in files.items():
            (directory / filename).write_bytes(data)
        manifest["cases"].append({
            "name": name,
            "expected_verdict": "TEST PASSED" if name == "reference" else "TEST FAILED",
            "required_failure_kind": None if name == "reference" else "behavioral_assertion",
            "mutation_note": MUTATION_NOTES.get(name),
            "mutation_targets": [{"original": old, "replacement": new, "original_occurrences": 1}
                                 for old, new in targets.get(name, [])],
            "files": [{"path": str((directory / filename).resolve()),
                       "sha256": hashlib.sha256(data).hexdigest()}
                      for filename, data in files.items()],
        })
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
