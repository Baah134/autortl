"""Vivado-free tests for the harness-winners board suite: the reference models
agree with every I/O example in the frozen specifications, every winner is
byte-identical to its run's recorded best design, each fault changes exactly
one place, vectors restart correctly, and the negative-control models really
differ."""
import json
from pathlib import Path
import random
import sys

import pytest

SUITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SUITE))

from hwsuite import designs, models, vectors          # noqa: E402
from hwsuite.cli import main as cli_main               # noqa: E402

REPO = designs.REPO
SPECS = {"fir4": "tier3/signed_fir4_build", "elastic_dot4": "tier3/elastic_dot4_build",
         "dot4_pipeline": "tier3/dot4_pipeline_build", "iterative_divider": "tier3/iterative_divider_build",
         "packet_fifo": "tier2/packet_fifo_build", "sync_fifo": "tier2/sync_fifo_build"}
TABLE = designs.load()


def spec_examples(design):
    spec = json.loads((REPO / "curriculum" / SPECS[design] / "design_spec.json").read_text(encoding="utf-8"))
    return [(m["name"], e) for m in spec["modules"] for e in m.get("examples", [])
            if e["inputs"].get("rst", 0) == 0]


def run_from_reset(name, tx):
    model = models.model_for(name)
    return int.from_bytes(model.step(bytes(tx)), "little")


def test_every_design_has_a_model_and_matching_widths():
    assert set(TABLE) == set(models.MODELS) == set(SPECS)
    for name, design in TABLE.items():
        model = models.model_for(name)
        assert (model.in_bytes, model.out_bytes) == (design.in_bytes, design.out_bytes)


@pytest.mark.parametrize("name", sorted(TABLE))
def test_winner_is_byte_identical_to_recorded_best(name):
    TABLE[name].verify()


@pytest.mark.parametrize("name", sorted(TABLE))
def test_harness_measurement_exists_for_the_same_winner(name):
    design = TABLE[name]
    summary = json.loads((design.state.parent / "run_summary.json").read_text(encoding="utf-8"))
    assert summary.get("best_sha256", design.sha256) == design.sha256
    best = summary["best_metrics"]
    assert best["sim_passed"] is True and best["lut_used"] > 0
    assert best["wns_ns"] >= 0 and best["whs_ns"] >= 0


@pytest.mark.parametrize("name", sorted(TABLE))
def test_fault_changes_exactly_one_place(name):
    design = TABLE[name]
    original = design.winner.read_text(encoding="utf-8")
    faulted = design.faulted_source()
    assert faulted != original
    assert len(faulted) - len(original) == len(design.fault["replace"]) - len(design.fault["find"])
    before = [l for l in original.splitlines()]
    after = [l for l in faulted.splitlines()]
    assert sum(a != b for a, b in zip(before, after)) == 1


def test_only_the_divider_contract_forbids_overlapping_transfers():
    # Its spec: in_ready = !busy && !out_valid, so it never accepts while retiring.
    assert {name for name, d in TABLE.items() if not d.overlap} == {"iterative_divider"}
    spec = (REPO / "curriculum" / SPECS["iterative_divider"] / "design_spec.json").read_text(encoding="utf-8")
    assert "in_ready equals !busy && !out_valid" in spec


def test_unknown_fault_anchor_is_rejected(tmp_path):
    design = TABLE["sync_fifo"]
    broken = designs.Design(**{**design.__dict__, "fault": {"find": "not in the file", "replace": "x"}})
    with pytest.raises(designs.DesignError, match="anchor"):
        broken.faulted_source()


def test_tampered_winner_is_rejected(tmp_path):
    design = TABLE["sync_fifo"]
    copy = tmp_path / "sync_fifo.v"
    copy.write_bytes(design.winner.read_bytes() + b"\n")
    with pytest.raises(designs.DesignError, match="SHA-256"):
        designs.Design(**{**design.__dict__, "winner": copy}).verify()


