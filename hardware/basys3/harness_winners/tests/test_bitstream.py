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


def receipt_setup(tmp_path, monkeypatch):
    from hwsuite import cli,designs
    from types import SimpleNamespace
    design=designs.load()['sync_fifo']
    bit=bit_file(tmp_path/'image.bit','12:00:00',b'\x01\x02\x03'*100)
    args=SimpleNamespace(bit=bit,design=design.name,vivado=tmp_path)
    monkeypatch.setattr(cli,'SUITE',tmp_path/'suite')
    monkeypatch.setattr(cli,'_tool',lambda folder,name:name)
    monkeypatch.setattr(cli,'_run',lambda cmd,cwd,log:(log.write_text('RESULT: programmed mock_device\n'),0)[1])
    return cli,design,args,bit


def test_existing_file_is_not_evidence_it_was_programmed(tmp_path, monkeypatch):
    cli,design,args,_=receipt_setup(tmp_path,monkeypatch)
    with pytest.raises(cli.SuiteError,match='programming receipt'):
        cli._on_board(args,design)


def test_legacy_record_is_not_retroactively_a_successful_programming_receipt(tmp_path, monkeypatch):
    import json
    cli,design,args,bit=receipt_setup(tmp_path,monkeypatch)
    cli._programmed().parent.mkdir(parents=True)
    cli._programmed().write_text(json.dumps({'design':design.name,'bitstream':str(bit),
                                           'payload_sha256':reports.bitstream_payload_sha256(bit)}))
    with pytest.raises(cli.SuiteError,match='programming receipt'):
        cli._on_board(args,design)


@pytest.mark.parametrize('damage',['exit','console','payload','schema'])
def test_corrupt_programming_receipts_are_rejected(tmp_path, monkeypatch, damage):
    import json
    cli,design,args,bit=receipt_setup(tmp_path,monkeypatch)
    cli.cmd_program(args,{design.name:design})
    record=json.loads(cli._programmed().read_text())
    if damage=='exit':record['tool_exit_code']=1
    elif damage=='console':record['console_sha256']='0'*64
    elif damage=='payload':record['payload_sha256']='0'*64
    else:record.pop('schema',None)
    cli._programmed().write_text(json.dumps(record))
    with pytest.raises(cli.SuiteError,match='programming receipt'):
        cli._on_board(args,design)


def test_programming_receipt_binds_successful_exit_console_and_payload(tmp_path, monkeypatch):
    import hashlib,json
    cli,design,args,bit=receipt_setup(tmp_path,monkeypatch)
    cli.cmd_program(args,{design.name:design})
    record=json.loads(cli._programmed().read_text())
    assert record['schema']==1 and record['tool_exit_code']==0
    assert record['console_sha256']==hashlib.sha256(Path(record['console_path']).read_bytes()).hexdigest()
    assert cli._on_board(args,design)==reports.bitstream_payload_sha256(bit)
    # A .bit timestamp is outside its programmed configuration payload.
    bit_file(bit,'12:01:00',b'\x01\x02\x03'*100)
    assert cli._on_board(args,design)==record['payload_sha256']


def test_bitstream_changed_while_programming_cannot_create_receipt(tmp_path, monkeypatch):
    cli,design,args,bit=receipt_setup(tmp_path,monkeypatch)
    def changed(cmd,cwd,log):
        log.write_text('RESULT: programmed mock_device\n')
        bit_file(bit,'12:01:00',b'\xff'*300)
        return 0
    monkeypatch.setattr(cli,'_run',changed)
    with pytest.raises(cli.SuiteError,match='changed'):
        cli.cmd_program(args,{design.name:design})
    assert not cli._programmed().exists()
