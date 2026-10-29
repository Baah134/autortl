"""Regenerate fixtures/evidence: small copies of each real manifest layout.

Each layout mirrors one found under evidence/ (named below). The digests are
computed from the fixture bytes, so the fixture tree is self-consistent; the
expected status of every claim is pinned in test_evidence_audit.py.
Run from anywhere: python tools/tests/make_fixtures.py
"""
import hashlib
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
OUT = HERE / "fixtures" / "evidence"
# Root sources the tests commit in two versions; see test_evidence_audit.py.
V1 = b"module core;\nendmodule\n"
V2 = b"module core(input clk);\nendmodule\n"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def put(rel, data):
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return sha(data)


def put_json(rel, value, **dump):
    put(rel, (json.dumps(value, **dump) + "\n").encode("utf-8"))


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    # Flat map, like the harness archivers' archive-manifest.json.
    put_json("archive-a/archive-manifest.json", {
        "xvlog.log": put("archive-a/xvlog.log", b"INFO: [VRFC 10-2263] Analyzing Verilog file\r\n"),
        "sub/xelab.pb": put("archive-a/sub/xelab.pb", b"\x00\x01binary\x00"),
        "result.json": (put("archive-a/result.json", b'{"passed": true}\n'), sha(b'{"passed": false}\n'))[1],
        "gone/xsim.jou": sha(b"lost journal\n"),
    }, indent=2)
    # Qualification case list: absolute Windows paths of the run folder under
    # logs/, archived into a folder with a different name (admission/).
    run = "C:\\Users\\someone\\autortl-work\\logs\\cases-run-01\\reference\\"
    put_json("cases-run-01/admission/manifest.json", {"schema_version": 1, "top": "core_tb", "cases": [{
        "name": "reference", "expected_verdict": "TEST PASSED", "files": [
            {"path": run + "core.v", "sha256": put("cases-run-01/admission/reference/core.v", b"module core; endmodule\n")},
            {"path": run + "core_tb.v", "sha256": put("cases-run-01/admission/reference/core_tb.v", b"module core_tb; endmodule\n")},
            {"path": run + "lost.v", "sha256": sha(b"lost\n")}]}]}, indent=1)
    # Board manifest as PowerShell writes it: UTF-8 BOM and CRLF, a sources
    # binding with a backslash path, and a digest of a file kept elsewhere.
    board = {"schema": 2, "tool": "Vivado 2025.2",
             "sources": {"src\\core.v": sha(V2.replace(b"\n", b"\r\n")), "src/old.v": sha(V1),
                         "src/never.v": sha(b"never committed\n")},
             "bitstream_sha256": sha(b"bitstream kept elsewhere\n"),
             "files": {"timing.rpt": put("board-01/timing.rpt", b"WNS 4.529\r\n")}}
    put("board-01/manifest.json", b"\xef\xbb\xbf" + json.dumps(board, indent=4).replace("\n", "\r\n").encode() + b"\r\n")
    # Relocation list: uppercase digests, and one path that leaves the repository.
    put_json("move/relocation-manifest.json", [{"path": "src/core.v", "sha256": sha(V1).upper()},
                                               {"path": "..\\outside.txt", "sha256": sha(b"x").upper()}], indent=2)
    # Reference cases: digests without paths.
    put_json("counter-ref/manifest.json", [{
        "case": "original", "top": "counter_tb", "expected_pass": True,
        "source_sha256": put("counter-ref/original/counter.v", b"module counter; endmodule\n"),
        "tb_sha256": sha(b"no such testbench\n")}], indent=2)
    # A source freeze taken before a test run: repository paths, no "manifest" in the name.
    put_json("freeze/proposal-fixes-source-freeze-01.json", {"src/old.v": sha(V1), "src/core.v": sha(V1)}, indent=2)
    # A manifest with digests the parser cannot attribute to any file.
    put_json("mixed/manifest.json", {"files": {"a.txt": put("mixed/a.txt", b"a\n")},
                                     "build_id": sha(b"build"), "seen": [sha(b"seen")]}, indent=2)
    # No digests at all, and a manifest that is not valid JSON.
    put_json("plain/manifest.json", [{"case": "latency0", "expected_pass": True}])
    put("broken/archive-manifest.json", b'{"a.txt": "unterminated\n')


if __name__ == "__main__":
    main()
