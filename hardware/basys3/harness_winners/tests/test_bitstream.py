"""Tests for .bit header parsing and the per-instance utilization parser."""
from pathlib import Path
import sys

import pytest

SUITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SUITE))

from hwsuite import reports        # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"
PREAMBLE = b"\x00\x09\x0f\xf0\x0f\xf0\x0f\xf0\x0f\xf0\x00\x00\x01"


def bit_file(path, time, payload, design="stream_shell;COMPRESS=TRUE"):
    def field(key, text):
        raw = text.encode() + b"\x00"
        return key.encode() + len(raw).to_bytes(2, "big") + raw
    body = (PREAMBLE + field("a", design) + field("b", "7a35tcpg236") + field("c", "2026/10/28")
            + field("d", time) + b"e" + len(payload).to_bytes(4, "big") + payload)
    path.write_bytes(body)
    return path


def test_header_fields_and_payload_are_separated(tmp_path):
    fields = reports.bitstream_fields(bit_file(tmp_path / "a.bit", "19:45:25", b"\xaa\x99\x55\x66" * 8))
    assert fields["a"].startswith("stream_shell") and fields["b"] == "7a35tcpg236"
    assert fields["d"] == "19:45:25" and fields["payload"] == b"\xaa\x99\x55\x66" * 8


def test_same_payload_different_build_time_compares_equal(tmp_path):
    one = bit_file(tmp_path / "one.bit", "19:45:25", b"\x01\x02\x03" * 100)
    two = bit_file(tmp_path / "two.bit", "19:50:05", b"\x01\x02\x03" * 100)
    assert one.read_bytes() != two.read_bytes()
    assert reports.bitstream_payload_sha256(one) == reports.bitstream_payload_sha256(two)


def test_one_changed_payload_byte_is_detected(tmp_path):
    one = bit_file(tmp_path / "one.bit", "19:45:25", b"\x01\x02\x03" * 100)
    two = bit_file(tmp_path / "two.bit", "19:45:25", b"\x01\x02\x03" * 99 + b"\x01\x02\x04")
    assert reports.bitstream_payload_sha256(one) != reports.bitstream_payload_sha256(two)


@pytest.mark.parametrize("damage", ["not a bit file", "truncated"])
def test_malformed_bitstreams_are_rejected(tmp_path, damage):
    path = bit_file(tmp_path / "x.bit", "19:45:25", b"\x00" * 64)
    if damage == "not a bit file":
        path.write_bytes(b"hello world, definitely not a bitstream")
    else:
        path.write_bytes(path.read_bytes()[:-10])
    with pytest.raises(ValueError):
        reports.bitstream_payload_sha256(path)


def test_winner_utilization_from_real_report():
    assert reports.winner_utilization(FIXTURES / "utilization_winner_sync_fifo.rpt") == {"luts": 21, "ffs": 13, "dsps": 0}


def test_winner_utilization_rejects_a_report_without_the_table(tmp_path):
    report = tmp_path / "empty.rpt"
    report.write_text("| Design : stream_shell\n")
    with pytest.raises(ValueError, match="Slice LUTs"):
        reports.winner_utilization(report)
