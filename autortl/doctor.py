"""Environment check: is this machine ready to run AutoRTL?

    python run.py doctor [--vivado PATH --xvlog PATH --xelab PATH --xsim PATH]

Each check reports OK, MISSING or WARN with the exact fix. Only local
commands run (version and login-status queries); nothing is sent to a model
and no design is touched. The exit code is 0 when every required check
passes, so scripts and CI can gate on it.
"""
from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import urllib.parse

TOOLS = ("vivado", "xvlog", "xelab", "xsim")


@dataclass
class Check:
    name: str
    status: str          # OK | MISSING | WARN
    detail: str
    fix: str = ""
    required: bool = True


def _probe(cmd, timeout=60):
    try:
        with tempfile.TemporaryDirectory(prefix="autortl-doctor-") as scratch:  # xvlog writes logs to its cwd
            out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                                 timeout=timeout, shell=False, cwd=scratch)
        return out.returncode, (out.stdout + out.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, str(exc)


def _resolve(value, name):
    if value:
        return value if Path(value).is_file() or shutil.which(value) else None
    for candidate in (name, name + ".bat", name + ".exe"):
        found = shutil.which(candidate)
        if found:
            return found
    return None


def python_check():
    ok = sys.version_info >= (3, 12)
    return Check("python", "OK" if ok else "MISSING", sys.version.split()[0],
                 "" if ok else "Install Python 3.12 or newer")


def package_checks():
    checks = []
    for module, package, required in (("yaml", "pyyaml", True), ("pytest", "pytest", False)):
        found = importlib.util.find_spec(module) is not None
        checks.append(Check(package, "OK" if found else ("MISSING" if required else "WARN"),
                            "installed" if found else "not installed",
                            "" if found else "python -m pip install -r requirements.txt", required))
    return checks


def tool_checks(paths):
    checks = []
    for name in TOOLS:
        path = _resolve(paths.get(name), name)
        if not path:
            checks.append(Check(name, "MISSING", "not found on PATH" + (f" or at {paths[name]}" if paths.get(name) else ""),
                                f"Pass --{name} <Vivado>/bin/{name}.bat or put Vivado's bin folder on PATH"))
            continue
        if name == "xvlog":
            rc, out = _probe([path, "--version"])
            line = out.splitlines()[0] if out else ""
            ok = rc == 0 and "Vivado Simulator" in line
            checks.append(Check(name, "OK" if ok else "WARN", f"{path}: {line or out[:120]}",
                                "" if ok else "Check that this is Vivado's xvlog"))
        else:
            checks.append(Check(name, "OK", path))
    return checks


def model_check():
    executable = os.environ.get("AUTORTL_CODEX_BIN") or shutil.which("codex")
    if not executable:
        return [Check("codex", "MISSING", "Codex CLI not found",
                      "Install the Codex CLI, or set AUTORTL_CODEX_BIN to its executable")]
    rc, version = _probe([executable, "--version"], timeout=30)
    checks = [Check("codex", "OK" if rc == 0 else "MISSING", f"{executable}: {version.splitlines()[0] if version else ''}",
                    "" if rc == 0 else "Check AUTORTL_CODEX_BIN points at a working Codex CLI")]
    if rc == 0:
        rc, status = _probe([executable, "login", "status"], timeout=30)
        logged = rc == 0 and "logged in" in status.lower() and "not logged in" not in status.lower()
        checks.append(Check("codex login", "OK" if logged else "MISSING", status.splitlines()[0] if status else "no status",
                            "" if logged else "Run `codex login` (model-driven runs need it; tests and the audit do not)"))
    return checks


def openai_check():
    """Optional alternative backend; reports presence of the key, never its value."""
    if not (os.environ.get("AUTORTL_OPENAI_API_KEY") or "").strip():
        return Check("openai", "WARN", "AUTORTL_OPENAI_API_KEY not set (optional alternative to Codex)",
                     "To use an OpenAI-compatible API, set AUTORTL_OPENAI_API_KEY and optionally "
                     "AUTORTL_OPENAI_BASE_URL / AUTORTL_OPENAI_MODEL, then run with --model openai.<model>",
                     required=False)
    base = (os.environ.get("AUTORTL_OPENAI_BASE_URL") or "").strip()
    try:
        host = urllib.parse.urlsplit(base).hostname if base else "api.openai.com (default)"
    except ValueError:
        host = None
    model = (os.environ.get("AUTORTL_OPENAI_MODEL") or "").strip()
    return Check("openai", "OK", f"AUTORTL_OPENAI_API_KEY is set; endpoint host {host or 'invalid URL'}; "
                 + (f"default model {model}" if model else "no AUTORTL_OPENAI_MODEL (name the model as openai.<model>)"),
                 required=False)


def workspace_check(root):
    try:
        with tempfile.NamedTemporaryFile(dir=root, prefix=".doctor-", delete=True):
            pass
        return Check("workspace", "OK", f"{root} is writable")
    except OSError as exc:
        return Check("workspace", "MISSING", f"{root}: {exc}", "Run from a writable checkout")


def run_checks(paths, root):
    return [python_check(), *package_checks(), *tool_checks(paths), *model_check(), openai_check(), workspace_check(root)]


def render(checks):
    width = max(len(c.name) for c in checks)
    lines = [f"{c.status:<7} {c.name:<{width}}  {c.detail}" + (f"\n        fix: {c.fix}" if c.fix else "")
             for c in checks]
    failed = [c for c in checks if c.required and c.status == "MISSING"]
    lines.append("")
    lines.append("ready: every required check passed" if not failed
                 else f"not ready: {len(failed)} required check(s) missing")
    return "\n".join(lines)


def main(paths, root=Path.cwd()):
    checks = run_checks(paths, Path(root))
    print(render(checks))
    return 0 if not any(c.required and c.status == "MISSING" for c in checks) else 1
