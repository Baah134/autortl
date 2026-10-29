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


def test_bench_command_matches_campaign14(tmp_path, monkeypatch):
    monkeypatch.delenv("AUTORTL_VIVADO_BIN", raising=False)
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


def test_bench_command_takes_the_vivado_folder_from_the_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTORTL_VIVADO_BIN", r"D:\Xilinx\Vivado\bin")
    command = gate.bench_command("PY", tmp_path / "run")
    assert command[-8:] == ["--vivado", "D:/Xilinx/Vivado/bin/vivado.bat", "--xvlog", "D:/Xilinx/Vivado/bin/xvlog.bat",
                            "--xelab", "D:/Xilinx/Vivado/bin/xelab.bat", "--xsim", "D:/Xilinx/Vivado/bin/xsim.bat"]


def test_the_vivado_bin_option_overrides_the_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTORTL_VIVADO_BIN", "D:/ignored")
    command = gate.bench_command("PY", tmp_path / "run", "E:/Vivado/bin/")
    assert command[-8:] == ["--vivado", "E:/Vivado/bin/vivado.bat", "--xvlog", "E:/Vivado/bin/xvlog.bat",
                            "--xelab", "E:/Vivado/bin/xelab.bat", "--xsim", "E:/Vivado/bin/xsim.bat"]


def test_main_passes_the_vivado_bin_option_to_the_bench(tmp_path, monkeypatch):
    # Stop main right after it builds the command, before any process starts.
    seen = []
    def stop(python, out, vivado=None):
        seen.append(vivado)
        raise SystemExit("stopped")
    monkeypatch.setattr(gate, "ROOT", tmp_path)
    monkeypatch.setattr(gate, "identities", lambda root=None: {})
    monkeypatch.setattr(gate, "bench_command", stop)
    monkeypatch.setattr(gate.subprocess, "run", lambda *a, **k: type("R", (), {"returncode": 0, "stdout": "1 passed"})())
    monkeypatch.syspath_prepend(str(gate.Path(gate.__file__).resolve().parents[1]))
    import curriculum.runner
    monkeypatch.setattr(curriculum.runner, "_history", lambda: [])
    (tmp_path / "logs").mkdir()
    with pytest.raises(SystemExit, match="stopped"):
        gate.main(["--name", "gate-02", "--vivado-bin", "E:/Vivado/bin"])
    assert seen == ["E:/Vivado/bin"]


def test_an_earlier_attempt_is_never_overwritten(tmp_path, monkeypatch):
    monkeypatch.setattr(gate, "ROOT", tmp_path)
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "gate-01-prelaunch.json").write_text("{}")
    with pytest.raises(SystemExit, match="never overwritten"):
        gate.main(["--name", "gate-01"])
