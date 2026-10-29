"""run.py doctor: an environment check that never runs a design or a model."""
from autortl import doctor
import run


def fake_env(monkeypatch, *, tools=True, codex=True, logged_in=True):
    monkeypatch.setattr(doctor.shutil, "which", lambda name: f"/bin/{name}" if (
        (tools and name.split(".")[0] in doctor.TOOLS) or (codex and name == "codex")) else None)
    monkeypatch.delenv("AUTORTL_CODEX_BIN", raising=False)

    def probe(cmd, timeout=60):
        if cmd[-1] == "--version" and "xvlog" in cmd[0]:
            return 0, "Vivado Simulator v2025.2"
        if cmd[-1] == "--version":
            return 0, "codex-cli 1.0"
        if cmd[-2:] == ["login", "status"]:
            return (0, "Logged in using ChatGPT") if logged_in else (1, "Not logged in")
        raise AssertionError(f"unexpected command {cmd}")

    monkeypatch.setattr(doctor, "_probe", probe)


def by_name(checks):
    return {c.name: c for c in checks}


def test_ready_machine_passes(monkeypatch, tmp_path, capsys):
    fake_env(monkeypatch)
    assert doctor.main({}, tmp_path) == 0
    assert "ready: every required check passed" in capsys.readouterr().out


def test_missing_vivado_names_the_flag_to_pass(monkeypatch, tmp_path):
    fake_env(monkeypatch, tools=False)
    checks = by_name(doctor.run_checks({}, tmp_path))
    assert checks["xvlog"].status == "MISSING" and "--xvlog" in checks["xvlog"].fix
    assert doctor.main({}, tmp_path) == 1


def test_missing_login_is_reported_with_the_fix(monkeypatch, tmp_path):
    fake_env(monkeypatch, logged_in=False)
    checks = by_name(doctor.run_checks({}, tmp_path))
    assert checks["codex login"].status == "MISSING" and "codex login" in checks["codex login"].fix


def test_explicit_tool_paths_are_used(monkeypatch, tmp_path):
    fake_env(monkeypatch, tools=False)
    paths = {}
    for name in doctor.TOOLS:
        path = tmp_path / f"{name}.bat"
        path.write_text("")
        paths[name] = str(path)
    checks = by_name(doctor.run_checks(paths, tmp_path))
    assert all(checks[name].status == "OK" for name in doctor.TOOLS)


def test_cli_dispatches_without_building_an_orchestrator(monkeypatch, tmp_path):
    seen = {}
    monkeypatch.setattr(doctor, "main", lambda paths, root: seen.update(paths=paths) or 0)
    monkeypatch.setattr(run, "Orchestrator", lambda *a, **k: (_ for _ in ()).throw(AssertionError("no run")))
    assert run.main(["doctor", "--xvlog", "X"]) == 0
    assert seen["paths"]["xvlog"] == "X"