def test_fir4_matches_spec_examples():
    # An example holds x for `after_cycles` accepted samples from reset; the
    # expected value is the last output as an unsigned 13-bit pattern.
    examples = spec_examples("fir4")
    assert len(examples) == 6
    for _, e in examples:
        model = models.model_for("fir4")
        for _ in range(e["after_cycles"]):
            y = int.from_bytes(model.step(bytes([e["inputs"]["x"] & 0xFF])), "little")
        assert y & 0x1FFF == e["expected"]["out_data"]


def test_fir4_is_stateful_and_reset_clears_history():
    model = models.model_for("fir4")
    outs = [int.from_bytes(model.step(bytes([b & 0xFF])), "little", signed=True) for b in (127, -128, 127, -128)]
    assert outs == [381, -1019, 1910, -2169]          # -2169 is the most negative possible output
    model.reset()
    assert int.from_bytes(model.step(bytes([127])), "little", signed=True) == 381


def test_elastic_dot4_matches_spec_examples():
    examples = spec_examples("elastic_dot4")
    assert len(examples) == 3
    for _, e in examples:
        i = e["inputs"]
        tx = [i[k] for k in ("a0", "b0", "a1", "b1", "a2", "b2", "a3", "b3")]
        assert run_from_reset("elastic_dot4", tx) == e["expected"]["out_data"]


def test_dot4_pipeline_matches_pair_examples():
    for module, e in spec_examples("dot4_pipeline"):
        i = e["inputs"]
        if module == "dot4_pair01":
            tx = [i["a0"], i["b0"], i["a1"], i["b1"], 0, 0, 0, 0]
            assert run_from_reset("dot4_pipeline", tx) == e["expected"]["pair01_sum"]
        elif module == "dot4_pair23":
            tx = [0, 0, 0, 0, i["a2"], i["b2"], i["a3"], i["b3"]]
            assert run_from_reset("dot4_pipeline", tx) == e["expected"]["pair23_sum"]
    assert run_from_reset("dot4_pipeline", [255] * 8) == 260100


def test_iterative_divider_matches_spec_examples_including_divide_by_zero():
    examples = spec_examples("iterative_divider")
    assert len(examples) == 6
    for _, e in examples:
        result = run_from_reset("iterative_divider", [e["inputs"]["dividend"], e["inputs"]["divisor"]])
        assert result & 0xFF == e["expected"]["quotient"]
        assert result >> 8 == e["expected"]["remainder"]


def test_fifo_models_match_spec_examples():
    for _, e in spec_examples("packet_fifo"):
        result = run_from_reset("packet_fifo", [e["inputs"]["in_data"], e["inputs"]["in_last"]])
        assert (result & 0xFF, result >> 8) == (e["expected"]["out_data"], e["expected"]["out_last"])
    for _, e in spec_examples("sync_fifo"):
        assert run_from_reset("sync_fifo", [e["inputs"]["in_data"]]) == e["expected"]["out_data"]


@pytest.mark.parametrize("name", sorted(TABLE))
def test_wrong_model_differs_on_most_of_the_stimulus(name):
    good, bad = models.model_for(name), models.model_for(name, wrong=True)
    stimulus = good.stimulus(random.Random(5), 2000)
    differ = sum(good.step(tx) != bad.step(tx) for tx in stimulus)
    assert differ > 0.5 * len(stimulus), f"{name}: wrong model differs on only {differ} of 2000"


@pytest.mark.parametrize("name", sorted(TABLE))
def test_stimulus_starts_with_edge_cases_and_has_the_right_widths(name):
    model = models.model_for(name)
    stimulus = model.stimulus(random.Random(1), 300)
    assert len(stimulus) == 300 and all(len(tx) == model.in_bytes for tx in stimulus)
    assert stimulus[:len(model.leading())] == model.leading()


