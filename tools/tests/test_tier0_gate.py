"""The tier0 gate runner keeps campaign14's source selection, budgets and command."""
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import tier0_gate as gate  # noqa: E402


def test_identity_selection(tmp_path):
    for rel in ("autortl/a.py", "autortl/sub/b.v", "tests/t.py", "data/x.yaml", ".claude/skills/s.md",
                "curriculum/c.json", "llm/l.sv", "scripts/s.py", "run.py"):
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rel)
    for rel in ("autortl/__pycache__/a.cpython-312.pyc", "autortl/__pycache__/a.py", "autortl/notes.txt",
                "tools/gate.py", "evidence/e.json", "hardware/h.v"):
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rel)
    found = gate.identities(tmp_path)
    assert sorted(found) == sorted(["autortl/a.py", "autortl/sub/b.v", "tests/t.py", "data/x.yaml",
                                    ".claude/skills/s.md", "curriculum/c.json", "llm/l.sv", "scripts/s.py", "run.py"])
    assert found["run.py"] == gate.sha(tmp_path / "run.py")


def test_this_runner_is_outside_the_identity():
    # Writing or editing the gate must not change what it freezes.
    assert "tools" not in gate.SELECTION


def test_bench_command_matches_campaign14(tmp_path):
    out = tmp_path / "run"
    command = gate.bench_command("PY", out)
    assert command == ["PY", "run.py", "bench", "--tier", "0", "--iterations", "1", "--best-of-n", "1",
                       "--max-llm-calls", "16", "--max-vivado-minutes", "20", "--max-wall-minutes", "30",
                       "--max-infra-retries", "1", "--target-part", "xc7a35tcpg236-1", "--target-freq-mhz", "100",
                       "--output-dir", str(out),
                       "--vivado", "C:/AMDDesignTools/2025.2/Vivado/bin/vivado.bat",
                       "--xvlog", "C:/AMDDesignTools/2025.2/Vivado/bin/xvlog.bat",
                       "--xelab", "C:/AMDDesignTools/2025.2/Vivado/bin/xelab.bat",
                       "--xsim", "C:/AMDDesignTools/2025.2/Vivado/bin/xsim.bat"]


def test_an_earlier_attempt_is_never_overwritten(tmp_path, monkeypatch):
    monkeypatch.setattr(gate, "ROOT", tmp_path)
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "gate-01-prelaunch.json").write_text("{}")
    with pytest.raises(SystemExit, match="never overwritten"):
        gate.main(["--name", "gate-01"])
