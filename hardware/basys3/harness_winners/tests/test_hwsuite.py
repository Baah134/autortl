"""Vivado-free tests for the harness-winners board suite: the reference models
agree with every I/O example in the frozen specifications, every winner is
byte-identical to its run's recorded best design, each fault changes exactly
one place, vectors restart correctly, and the negative-control models really
differ."""
import hashlib
import json
import math
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
         "packet_fifo": "tier2/packet_fifo_build", "sync_fifo": "tier2/sync_fifo_build",
         "aes128": "tier6/aes128_core_build", "cordic": "tier6/cordic_build",
         "fir16_sym": "tier5/fir16_sym_build"}
# The archived winners as of this suite's last edit, pinned here so a
# designs.json edit cannot silently swap a winner and its hash together.
PINNED_SHA256 = {
    "aes128": ("evidence/2026-11-02/tier6-aes128/run/aes128_core_best.v",
               "69316101be0e8d12cec4b45678e72851da18ae95663891c968beb0e65ba5ec3c"),
    "cordic": ("evidence/2026-11-02/tier6-cordic/run/cordic_sincos_best.v",
               "aa5fd82e8329371da619a451846fce9d38a19f2334772c350849be9448d6deff"),
    "fir16_sym": ("evidence/2026-11-02/fir16-ooc-02/run/fir16_sym_best.v",
                  "0099ea011cf11ef1277dedf99d4382f28c02d8403b8d2d0176f19c4bdca767d1"),
}
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


def test_only_iterative_contracts_forbid_overlapping_transfers():
    # Their specs: in_ready = !busy && !out_valid, so they never accept while retiring.
    assert {name for name, d in TABLE.items() if not d.overlap} == {"iterative_divider", "aes128", "cordic"}
    spec = (REPO / "curriculum" / SPECS["iterative_divider"] / "design_spec.json").read_text(encoding="utf-8")
    assert "in_ready equals !busy && !out_valid" in spec
    for name in ("aes128", "cordic"):
        spec = (REPO / "curriculum" / SPECS[name] / "design_spec.json").read_text(encoding="utf-8")
        assert "in_ready = !busy && !out_valid" in spec


@pytest.mark.parametrize("name", sorted(PINNED_SHA256))
def test_new_winners_are_pinned_and_match_their_run_state(name):
    path, digest = PINNED_SHA256[name]
    design = TABLE[name]
    assert design.winner == REPO / path and design.sha256 == digest
    assert hashlib.sha256(design.winner.read_bytes()).hexdigest() == digest
    state = json.loads(design.state.read_text(encoding="utf-8"))
    assert state["best_sha256"] == digest
    summary = json.loads((design.state.parent / "run_summary.json").read_text(encoding="utf-8"))
    assert summary["top_module"] == design.module and summary["status"] == "done"


def test_transaction_widths_are_bounded_by_the_shell():
    assert max(max(d.in_bytes, d.out_bytes) for d in TABLE.values()) == designs.MAX_BYTES == 32
    tcl = (SUITE / "scripts" / "build.tcl").read_text(encoding="utf-8")
    assert "$value > 32" in tcl
    bench = (SUITE / "sim" / "tb_stream_shell.v").read_text(encoding="utf-8")
    assert "MAX_BYTES = 32 * 4096" in bench


def test_width_above_the_bound_is_rejected(tmp_path):
    raw = json.loads((SUITE / "designs.json").read_text(encoding="utf-8"))
    raw = {"aes128": {**raw["aes128"], "in_bytes": 33}}
    path = tmp_path / "designs.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(designs.DesignError, match="1..32"):
        designs.load(path)


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


def _block(value: int) -> bytes:
    return value.to_bytes(16, "big")                 # spec ports are big-endian: byte 0 = [127:120]


def test_aes_sbox_is_computed_and_has_the_published_properties():
    sbox = models.AES_SBOX
    assert (sbox[0x00], sbox[0x01], sbox[0x53], sbox[0xFF]) == (0x63, 0x7C, 0xED, 0x16)
    assert sorted(sbox) == list(range(256))                       # a permutation
    assert all(sbox[v] != v and sbox[v] != v ^ 0xFF for v in range(256))   # no (opposite) fixed points
    assert all(models._gf_mul(v, models._gf_inverse(v)) == 1 for v in range(1, 256))


