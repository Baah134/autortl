"""Tests for tools/evidence_audit.py against fixtures of every real layout.

Each test builds a throwaway Git repository holding fixtures/evidence and two
committed versions of src/core.v, so committed-blob reads, the history index
and Windows line-ending variants are exercised with real Git.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import evidence_audit as audit  # noqa: E402
from make_fixtures import V1, V2  # noqa: E402

FIXTURES = HERE / "fixtures" / "evidence"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True).stdout


def commit(root, message):
    git(root, "add", "-A")
    git(root, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", message)


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q")
    git(root, "config", "core.autocrlf", "false")
    (root / ".gitattributes").write_text("* -text\n")
    (root / ".gitignore").write_text("*.ignored\n")
    (root / "src").mkdir()
    (root / "src" / "core.v").write_bytes(V1)
    (root / "src" / "old.v").write_bytes(V1)
    commit(root, "v1")
    shutil.copytree(FIXTURES, root / "evidence")
    (root / "src" / "core.v").write_bytes(V2)
    commit(root, "v2 with evidence")
    return root


def run(root, exceptions=(), worktree=False):
    snapshot = audit.TreeSnapshot(root) if worktree else audit.CommitSnapshot(root, "HEAD")
    history = audit.History(root)
    try:
        return audit.audit(snapshot, history, list(exceptions))
    finally:
        snapshot.close()
        history.close()


def statuses(report):
    rows = report["failures"] + report["exceptions"]
    return {(r["manifest"].removeprefix("evidence/"), r.get("path")): r["status"] for r in rows}


# Every failing claim in the fixture tree at HEAD, and why it fails.
EXPECTED_FAILURES = {
    ("archive-a/archive-manifest.json", "result.json"): "mismatch",
    ("archive-a/archive-manifest.json", "gone/xsim.jou"): "missing",
    ("cases-run-01/admission/manifest.json",
     "C:\\Users\\someone\\autortl-work\\logs\\cases-run-01\\reference\\lost.v"): "missing",
    ("board-01/manifest.json", "src/never.v"): "unbound",
    ("board-01/manifest.json", "bitstream_sha256"): "digest_not_found",
    ("move/relocation-manifest.json", "..\\outside.txt"): "unsafe_path",
    ("counter-ref/manifest.json", "tb_sha256"): "digest_not_found",
    ("broken/archive-manifest.json", None): "unreadable_manifest",
}


def test_fixtures_match_their_generator(tmp_path, monkeypatch):
    import make_fixtures
    monkeypatch.setattr(make_fixtures, "OUT", tmp_path / "evidence")
    make_fixtures.main()
    made = {p.relative_to(tmp_path / "evidence"): p.read_bytes() for p in (tmp_path / "evidence").rglob("*") if p.is_file()}
    kept = {p.relative_to(FIXTURES): p.read_bytes() for p in FIXTURES.rglob("*") if p.is_file()}
    assert made == kept


def test_every_layout_gets_the_pinned_status(repo):
    report = run(repo)
    assert statuses(report) == EXPECTED_FAILURES
    assert report["manifests_without_claims"] == ["evidence/plain/manifest.json"]
    assert report["status"] == {"digest_not_found": 2, "missing": 2, "mismatch": 1, "ok": 5,
                                "ok_current": 2, "ok_digest_found": 1, "ok_historical": 1,
                                "unbound": 1, "unreadable_manifest": 1, "unsafe_path": 1}
    assert report["claims_by_kind"] == {"archive": 8, "binding": 5, "unpathed": 3}
    assert not report["passed"]


def test_bindings_report_how_they_matched(repo):
    # board-01 binds src\core.v as a Windows CRLF checkout of HEAD and
    # src/old.v as stored; the relocation list binds V1 of src/core.v, which
    # only history still holds.
    assert run(repo)["bindings_by_line_ending"] == {
        "ok_current/crlf": 1, "ok_current/raw": 1, "ok_historical/raw": 1}
    history = audit.History(repo)
    try:
        digests = history.digests("src/core.v")
    finally:
        history.close()
    assert digests == {sha(V1): "raw", sha(V1.replace(b"\n", b"\r\n")): "crlf",
                       sha(V2): "raw", sha(V2.replace(b"\n", b"\r\n")): "crlf"}


def test_committed_blobs_are_audited_not_the_working_copy(repo):
    # The publication failure this audit exists for: a manifest entry present
    # on disk but kept out of Git by an ignore rule.
    archive = repo / "evidence" / "late"
    archive.mkdir()
    (archive / "xsim.ignored").write_bytes(b"journal\n")
    (archive / "archive-manifest.json").write_text(json.dumps({"xsim.ignored": sha(b"journal\n")}))
    commit(repo, "archive with an ignored file")
    assert statuses(run(repo))[("late/archive-manifest.json", "xsim.ignored")] == "missing"
    # The working-copy view excludes ignored files too: it shows what a commit would hold.
    assert statuses(run(repo, worktree=True))[("late/archive-manifest.json", "xsim.ignored")] == "missing"


def test_worktree_sees_uncommitted_archives(repo):
    (repo / "evidence" / "archive-a" / "gone").mkdir()
    (repo / "evidence" / "archive-a" / "gone" / "xsim.jou").write_bytes(b"lost journal\n")
    assert ("archive-a/archive-manifest.json", "gone/xsim.jou") in statuses(run(repo))
    assert ("archive-a/archive-manifest.json", "gone/xsim.jou") not in statuses(run(repo, worktree=True))


def test_unpathed_digest_found_elsewhere_in_the_snapshot(repo):
    (repo / "bits").mkdir()
    (repo / "bits" / "board.bit").write_bytes(b"bitstream kept elsewhere\n")
    commit(repo, "archive the bitstream")
    report = run(repo)
    assert ("board-01/manifest.json", "bitstream_sha256") not in statuses(report)
    assert report["status"]["ok_digest_elsewhere"] == 1


def exception(manifest, paths, predecessor=None, **extra):
    return {"manifest": "evidence/" + manifest, "paths": paths, "kind": "test", "reason": "test",
            "predecessor": predecessor, **extra}


def test_exception_proven_by_predecessor(repo):
    pred = repo / "evidence" / "before" / "gone"
    pred.mkdir(parents=True)
    (pred / "xsim.jou").write_bytes(b"lost journal\n")
    commit(repo, "predecessor")
    report = run(repo, [exception("archive-a/archive-manifest.json", ["gone/xsim.jou"], "evidence/before")])
    row = next(r for r in report["exceptions"] if r["path"] == "gone/xsim.jou")
    assert row["status"] == "excepted" and row["proven_by"] == "evidence/before/gone/xsim.jou"


def test_exception_with_wrong_predecessor_fails(repo):
    report = run(repo, [exception("archive-a/archive-manifest.json", ["result.json"], "evidence/archive-a")])
    assert statuses(report)[("archive-a/archive-manifest.json", "result.json")] == "exception_unproven"


def test_recorded_loss_passes_but_is_listed(repo):
    report = run(repo, [exception("archive-a/archive-manifest.json", ["gone/xsim.jou"])])
    assert statuses(report)[("archive-a/archive-manifest.json", "gone/xsim.jou")] == "accepted_loss"
    assert ("archive-a/archive-manifest.json", "gone/xsim.jou") not in {
        (r["manifest"].removeprefix("evidence/"), r.get("path")) for r in report["failures"]}


def test_exception_for_a_passing_claim_is_stale(repo):
    report = run(repo, [exception("archive-a/archive-manifest.json", ["xvlog.log"])])
    assert statuses(report)[("archive-a/archive-manifest.json", "xvlog.log")] == "stale_exception"
    # Working-copy line endings depend on the checkout, so there it is only noted.
    assert ("archive-a/archive-manifest.json", "xvlog.log") not in statuses(
        run(repo, [exception("archive-a/archive-manifest.json", ["xvlog.log"])], worktree=True))


def test_wildcard_exception_must_match_its_count(repo):
    good = exception("archive-a/archive-manifest.json", ["*"], expected_count=2)
    assert {s for (m, _), s in statuses(run(repo, [good])).items() if m.startswith("archive-a")} == {"accepted_loss"}
    bad = exception("archive-a/archive-manifest.json", ["*"], expected_count=3)
    assert statuses(run(repo, [bad]))[("archive-a/archive-manifest.json", "*")] == "exception_count_changed"


def test_reconstruct_proves_a_mixed_ending_working_copy(repo):
    blob = git(repo, "rev-parse", "HEAD:src/core.v").decode().strip()
    mixed = V2.replace(b"endmodule\n", b"endmodule\r\n")
    manifest = repo / "evidence" / "tested" / "tested-source-manifest.json"
    manifest.parent.mkdir()
    manifest.write_text(json.dumps({"src/core.v": sha(mixed)}))
    commit(repo, "tested source identity")
    assert statuses(run(repo))[("tested/tested-source-manifest.json", "src/core.v")] == "unbound"
    proof = exception("tested/tested-source-manifest.json", ["src/core.v"], reconstruct={"blob": blob, "crlf_lines": [2]})
    assert statuses(run(repo, [proof]))[("tested/tested-source-manifest.json", "src/core.v")] == "excepted"
    wrong = exception("tested/tested-source-manifest.json", ["src/core.v"], reconstruct={"blob": blob, "crlf_lines": [1]})
    assert statuses(run(repo, [wrong]))[("tested/tested-source-manifest.json", "src/core.v")] == "exception_unproven"


@pytest.mark.parametrize("data, crlf, lf, expected", [
    (b"a\nb\nc\n", [2], [], b"a\nb\r\nc\n"),
    (b"a\nb\nc\n", [], [3], b"a\r\nb\r\nc\n"),
    (b"a\nb", [1], [], b"a\r\nb"),
    (b"a\r\nb\r\n", [1], [], b"a\r\nb\n"),
])
def test_reconstruct(data, crlf, lf, expected):
    assert audit.reconstruct(data, crlf, lf) == expected


def test_checkout_digests():
    assert set(audit.checkout_digests(b"a\nb\n")) == {"raw", "crlf"}
    assert audit.checkout_digests(b"a\nb\n")["crlf"] == sha(b"a\r\nb\r\n")
    assert set(audit.checkout_digests(b"a\r\nb\r\n")) == {"raw"}
    assert set(audit.checkout_digests(b"\x00\n")) == {"raw"}
    assert set(audit.checkout_digests(b"no newline")) == {"raw"}


@pytest.mark.parametrize("base, path, expected", [
    ("evidence/a", "x.log", "evidence/a/x.log"),
    ("evidence/a", "sub\\x.pb", "evidence/a/sub/x.pb"),
    ("evidence/a", "../b/x.log", None),
    ("evidence/a", "sub/../../x", None),
    ("evidence/a", "/etc/passwd", None),
    ("evidence/a", "C:\\elsewhere\\nothing.v", None),
    ("evidence/a", "C:\\run\\logs\\a\\..\\x.v", None),
    ("evidence/a", "C:\\run\\logs\\renamed\\ref\\core.v", "evidence/a/ref/core.v"),
    ("evidence/a", "C:\\run\\logs\\renamed\\ref\\lost.v", "evidence/a/ref/lost.v"),
    ("", "src\\core.v", "src/core.v"),
    ("", "..\\outside.txt", None),
    ("", "C:\\src\\core.v", None),
])
def test_resolve(base, path, expected):
    files = {"evidence/a/ref/core.v", "evidence/a/x.log"}
    folders = {"evidence/a", "evidence/a/ref"}
    assert audit._resolve(base, path, files, folders) == expected


def test_claims_lowercase_and_classify():
    data = {"sources": {"src/a.v": "A" * 64}, "files": {"r.txt": "b" * 64},
            "cases": [{"files": [{"path": "x", "sha256": "c" * 64}]}], "winner_sha256": "d" * 64,
            "note": "e" * 64}
    found = {(c.kind, c.path, c.sha256[0]) for c in audit.claims("evidence/x/manifest.json", data)}
    assert found == {("binding", "src/a.v", "a"), ("archive", "r.txt", "b"), ("archive", "x", "c"),
                     ("unpathed", "winner_sha256", "d")}
    binding = list(audit.claims("evidence/x/tested-source-manifest-02.json", {"autortl/fsm.py": "f" * 64}))
    assert [c.kind for c in binding] == ["binding"]


def test_is_manifest():
    assert audit.is_manifest("evidence/a/archive-manifest.json")
    assert audit.is_manifest("evidence/a/source-identity.json")
    assert not audit.is_manifest("evidence/a/missing-manifest-blobs.json")
    assert not audit.is_manifest("tools/tests/fixtures/evidence/a/manifest.json")
    assert not audit.is_manifest("evidence/a/summary.json")


def test_load_exceptions_rejects_incomplete_entries(tmp_path):
    path = tmp_path / "exceptions.json"
    path.write_text(json.dumps({"schema": 1, "exceptions": [{"manifest": "m", "paths": ["*"], "kind": "k",
                                                              "reason": "r", "predecessor": None}]}))
    with pytest.raises(audit.AuditError, match="expected_count"):
        audit.load_exceptions(path)
    path.write_text(json.dumps({"schema": 1, "exceptions": [{"manifest": "m", "paths": ["p"]}]}))
    with pytest.raises(audit.AuditError, match="lacks"):
        audit.load_exceptions(path)
    assert audit.load_exceptions(tmp_path / "absent.json") == []


def test_shallow_clone_is_refused(repo, tmp_path):
    shallow = tmp_path / "shallow"
    git(tmp_path, "clone", "-q", "--depth", "1", repo.as_uri(), str(shallow))
    snapshot = audit.CommitSnapshot(shallow, "HEAD")
    history = audit.History(shallow)
    try:
        with pytest.raises(audit.AuditError, match="shallow"):
            audit.audit(snapshot, history)
    finally:
        snapshot.close()
        history.close()


def test_cli_exit_codes_and_report(repo, tmp_path, capsys):
    out = tmp_path / "report.json"
    assert audit.main(["--root", str(repo), "--report", str(out)]) == 1
    assert json.loads(out.read_text())["passed"] is False
    assert "FAILED: 8 claims" in capsys.readouterr().out
    for manifest in ("archive-a", "cases-run-01", "board-01", "move", "counter-ref", "broken"):
        shutil.rmtree(repo / "evidence" / manifest)
    commit(repo, "drop failing fixtures")
    assert audit.main(["--root", str(repo)]) == 0
    assert audit.main(["--root", str(repo), "--rev", "no-such-rev"]) == 2
