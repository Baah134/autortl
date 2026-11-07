"""The gate must prune other checkouts without changing its source identity."""
import hashlib
import errno
import os
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tier0_gate as gate  # noqa: E402


def link_or_skip(create):
    """Only skip missing OS privileges, not unexpected link/fixture failures."""
    try:
        create()
    except OSError as error:
        if getattr(error, "winerror", None) in (5, 1314) or error.errno in (errno.EACCES, errno.EPERM):
            pytest.skip(f"OS does not permit creating this test link: {error}")
        raise


def legacy_identities(root):
    """Small independent copy of the pre-pruning selection, not a saved module."""
    selected = {}
    for name in ("autortl", "llm", "tests", "curriculum", "scripts", "data", ".claude"):
        for path in (root / name).rglob("*"):
            relative = path.relative_to(root)
            if relative.parts[:2] == (".claude", "worktrees"):
                continue
            if (path.is_file() and path.suffix in (".py", ".v", ".sv", ".json", ".yaml", ".md")
                    and "__pycache__" not in path.parts):
                selected[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    selected["run.py"] = hashlib.sha256((root / "run.py").read_bytes()).hexdigest()
    return dict(sorted(selected.items()))


def source_tree(root):
    files = {
        "run.py": b"run\r\n",
        "autortl/a.py": b"a\r\nb",
        ".claude/skills/x/SKILL.md": b"skill",
        ".claude/worktrees/agent/nested/a.py": b"excluded",
        ".claude/worktrees/agent/nested/more/data.json": b"{}",
        "tests/__pycache__/ignored.py": b"excluded",
        "tests/test_ok.py": b"test",
        "data/ignored.txt": b"ignored",
        "curriculum/worktrees/keep.json": b"{}",
        ".claude/worktrees_like/keep.md": b"keep",
        ".claude/other.yaml": b"yaml",
    }
    for name, contents in files.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(contents)


def test_pruning_preserves_exact_selection_and_raw_bytes(tmp_path):
    source_tree(tmp_path)
    found = gate.identities(tmp_path)
    assert found == legacy_identities(tmp_path)
    assert found["autortl/a.py"] == hashlib.sha256(b"a\r\nb").hexdigest()
    assert ".claude/skills/x/SKILL.md" in found
    assert "curriculum/worktrees/keep.json" in found
    assert ".claude/worktrees_like/keep.md" in found
    assert list(found) == sorted(found)


def test_excluded_worktree_descendants_are_never_scanned(tmp_path, monkeypatch):
    source_tree(tmp_path)
    scans = []
    original = os.scandir

    def counted(path):
        scans.append(Path(path))
        return original(path)

    monkeypatch.setattr(os, "scandir", counted)
    gate.identities(tmp_path)
    excluded = tmp_path / ".claude" / "worktrees"
    assert not [path for path in scans if path == excluded or excluded in path.parents]
    assert tmp_path / ".claude" / "skills" in scans


def test_missing_optional_roots_preserve_selection(tmp_path):
    (tmp_path / "run.py").write_bytes(b"run")
    assert gate.identities(tmp_path) == legacy_identities(tmp_path)
    assert list(gate.identities(tmp_path)) == ["run.py"]


def test_file_symlinks_are_hashed_but_directory_symlinks_are_not_followed(tmp_path):
    root = tmp_path / "checkout"
    source_tree(root)
    external = tmp_path / "external"
    external.mkdir()
    (external / "outside.py").write_bytes(b"external\r\n")
    link_or_skip(lambda: (root / "data" / "linked.py").symlink_to(external / "outside.py"))
    link_or_skip(lambda: (root / "data" / "linked_dir").symlink_to(external, target_is_directory=True))
    found = gate.identities(root)
    assert found == legacy_identities(root)
    assert found["data/linked.py"] == hashlib.sha256(b"external\r\n").hexdigest()
    assert not any(name.startswith("data/linked_dir/") for name in found)


@pytest.mark.skipif(os.name != "nt", reason="Windows junction behavior")
def test_windows_junction_traversal_matches_legacy_rglob(tmp_path):
    import _winapi

    root = tmp_path / "checkout"
    source_tree(root)
    external = tmp_path / "external"
    external.mkdir()
    (external / "through_junction.py").write_bytes(b"junction\r\n")
    # Junctions do not require the Windows symbolic-link privilege. Both paths
    # are inside this test's private tree; no machine/source paths are linked.
    link_or_skip(lambda: _winapi.CreateJunction(str(external), str(root / "data" / "junction")))
    found = gate.identities(root)
    assert found == legacy_identities(root)
    assert found["data/junction/through_junction.py"] == hashlib.sha256(b"junction\r\n").hexdigest()


@pytest.mark.skipif(os.name != "nt", reason="Windows junction behavior")
def test_selected_root_junction_matches_legacy_rglob(tmp_path):
    import _winapi

    root = tmp_path / "checkout"
    root.mkdir()
    (root / "run.py").write_bytes(b"run")
    external = tmp_path / "external"
    external.mkdir()
    (external / "source.py").write_bytes(b"root junction")
    link_or_skip(lambda: _winapi.CreateJunction(str(external), str(root / "autortl")))
    found = gate.identities(root)
    assert found == legacy_identities(root)
    assert "autortl/source.py" in found
