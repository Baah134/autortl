"""Copy real control logs into fixtures with local paths replaced."""
import re
import sys
from pathlib import Path

controls, fixtures = Path(sys.argv[1]), Path(sys.argv[2])
BS = re.escape("\\")
DATASET = re.compile(r"[A-Za-z]:" + BS + r"\S*?" + BS + "dataset_spec-to-rtl" + BS)
CANDIDATE = re.compile(r"[A-Za-z]:" + BS + r"\S*?" + BS + r"(syntax|broken|reference|hang)" + BS)


def san(path):
    text = DATASET.sub("<dataset>/", path.read_text(encoding="utf-8"))
    text = CANDIDATE.sub("<candidate>/", text)
    assert "Users" not in text, text
    return text


for src, dst in [("Prob035_count1to10/reference/grade/sim.log", "sim_pass.log"),
                 ("Prob035_count1to10/broken/grade/sim.log", "sim_fail.log"),
                 ("Prob035_count1to10/syntax/grade/compile.log", "compile_syntax.log")]:
    (fixtures / dst).write_text(san(controls / src), encoding="utf-8", newline="\n")
    print("==", dst)
    print((fixtures / dst).read_text(encoding="utf-8"))