def test_packet_last_marker_uses_every_bit_of_byte_one():
    model = models.model_for("packet_fifo")
    for marker in range(256):
        assert model.step(bytes([0x3C, marker])) == bytes([0x3C, 1 if marker else 0])
    stimulus = model.stimulus(random.Random(3), 2000)
    markers = {tx[1] for tx in stimulus}
    assert 0 in markers and len(markers - {0, 1}) > 100      # high bits really exercised


def test_divider_stimulus_exercises_divide_by_zero():
    stimulus = models.model_for("iterative_divider").stimulus(random.Random(9), 2000)
    assert sum(tx[1] == 0 for tx in stimulus) > 50


def test_vectors_restart_resets_the_stateful_model(tmp_path):
    stimulus, expected = vectors.build("fir4", 40, 20)
    assert stimulus[20:30] == models.model_for("fir4").leading()
    fresh = models.model_for("fir4")
    assert expected[20:30] == [fresh.step(tx) for tx in stimulus[20:30]]
    vectors.write(tmp_path, stimulus, expected)
    assert len((tmp_path / "stim.hex").read_text().split()) == 40
    assert len((tmp_path / "expect.hex").read_text().split()) == 80


def test_vectors_reject_a_restart_outside_the_stream():
    with pytest.raises(ValueError):
        vectors.build("sync_fifo", 10, 10)


def test_results_out_of_range_are_rejected():
    model = models.model_for("sync_fifo")
    with pytest.raises(ValueError, match="input bytes"):
        model.step(b"\x00\x00")


def test_cli_verify_lists_every_design(capsys):
    assert cli_main(["verify"]) == 0
    out = capsys.readouterr().out
    assert all(name in out for name in TABLE)


def test_evidence_never_overwrites_a_folder(tmp_path, capsys):
    (tmp_path / "existing.txt").write_text("keep")
    assert cli_main(["evidence", "--out", str(tmp_path)]) == 1
    assert "never overwritten" in capsys.readouterr().err
    assert (tmp_path / "existing.txt").read_text() == "keep"


def test_evidence_refuses_incomplete_outputs(tmp_path, monkeypatch, capsys):
    from hwsuite import cli
    monkeypatch.setattr(cli, "SUITE", tmp_path / "suite")      # no build/ outputs at all
    assert cli_main(["evidence", "--design", "sync_fifo", "--out", str(tmp_path / "ev")]) == 1
    assert "missing outputs" in capsys.readouterr().err
    assert not (tmp_path / "ev").exists() and not (tmp_path / "ev.partial").exists()   # nothing half-written


def test_evidence_readme_renders_every_design_from_the_summary():
    from hwsuite.cli import evidence_readme
    run = {"checked": 50000, "requested": 50000, "mismatches": 0, "restarts": 10, "wrong_model": False}
    wrong = {"checked": 2000, "requested": 2000, "mismatches": 1990, "restarts": 1, "wrong_model": True}
    summary = {"fir4": {"title": "Signed FIR", "hardware": {"model_50000": run, "wrong_model_2000": wrong},
                        "fault": "tap2", "fault_simulation": "FAIL: 1190 errors, 1200 of 1200 results checked",
                        "build_warnings": 0, "wns_ns": 2.567, "whs_ns": 0.037,
                        "winner_resources": {"luts": 51, "ffs": 67, "dsps": 0},
                        "harness_measurement": {"lut_used": 52, "ff_used": 67, "dsp_used": 0}}}
    text = evidence_readme(summary)
    row = next(line for line in text.splitlines() if line.startswith("| Signed FIR"))
    assert "50,000/50,000, 0 mismatches, 10 restarts" in row and "1,990/2,000 differ" in row
    assert "tap2: FAIL: 1190 errors |" in row and "+2.567 / +0.037" in row
    assert "51 / 67 / 0 | 52 / 67 / 0 |" in row


