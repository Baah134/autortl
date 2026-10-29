"""Write manifest.json for the archived Basys 3 bitstreams, checking each claim.

Each .bit here was copied unchanged from the board build folder that produced
the tested image. Every file's full SHA-256 must equal the digest that its
board evidence recorded, and for the harness winners the configuration
payload (the bitstream without its build-time header) must also equal the
payload that was actually programmed and tested.
"""
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "hardware" / "basys3" / "harness_winners"))
from hwsuite.reports import bitstream_payload_sha256  # noqa: E402

BOARD = {
    "basys3_uart_echo_v02.bit": ("evidence/2026-10-28/basys3-uart-echo-02/manifest.json", None),
    "basys3_fir4_shell.bit": ("evidence/2026-10-28/basys3-fir4-01/manifest.json", None),
}
WINNERS = "evidence/2026-10-28/basys3-harness-winners-01/summary.json"


def main():
    summary = json.loads((ROOT / WINNERS).read_text(encoding="utf-8"))
    files, bitstreams = {}, {}
    for path in sorted(HERE.rglob("*.bit")):
        rel = path.relative_to(HERE).as_posix()
        full = hashlib.sha256(path.read_bytes()).hexdigest()
        payload = bitstream_payload_sha256(path)
        if rel in BOARD:
            source = BOARD[rel][0]
            recorded = json.loads((ROOT / source).read_text(encoding="utf-8-sig"))["bitstream_sha256"]
            checks = {"bitstream_sha256": recorded == full}
        else:
            design = Path(rel).stem
            source = f"{WINNERS} [{design}]"
            entry = summary[design]
            checks = {"bitstream_sha256": entry["bitstream_sha256"] == full,
                      "bitstream_payload_sha256": entry["bitstream_payload_sha256"] == payload}
        if not all(checks.values()):
            raise SystemExit(f"{rel} does not match its recorded digest: {checks}")
        files[rel] = full
        bitstreams[rel] = {"bytes": path.stat().st_size, "configuration_payload_digest": payload,
                           "recorded_by": source, "checked": sorted(checks)}
    manifest = {"schema": 1, "part": "xc7a35tcpg236-1", "board": "Digilent Basys 3",
                "tool": "Vivado 2025.2", "files": files, "bitstreams": bitstreams}
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(files)} bitstreams match their recorded digests")


if __name__ == "__main__":
    main()