# FIPS-197 Appendix C.1 and Appendix B, then AESAVS (GFSbox, KeySbox, VarTxt,
# VarKey) known answers: (key, plaintext, ciphertext).
AES_KNOWN_ANSWERS = [
    ("000102030405060708090a0b0c0d0e0f", "00112233445566778899aabbccddeeff", "69c4e0d86a7b0430d8cdb78070b4c55a"),
    ("2b7e151628aed2a6abf7158809cf4f3c", "3243f6a8885a308d313198a2e0370734", "3925841d02dc09fbdc118597196a0b32"),
    ("00" * 16, "f34481ec3cc627bacd5dc3fb08f273e6", "0336763e966d92595a567cc9ce537f5e"),
    ("00" * 16, "9798c4640bad75c7c3227db910174e72", "a9a1631bf4996954ebc093957b234589"),
    ("10a58869d74be5a374cf867cfb473859", "00" * 16, "6d251e6944b051e04eaa6fb4dbf78465"),
    ("00" * 16, "80" + "00" * 15, "3ad78e726c1ec02b7ebfe92b23d9ec34"),
    ("80" + "00" * 15, "00" * 16, "0edd33d3c621e546455bd8ba1418bec8"),
    ("00" * 16, "00" * 16, "66e94bd4ef8a2c3b884cfa59ca342b2e"),
]


@pytest.mark.parametrize("key,pt,ct", AES_KNOWN_ANSWERS)
def test_aes_model_matches_published_known_answers(key, pt, ct):
    # The transaction is the key then the plaintext in FIPS byte order, and
    # the result is the ciphertext in the same order, byte 0 first.
    tx = bytes.fromhex(key) + bytes.fromhex(pt)
    assert models.model_for("aes128").step(tx) == bytes.fromhex(ct)


def test_aes_key_schedule_matches_fips197_appendix_a1():
    key, rcon = bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c"), 1
    for _ in range(10):
        key = models.aes_key_step(key, rcon)
        rcon = models._gf_mul(rcon, 2)
    assert key.hex() == "d014f9a8c9ee2589e13f0cc8b6630ca6"     # w[40..43]


def test_aes_model_matches_spec_module_examples():
    examples = spec_examples("aes128")
    for module, e in examples:
        i, x = e["inputs"], e["expected"]
        if module == "aes_round":
            got = models.aes_round(_block(i["state_in"]), _block(i["round_key"]), bool(i["final_round"]))
            assert got == _block(x["state_out"])
        elif module == "aes_key_step":
            assert models.aes_key_step(_block(i["key_in"]), i["rcon"]) == _block(x["key_out"])
        elif e["after_cycles"] == 1:                 # aes_ctrl: the accepting edge applies AddRoundKey
            assert x["ct"] == i["pt"] ^ i["key"] and x["rk"] == i["key"]
            ct = models.aes128_encrypt(_block(i["key"]), _block(i["pt"]))
            assert ct.hex() == "69c4e0d86a7b0430d8cdb78070b4c55a"
    assert {m for m, _ in examples} == {"aes_ctrl", "aes_round", "aes_key_step"}


def test_aes_wrong_twin_only_errs_where_the_exchanged_sbox_entries_are_used():
    good, bad = models.model_for("aes128"), models.model_for("aes128", wrong=True)
    assert models.AES_SBOX[0x52] != models.AES_SBOX[0x53]
    # FIPS C.1 never looks up 0x52 or 0x53, so the twin still gets it right;
    # a block whose first SubBytes looks up 0x52 must differ.
    c1 = bytes.fromhex(AES_KNOWN_ANSWERS[0][0] + AES_KNOWN_ANSWERS[0][1])
    assert bad.step(c1) == good.step(c1)
    hits = bytes(16) + bytes([0x52] * 16)
    assert bad.step(hits) != good.step(hits)


def test_cordic_tables_are_computed_from_their_definitions():
    spec = json.loads((REPO / "curriculum" / SPECS["cordic"] / "design_spec.json").read_text(encoding="utf-8"))
    atan = next(m for m in spec["modules"] if m["name"] == "cordic_atan")["behavior"]
    listed = [int(v) for v in atan.split("for idx 0..15: ")[1].split(". Python")[0].split(", ")]
    assert models.CORDIC_ATAN == listed
    assert models.CORDIC_K == 39797


