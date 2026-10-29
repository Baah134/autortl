"""Parsers for the Vivado outputs the suite archives."""
from __future__ import annotations

import re
from pathlib import Path

HIER_COLUMNS = ("total_luts", "logic_luts", "lutrams", "srls", "ffs", "ramb36", "ramb18", "dsps")


def instance_utilization(report: Path, instance: str) -> dict:
    """Resources of one instance from `report_utilization -hierarchical`.

    Rows look like `|   u_winner   | signed_fir4 |  49 |  49 | 0 | 0 | 67 | 0 | 0 | 0 |`.
    The instance must appear exactly once.
    """
    rows = []
    for line in report.read_text(encoding="utf-8", errors="replace").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 2 + len(HIER_COLUMNS) and cells[0] == instance:
            rows.append(cells)
    if len(rows) != 1:
        raise ValueError(f"{report.name}: expected one row for instance {instance!r}, found {len(rows)}")
    cells = rows[0]
    values = {}
    for name, text in zip(HIER_COLUMNS, cells[2:]):
        if not re.fullmatch(r"\d+(\.\d+)?", text):
            raise ValueError(f"{report.name}: {instance} {name} is not a number: {text!r}")
        values[name] = float(text) if "." in text else int(text)
    return {"instance": instance, "module": cells[1], **values}


def build_result(console: Path) -> dict:
    """WNS/WHS from the `RESULT: WNS=... ns WHS=... ns` line that build.tcl prints."""
    text = console.read_text(encoding="utf-8", errors="replace")
    matches = re.findall(r"^RESULT: WNS=(-?\d+(?:\.\d+)?) ns WHS=(-?\d+(?:\.\d+)?) ns$", text, re.MULTILINE)
    if len(matches) != 1:
        raise ValueError(f"{console.name}: expected one timing RESULT line, found {len(matches)}")
    wns, whs = (float(v) for v in matches[0])
    return {"wns_ns": wns, "whs_ns": whs}


def bitstream_fields(path: Path) -> dict:
    """Split a Xilinx .bit file into its header fields and configuration payload.

    Layout: a 13-byte preamble, then keyed fields 'a' design, 'b' part,
    'c' date, 'd' time (2-byte big-endian length each) and 'e' payload
    (4-byte length). The date and time differ on every build, so two builds
    of the same netlist are compared by payload, not by file hash.
    """
    data = path.read_bytes()
    if data[:2] != b"\x00\x09" or len(data) < 13:
        raise ValueError(f"{path.name}: not a .bit file")
    pos, fields = 13, {}
    while pos < len(data):
        key = chr(data[pos])
        pos += 1
        if key in "abcd":
            length = int.from_bytes(data[pos:pos + 2], "big")
            fields[key] = data[pos + 2:pos + 2 + length].rstrip(b"\x00").decode("ascii", "replace")
            pos += 2 + length
        elif key == "e":
            length = int.from_bytes(data[pos:pos + 4], "big")
            payload = data[pos + 4:pos + 4 + length]
            if len(payload) != length:
                raise ValueError(f"{path.name}: payload truncated")
            fields["payload"] = payload
            return fields
        else:
            raise ValueError(f"{path.name}: unexpected field {key!r}")
    raise ValueError(f"{path.name}: no payload field")


def bitstream_payload_sha256(path: Path) -> str:
    import hashlib
    return hashlib.sha256(bitstream_fields(path)["payload"]).hexdigest()


def winner_utilization(report: Path) -> dict:
    """Slice LUTs, Slice Registers and DSPs from `report_utilization -cells`."""
    text = report.read_text(encoding="utf-8", errors="replace")
    values = {}
    for key, label in (("luts", "Slice LUTs"), ("ffs", "Slice Registers"), ("dsps", "DSPs")):
        found = re.findall(rf"^\| {re.escape(label)}\s*\|\s*(\d+)\s*\|", text, re.MULTILINE)
        if not found or len(set(found)) != 1:
            raise ValueError(f"{report.name}: cannot read a single {label} value")
        values[key] = int(found[0])
    return values


def build_warnings(log: Path) -> int:
    """Count WARNING, CRITICAL WARNING and ERROR messages in a Vivado log."""
    return sum(1 for line in log.read_text(encoding="utf-8", errors="replace").splitlines()
               if re.match(r"^(WARNING|CRITICAL WARNING|ERROR):", line))