def test_program_and_hw_use_an_archived_bitstream_with_bit(tmp_path, monkeypatch):
    # A fresh clone has no build/ folder; --bit programs and identifies an
    # archived bitstream instead.
    from hwsuite import cli, hw
    archived = REPO / "evidence" / "2026-10-28" / "basys3-bitstreams-01" / "harness_winners" / "sync_fifo.bit"
    monkeypatch.setattr(cli, "SUITE", tmp_path / "suite")
    calls = []

    def fake_run(cmd, cwd, log):
        calls.append(cmd)
        log.write_text("RESULT: programmed\n")
        return 0

    monkeypatch.setattr(cli, "_run", fake_run)
    monkeypatch.setattr(cli, "_tool", lambda vivado, name: name)
    monkeypatch.setattr(hw, "run", lambda design, **kw: {"passed": True, "checked": 1})
    monkeypatch.setattr(hw, "format_report", lambda report: "ok")
    assert cli_main(["program", "--design", "sync_fifo"]) == 1          # nothing built, no --bit
    assert cli_main(["program", "--design", "sync_fifo", "--bit", str(archived)]) == 0
    assert calls[-1][-1] == archived.as_posix()
    assert cli_main(["hw", "--design", "sync_fifo", "--bit", str(archived), "--count", "1"]) == 0
    report = json.loads((tmp_path / "suite" / "build" / "sync_fifo" / "hw" / "model_1.json").read_text())
    # The tested payload of the archived file is the one the board evidence recorded.
    summary = json.loads((REPO / "evidence" / "2026-10-28" / "basys3-harness-winners-01" / "summary.json").read_text())
    assert report["bitstream_payload_sha256"] == summary["sync_fifo"]["bitstream_payload_sha256"]
    # hw reports what program loaded: it refuses a different --bit or design.
    other = archived.with_name("fir4.bit")
    assert cli_main(["hw", "--design", "sync_fifo", "--bit", str(other), "--count", "1"]) == 1
    assert cli_main(["hw", "--design", "fir4", "--count", "1"]) == 1
    assert cli_main(["hw", "--design", "sync_fifo", "--count", "1"]) == 0      # no --bit: the record decides
    assert cli_main(["hw", "--design", "sync_fifo", "--bit", str(tmp_path / "absent.bit"), "--count", "1"]) == 1
    # A failed programming attempt clears the record: the board's image is unknown.
    monkeypatch.setattr(cli, "_run", lambda cmd, cwd, log: (log.write_text("ERROR\n"), 1)[1])
    assert cli_main(["program", "--design", "sync_fifo", "--bit", str(archived)]) == 1
    assert not (tmp_path / "suite" / "build" / "programmed.json").exists()


def test_bit_is_only_for_program_and_hw(tmp_path):
    with pytest.raises(SystemExit):
        cli_main(["all", "--bit", str(tmp_path / "x.bit")])


def test_archived_bitstreams_match_the_board_evidence():
    # Ties summary.json's recorded digests to the archived files, so CI
    # catches a bitstream that drifts from the evidence that cites it.
    import hashlib
    from hwsuite import reports
    ev = REPO / "evidence" / "2026-10-28"
    summary = json.loads((ev / "basys3-harness-winners-01" / "summary.json").read_text())
    manifest = json.loads((ev / "basys3-bitstreams-01" / "manifest.json").read_text())
    for name, entry in summary.items():
        bit = ev / "basys3-bitstreams-01" / "harness_winners" / f"{name}.bit"
        assert hashlib.sha256(bit.read_bytes()).hexdigest() == entry["bitstream_sha256"]
        assert reports.bitstream_payload_sha256(bit) == entry["bitstream_payload_sha256"]
        assert manifest["files"][f"harness_winners/{name}.bit"] == entry["bitstream_sha256"]


def test_cli_rejects_unknown_design(capsys):
    assert cli_main(["verify", "--design", "nope"]) == 1
    assert "unknown design" in capsys.readouterr().err