def test_cordic_model_matches_spec_module_examples():
    for module, e in spec_examples("cordic"):
        i, x = e["inputs"], e["expected"]
        if module == "cordic_prerot":
            assert models.cordic_prerot(i["angle"]) == (x["x0"], x["z0"])
        elif module == "cordic_atan":
            assert models.CORDIC_ATAN[i["idx"]] == x["atan"]
        elif module == "cordic_out":
            assert models.cordic_out(i["x_in"], i["y_in"]) == (x["cos_out"], x["sin_out"])
        elif module == "cordic_engine":
            # The examples hold atan_val constant. One accept edge, then busy edges;
            # 17 edges from reset = accept + 16 rotations; 20 with out_ready = a
            # result transfer, a new accept and one rotation; 2 = one rotation.
            rotations = {2: 1, 17: 16, 20: 1}[e["after_cycles"]]
            table = [i["atan_val"]] * 16
            assert models.cordic_rotate(i["x0"], i["z0"], table, rotations) == (x["x"], x["y"])


def _s16(value):
    return value - 65536 if value & 0x8000 else value


def test_cordic_model_is_within_4_lsb_of_true_sine_and_cosine_over_the_circle():
    # The entry testbench's loose check, on every angle.
    worst = 0.0
    for angle in range(65536):
        cos_out, sin_out = models.cordic_sincos(angle)
        theta = _s16(angle) * 2 * math.pi / 65536
        worst = max(worst, abs(_s16(cos_out) - 16384 * math.cos(theta)),
                    abs(_s16(sin_out) - 16384 * math.sin(theta)))
    assert worst <= 4.0


def test_cordic_transaction_byte_order():
    model = models.model_for("cordic")
    result = model.step((0x4000).to_bytes(2, "little"))      # a quarter turn: sin 1, cos 0
    sin_out, cos_out = (_s16(int.from_bytes(result[k:k + 2], "little")) for k in (0, 2))
    assert abs(sin_out - 16384) <= 4 and abs(cos_out) <= 4
    wrong = models.model_for("cordic", wrong=True)
    assert models.CORDIC_ATAN[3] == 20753
    assert sum(model.step(tx) != wrong.step(tx) for tx in model.leading()) > 0


def test_fir16_matches_spec_examples():
    examples = spec_examples("fir16_sym")
    assert len(examples) == 3
    for _, e in examples:
        model = models.model_for("fir16_sym")
        sample = (e["inputs"]["in_sample"] & 0xFFFF).to_bytes(2, "little")
        for _ in range(e["after_cycles"]):
            y = int.from_bytes(model.step(sample), "little")
        assert y == e["expected"]["out_sample"]


