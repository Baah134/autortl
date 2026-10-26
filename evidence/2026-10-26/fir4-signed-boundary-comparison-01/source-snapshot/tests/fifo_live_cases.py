"""Prepare original/repaired FIFO fixtures and true behavioral mutants.

The helper never launches Vivado. Use --source for a candidate reference copy.
The legacy combinational-loop source is not a qualification mutant.
"""
import argparse
import hashlib
import json
from pathlib import Path


def save(output: Path, source: Path | None = None):
    root = Path(__file__).resolve().parents[1]
    source = source or root / ".claude/skills/cdc/snippets/async_fifo_skeleton.v"
    rtl = source.read_text()
    if "assign full = (wptr_gray_n ==" in rtl:
        raise ValueError("reference still has combinational full/next-pointer loop; repair it before qualification")
    if rtl.count("assign full = (wptr_gray ==") != 1:
        raise ValueError("review full-comparator mutation for changed source")
    data_line = "rd_data <= mem[rptr_bin[AW-1:0]];"
    if rtl.count(data_line) != 1:
        raise ValueError("review data mutation for changed source")
    variants = [("control", rtl, True),
                ("bad_data", rtl.replace(data_line, "rd_data <= mem[rptr_bin[AW-1:0]] ^ 1'b1;"), False),
                ("bad_full", rtl.replace("assign full = (wptr_gray ==", "assign full = (wptr_gray !="), False)]
    template = (root / "tests/fixtures/async_fifo_tb.v").read_text()
    manifest = []
    for aw in (2, 4):
        for variant, content, expected in variants:
            folder = output / f"aw{aw}_{variant}"
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "async_fifo.v").write_text("`timescale 1ns/1ps\n" + content)
            (folder / "async_fifo_tb.v").write_text(template.replace("localparam AW = 2;", f"localparam AW = {aw};"))
            manifest.append({"case": folder.name, "top": "async_fifo_tb", "expected_pass": expected,
                "source_sha256": hashlib.sha256((folder / "async_fifo.v").read_bytes()).hexdigest(),
                "tb_sha256": hashlib.sha256((folder / "async_fifo_tb.v").read_bytes()).hexdigest()})
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source", type=Path)
    args = parser.parse_args()
    print(json.dumps(save(args.output, args.source), indent=2))
