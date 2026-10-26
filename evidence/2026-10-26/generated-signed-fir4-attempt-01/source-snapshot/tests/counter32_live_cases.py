"""Write counter32 reference-checker mutation fixtures; never run tools itself."""
from pathlib import Path
import argparse
import hashlib
import json


def save(output: Path):
    root = Path(__file__).resolve().parents[1]
    source = (root / "curriculum/tier0/counter/counter.v").read_text()
    tb = (root / "curriculum/tier0/counter/counter_tb.v").read_text()
    marker = "    // registered threshold flags: one cycle late AND extra FFs"
    if source.count(marker) != 1:
        raise ValueError("counter fixture changed: review mutation locations")
    prefix, flags = source.split(marker)
    if flags.count("always @(posedge clk)") != 1:
        raise ValueError("counter flag block no longer matches mutation")
    combinational = prefix + marker + flags.replace("always @(posedge clk)", "always @(*)", 1)
    if source.count("(count < THRESH_") != 3:
        raise ValueError("counter comparisons no longer match mutation")
    truncated = source.replace("(count < THRESH_", "(count[9:0] < THRESH_")
    disabled_marker = "            end\n        end\n    end\n"
    if prefix.count(disabled_marker) != 1:
        raise ValueError("counter enable block no longer matches mutation")
    clear_disabled = prefix.replace(disabled_marker,
        "            end else begin\n                overflow <= 1'b0;\n            end\n        end\n    end\n", 1) + marker + flags
    asynchronous = source.replace("always @(posedge clk)", "always @(posedge clk or posedge rst)")
    variants = [("original", source, True), ("combinational_flags", combinational, False),
                ("truncated_comparisons", truncated, False),
                ("disabled_overflow_clear", clear_disabled, False),
                ("asynchronous_reset", asynchronous, False)]
    output.mkdir(parents=True, exist_ok=True)
    manifest = []
    for name, rtl, expected in variants:
        folder = output / name
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "counter.v").write_text(rtl)
        (folder / "counter_tb.v").write_text(tb)
        manifest.append({"case": name, "top": "counter_tb", "expected_pass": expected,
                         "source_sha256": hashlib.sha256((folder / "counter.v").read_bytes()).hexdigest(),
                         "tb_sha256": hashlib.sha256((folder / "counter_tb.v").read_bytes()).hexdigest()})
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(save(parser.parse_args().output), indent=2))