def test_fir16_equals_the_pre_adder_form_and_resets():
    # Independent evaluation: the spec's pre-adder form over a kept window.
    h = models.FIR16_COEFFICIENTS
    assert h == tuple(reversed(h)) and sum(h) == 2048
    rng = random.Random(16)
    model = models.model_for("fir16_sym")
    window = [0] * 16
    for n in range(3000):
        if n == 1500:
            model.reset()
            window = [0] * 16
        x = rng.choice((32767, -32768)) if rng.randrange(4) == 0 else rng.randrange(-32768, 32768)
        window = [x] + window[:15]
        acc = sum(h[k] * (window[k] + window[15 - k]) for k in range(8))
        r = max(-32768, min(32767, (acc + 1024) // 2048))
        assert model.step((x & 0xFFFF).to_bytes(2, "little")) == (r & 0xFFFF).to_bytes(2, "little")


def test_fir16_leading_cases_reach_saturation_and_rounding_ties():
    model = models.model_for("fir16_sym")
    outs = [int.from_bytes(model.step(tx), "little", signed=True) for tx in model.leading()]
    assert 32767 in outs and -32768 in outs
    # The 512 impulse starts at index 34: acc = 512 * -6, so acc / 2048 = -1.5,
    # an exact tie that rounds half up to -1 (round half away would give -2).
    assert outs[34] == -1


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
    monkeypatch.setattr(hw, "run", lambda design, **kw: {
        "passed": True, "checked": 1, "requested": 1, "mismatches": 0,
        "wrong_model": False, "short_reply": None, "first_mismatch": None})
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


GOOD_SIM = "COVERAGE: 300 cycles with a result held under backpressure, 40 cycles accepting while retiring\nPASS: 1200 results matched the model, with a restart at 600 (stalled 300, overlap 40)\n"
BAD_SIM = "ERROR: transaction 17 result differs from the model\nFAIL: 1 errors, 1200 of 1200 results checked\n"


def fake_sim_tools(tmp_path, monkeypatch, *, failure=None, xsim_code=0, fault_only=False):
    """Real fixture log files and mocked process exits; no vendor invocation."""
    from hwsuite import cli
    suite = tmp_path / "suite"
    (suite / "sim").mkdir(parents=True)
    (suite / "sim" / "tb_stream_shell.v").write_text("module tb_stream_shell; endmodule\n")
    source = tmp_path / "winner.v"
    source.write_text("module sync_fifo; endmodule\n")
    monkeypatch.setattr(cli, "SUITE", suite)
    monkeypatch.setattr(cli, "rtl_sources", lambda design, winner: [source])
    monkeypatch.setattr(cli, "_tool", lambda folder, name: name)
    calls = []

    def run(cmd, cwd, log):
        tool = cmd[0]
        calls.append(tool)
        bad = not fault_only or "fault" in cwd.parts
        if bad and failure == "xelab" and tool == "xelab":
            log.write_text("ERROR: [XSIM 43-3322] elaboration failed\n")
            return 1
        if tool == "xsim":
            log.write_text(failure if bad and failure not in (None, "xelab") else (BAD_SIM if bad and fault_only else GOOD_SIM))
            return xsim_code if bad else 0
        log.write_text("INFO: successful tool process\n")
        return 0

    monkeypatch.setattr(cli, "_run", run)
    return cli, source, calls


def test_simulation_rejects_nonzero_xsim_even_after_pass(tmp_path, monkeypatch):
    cli, source, _ = fake_sim_tools(tmp_path, monkeypatch, xsim_code=7)
    passed, verdict = cli.simulate(TABLE['sync_fifo'], tmp_path, tmp_path/'sim', source)
    assert not passed and 'exit' in verdict.lower()
    receipt = json.loads((tmp_path/'sim/simulation.json').read_text())
    assert receipt['tool_exits']['xsim'] == 7 and receipt['outcome'] == 'tool_failure'


@pytest.mark.parametrize('failure,xsim_code', [
    ('xelab', 0), ('no simulator verdict\n', 0),
    ('FAIL: timeout after 0 of 1200 results\n', 0),
    ('FAIL: 1 errors, 1200 of 1200 results checked\n', 0),
    (BAD_SIM, 7),
    ('ERROR: [Common 17-345] license unavailable\n'+BAD_SIM, 0),
    (BAD_SIM+'PASS: 1200 results matched the model\n', 0),
    ('ERROR: transaction 17 result differs from the model\nFAIL: 1 errors, 1199 of 1200 results checked\n', 0),
])
def test_fault_gate_never_counts_tool_timeout_incomplete_or_unproved_failures(tmp_path, monkeypatch, failure, xsim_code):
    cli, _, _ = fake_sim_tools(tmp_path, monkeypatch, failure=failure, xsim_code=xsim_code, fault_only=True)
    from types import SimpleNamespace
    args = SimpleNamespace(design='sync_fifo', vivado=tmp_path)
    with pytest.raises(cli.SuiteError, match='simulation'):
        cli.cmd_sim(args, TABLE)
    summary = json.loads((tmp_path/'suite/build/sim_summary.json').read_text())
    assert summary['sync_fifo']['fault_caught'] is False


def test_fault_gate_requires_complete_actual_mismatch_and_successful_exits(tmp_path, monkeypatch):
    cli, _, _ = fake_sim_tools(tmp_path, monkeypatch, failure=BAD_SIM, fault_only=True)
    from types import SimpleNamespace
    cli.cmd_sim(SimpleNamespace(design='sync_fifo', vivado=tmp_path), TABLE)
    folder=tmp_path/'suite/build/sync_fifo/fault/sim'
    receipt=json.loads((folder/'simulation.json').read_text())
    assert receipt['outcome']=='behavioral_failure'
    assert receipt['tool_exits']=={'xvlog':0,'xelab':0,'xsim':0}
    assert cli._simulation_evidence(folder, 'behavioral_failure')
    (folder/'xsim.txt').write_text(BAD_SIM+'INFO: modified after receipt\n')
    assert not cli._simulation_evidence(folder, 'behavioral_failure')


def test_source_drift_during_simulation_invalidates_result(tmp_path, monkeypatch):
    cli, source, _=fake_sim_tools(tmp_path, monkeypatch)
    run=cli._run
    def changed(cmd,cwd,log):
        code=run(cmd,cwd,log)
        if cmd[0]=='xsim':source.write_text(source.read_text()+'// changed\n')
        return code
    monkeypatch.setattr(cli,'_run',changed)
    passed,_=cli.simulate(TABLE['sync_fifo'],tmp_path,tmp_path/'sim',source)
    assert not passed


def fake_program(tmp_path, monkeypatch):
    from hwsuite import cli
    bit=REPO/'evidence/2026-10-28/basys3-bitstreams-01/harness_winners/sync_fifo.bit'
    monkeypatch.setattr(cli,'SUITE',tmp_path/'suite')
    monkeypatch.setattr(cli,'_tool',lambda folder,name:name)
    monkeypatch.setattr(cli,'_run',lambda cmd,cwd,log:(log.write_text('RESULT: programmed mock_device\n'),0)[1])
    assert cli_main(['program','--design','sync_fifo','--bit',str(bit)])==0
    return cli,bit


@pytest.mark.parametrize('damage', ['short','partial','zero_mismatches','no_first_mismatch','contradictory_pass'])
def test_wrong_model_must_complete_and_show_real_mismatches(tmp_path, monkeypatch, damage):
    cli,bit=fake_program(tmp_path,monkeypatch)
    from hwsuite import hw
    result={'passed':False,'checked':4,'requested':4,'mismatches':1,'wrong_model':True,
            'short_reply':None,'first_mismatch':{'index':1,'tx':'01','expected':'00','got':'01'}}
    if damage=='short':result.update(checked=0,mismatches=0,first_mismatch=None,short_reply={'got':0,'wanted':4})
    elif damage=='partial':result['checked']=3
    elif damage=='zero_mismatches':result['mismatches']=0
    elif damage=='no_first_mismatch':result['first_mismatch']=None
    else:result['passed']=True
    monkeypatch.setattr(hw,'run',lambda design,**kw:dict(result))
    monkeypatch.setattr(hw,'format_report',lambda report:'mock hardware report')
    assert cli_main(['hw','--design','sync_fifo','--bit',str(bit),'--count','4','--wrong-model'])==1
    saved=json.loads((tmp_path/'suite/build/sync_fifo/hw/wrong_model_4.json').read_text())
    assert saved['control_accepted'] is False


def test_complete_wrong_model_control_embeds_verified_programming_receipt(tmp_path, monkeypatch):
    cli,bit=fake_program(tmp_path,monkeypatch)
    from hwsuite import hw
    result={'passed':False,'checked':4,'requested':4,'mismatches':1,'wrong_model':True,
            'short_reply':None,'first_mismatch':{'index':1,'tx':'01','expected':'00','got':'01'}}
    monkeypatch.setattr(hw,'run',lambda design,**kw:dict(result))
    monkeypatch.setattr(hw,'format_report',lambda report:'mock hardware report')
    assert cli_main(['hw','--design','sync_fifo','--bit',str(bit),'--count','4','--wrong-model'])==0
    saved=json.loads((tmp_path/'suite/build/sync_fifo/hw/wrong_model_4.json').read_text())
    assert saved['control_accepted'] and saved['programming_verified']
    assert saved['programming_receipt']['tool_exit_code']==0


def test_hardware_receipt_drift_during_run_cannot_be_claimed_verified(tmp_path, monkeypatch):
    cli,bit=fake_program(tmp_path,monkeypatch)
    from hwsuite import hw
    def run(design,**kw):
        cli._programmed().unlink()
        return {'passed':True,'checked':4,'requested':4,'mismatches':0,'wrong_model':False,
                'short_reply':None,'first_mismatch':None}
    monkeypatch.setattr(hw,'run',run)
    monkeypatch.setattr(hw,'format_report',lambda report:'mock hardware report')
    assert cli_main(['hw','--design','sync_fifo','--bit',str(bit),'--count','4'])==1
    saved=json.loads((tmp_path/'suite/build/sync_fifo/hw/model_4.json').read_text())
    assert not saved['programming_verified'] and not saved['control_accepted']
