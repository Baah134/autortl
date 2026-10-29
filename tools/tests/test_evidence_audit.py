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
ABS_LOST = "C:\\Users\\someone\\autortl-work\\logs\\cases-run-01\\reference\\lost.v"


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
    git(root, "init", "-q", "-b", "main")
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


def run(root, exceptions=None, worktree=False, rev="HEAD"):
    snapshot = audit.TreeSnapshot(root) if worktree else audit.CommitSnapshot(root, rev)
    history = audit.History(root, snapshot.rev or "HEAD")
    try:
        return audit.audit(snapshot, history, exceptions)
    finally:
        snapshot.close()
        history.close()


def statuses(report):
    rows = report["failures"] + report["exceptions"]
    return {(r["manifest"].removeprefix("evidence/"), r.get("path")): r["status"] for r in rows}


# Every failure in the fixture tree at HEAD, and why it fails.
EXPECTED_FAILURES = {
    ("archive-a/archive-manifest.json", "result.json"): "mismatch",
    ("archive-a/archive-manifest.json", "gone/xsim.jou"): "missing",
    ("cases-run-01/admission/manifest.json", ABS_LOST): "missing",
    ("board-01/manifest.json", "src/never.v"): "unbound",
    ("board-01/manifest.json", "bitstream_sha256"): "digest_not_found",
    ("move/relocation-manifest.json", "..\\outside.txt"): "unsafe_path",
    ("counter-ref/manifest.json", "tb_sha256"): "digest_not_found",
    ("mixed/manifest.json", None): "unparsed_digests",
    ("plain/manifest.json", None): "no_claims",
    ("broken/archive-manifest.json", None): "unreadable_manifest",
}


def claim_of(report_or_none, manifest, path, status, container=""):
    """An exception claim entry for a fixture claim, with its real digest."""
    return {"container": container, "path": path, "status": status, "sha256": DIGESTS[(manifest, path)]}


def manifest_digests():
    found = {}
    for path in FIXTURES.rglob("*.json"):
        rel = "evidence/" + path.relative_to(FIXTURES).as_posix()
        try:
            data = json.loads(path.read_bytes().decode("utf-8-sig"))
        except ValueError:
            continue
        for claim in audit.claims(rel, data):
            found[(rel.removeprefix("evidence/"), claim.path)] = claim.sha256
    return found


DIGESTS = manifest_digests()


def exception(manifest, claims, predecessor=None, **extra):
    return {"manifest": "evidence/" + manifest, "claims": claims, "kind": "test", "reason": "test",
            "predecessor": predecessor, **extra}


def loss(manifest, path, status, container=""):
    return exception(manifest, [claim_of(None, manifest, path, status, container)])


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
    assert report["status"] == {"digest_not_found": 2, "missing": 2, "mismatch": 1, "no_claims": 1, "ok": 6,
                                "ok_current": 3, "ok_digest_found": 1, "ok_historical": 2, "unbound": 1,
                                "unparsed_digests": 1, "unreadable_manifest": 1, "unsafe_path": 1}
    assert report["claims_by_kind"] == {"archive": 9, "binding": 7, "unpathed": 3}
    mixed = next(r for r in report["failures"] if r["status"] == "unparsed_digests")
    assert mixed["detail"] == {"build_id": 1, "seen/[]": 1}
    assert not report["passed"]


def test_source_freezes_are_claim_files(repo):
    assert audit.is_manifest("evidence/x/proposal-fixes-source-freeze-01.json")
    assert audit.is_manifest("evidence/x/source-freeze.json")
    assert audit.is_manifest("evidence/x/original-source227.json")
    assert audit.is_manifest("evidence/x/tested-source-identities.json")
    assert not audit.is_manifest("evidence/x/source-verification.json")
    assert not audit.is_manifest("evidence/x/summary.json")
    data = json.loads((FIXTURES / "freeze" / "proposal-fixes-source-freeze-01.json").read_text())
    assert {c.kind for c in audit.claims("evidence/freeze/proposal-fixes-source-freeze-01.json", data)} == {"binding"}


def test_bindings_report_how_they_matched(repo):
    # board-01 binds src\core.v as a Windows CRLF checkout of HEAD and src/old.v
    # as stored; the relocation list and the freeze bind V1 of src/core.v, which
    # only history still holds.
    assert run(repo)["bindings_by_line_ending"] == {
        "ok_current/crlf": 1, "ok_current/raw": 2, "ok_historical/raw": 2}
    history = audit.History(repo)
    try:
        digests = history.digests("src/core.v")
    finally:
        history.close()
    assert digests == {sha(V1): "raw", sha(V1.replace(b"\n", b"\r\n")): "crlf",
                       sha(V2): "raw", sha(V2.replace(b"\n", b"\r\n")): "crlf"}


def test_history_is_the_audited_revisions_own(repo):
    # A version that exists only on another branch does not bind a claim.
    git(repo, "checkout", "-q", "-b", "side")
    (repo / "src" / "core.v").write_bytes(b"side only\n")
    commit(repo, "side")
    git(repo, "checkout", "-q", "main")
    freeze = repo / "evidence" / "freeze2"
    freeze.mkdir()
    (freeze / "source-freeze.json").write_text(json.dumps({"src/core.v": sha(b"side only\n")}))
    commit(repo, "freeze naming a side-branch version")
    assert statuses(run(repo))[("freeze2/source-freeze.json", "src/core.v")] == "unbound"
    git(repo, "merge", "-q", "--no-ff", "-m", "merge side", "side")
    assert ("freeze2/source-freeze.json", "src/core.v") not in statuses(run(repo))
    # Deleted files keep their history.
    (repo / "src" / "old.v").unlink()
    commit(repo, "delete old.v")
    assert ("board-01/manifest.json", "src/old.v") not in statuses(run(repo))


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


def test_unpathed_digest_must_be_in_evidence(repo):
    (repo / "bits").mkdir()
    (repo / "bits" / "board.bit").write_bytes(b"bitstream kept elsewhere\n")
    commit(repo, "a matching file outside evidence/")
    assert statuses(run(repo))[("board-01/manifest.json", "bitstream_sha256")] == "digest_not_found"
    shutil.move(repo / "bits", repo / "evidence" / "bits")
    commit(repo, "archive the bitstream")
    report = run(repo)
    assert ("board-01/manifest.json", "bitstream_sha256") not in statuses(report)
    assert report["status"]["ok_digest_elsewhere"] == 1


def test_empty_file_digest_proves_nothing(repo):
    ref = repo / "evidence" / "empty-ref"
    ref.mkdir()
    (ref / "empty.log").write_bytes(b"")
    (ref / "manifest.json").write_text(json.dumps([{"case": "c", "source_sha256": sha(b"")}]))
    commit(repo, "a digest of the empty file")
    assert statuses(run(repo))[("empty-ref/manifest.json", "source_sha256")] == "vacuous_digest"


def test_absolute_path_falls_back_to_an_existing_folder(repo):
    # lost.v is gone, but its folder reference/ exists in the renamed archive,
    # so the claim is reported as missing there rather than as unmappable.
    report = run(repo)
    row = next(r for r in report["failures"] if r.get("path") == ABS_LOST)
    assert row["status"] == "missing"


def test_exception_proven_by_predecessor(repo):
    pred = repo / "evidence" / "before" / "gone"
    pred.mkdir(parents=True)
    (pred / "xsim.jou").write_bytes(b"lost journal\n")
    commit(repo, "predecessor")
    proof = exception("archive-a/archive-manifest.json",
                      [claim_of(None, "archive-a/archive-manifest.json", "gone/xsim.jou", "missing")], "evidence/before")
    report = run(repo, [proof])
    row = next(r for r in report["exceptions"] if r["path"] == "gone/xsim.jou")
    assert row["status"] == "excepted" and row["proven_by"] == "evidence/before/gone/xsim.jou"


def test_exception_with_wrong_predecessor_fails(repo):
    wrong = exception("archive-a/archive-manifest.json",
                      [claim_of(None, "archive-a/archive-manifest.json", "result.json", "mismatch")], "evidence/archive-a")
    assert statuses(run(repo, [wrong]))[("archive-a/archive-manifest.json", "result.json")] == "exception_unproven"


def test_recorded_loss_passes_but_is_listed(repo):
    report = run(repo, [loss("archive-a/archive-manifest.json", "gone/xsim.jou", "missing")])
    assert statuses(report)[("archive-a/archive-manifest.json", "gone/xsim.jou")] == "accepted_loss"
    assert ("archive-a/archive-manifest.json", "gone/xsim.jou") not in {
        (r["manifest"].removeprefix("evidence/"), r.get("path")) for r in report["failures"]}


def test_exception_is_pinned_to_its_digest(repo):
    # Editing the recorded digest makes it a different claim: the old
    # exception goes stale and the new failure is reported.
    rules = [loss("archive-a/archive-manifest.json", "gone/xsim.jou", "missing")]
    path = repo / "evidence" / "archive-a" / "archive-manifest.json"
    data = json.loads(path.read_text())
    data["gone/xsim.jou"] = sha(b"some other journal\n")
    path.write_text(json.dumps(data))
    commit(repo, "edit a recorded digest")
    found = {(r.get("path"), r["status"]) for r in run(repo, rules)["failures"]}
    assert ("gone/xsim.jou", "missing") in found and ("gone/xsim.jou", "stale_exception") in found


def test_exception_is_pinned_to_its_failure(repo):
    rules = [loss("archive-a/archive-manifest.json", "gone/xsim.jou", "missing")]
    (repo / "evidence" / "archive-a" / "gone").mkdir()
    (repo / "evidence" / "archive-a" / "gone" / "xsim.jou").write_bytes(b"different bytes\n")
    commit(repo, "missing becomes mismatch")
    assert statuses(run(repo, rules))[("archive-a/archive-manifest.json", "gone/xsim.jou")] == "exception_status_changed"


def test_exception_for_a_passing_claim_is_stale(repo):
    entry = exception("archive-a/archive-manifest.json",
                      [{"container": "", "path": "xvlog.log", "status": "missing",
                        "sha256": DIGESTS[("archive-a/archive-manifest.json", "xvlog.log")]}])
    assert statuses(run(repo, [entry]))[("archive-a/archive-manifest.json", "xvlog.log")] == "stale_exception"
    # Working-copy line endings depend on the checkout, so there it is only noted.
    assert ("archive-a/archive-manifest.json", "xvlog.log") not in statuses(run(repo, [entry], worktree=True))


def test_policy_rejects_loose_or_duplicate_entries():
    good = {"container": "", "path": "a", "sha256": "0" * 64, "status": "missing"}
    with pytest.raises(audit.AuditError, match="listed twice"):
        audit.policy([exception("m", [good]), exception("m", [good])])
    with pytest.raises(audit.AuditError, match="failing status"):
        audit.policy([exception("m", [{**good, "status": "ok"}])])
    with pytest.raises(audit.AuditError, match="failing status"):
        audit.policy([exception("m", [{"path": "a", "sha256": "0" * 64}])])
    with pytest.raises(audit.AuditError, match="lists no claims"):
        audit.policy([exception("m", [])])
    with pytest.raises(audit.AuditError, match="lacks"):
        audit.policy([{"manifest": "m", "claims": [good]}])
    with pytest.raises(audit.AuditError, match="unique manifest"):
        audit.policy({"manifests_without_claims": [{"manifest": "m", "reason": "r"}] * 2})


def test_claim_files_without_claims_and_recorded_values(repo):
    rules = {"manifests_without_claims": [{"manifest": "evidence/plain/manifest.json", "reason": "case list"}],
             "recorded_values": [{"manifest": "evidence/mixed/manifest.json",
                                  "keys": {"build_id": 1, "seen/[]": 1}, "reason": "ids"}]}
    found = statuses(run(repo, rules))
    assert ("plain/manifest.json", None) not in found and ("mixed/manifest.json", None) not in found
    # The recorded keys must match exactly, or the manifest fails again.
    rules["recorded_values"][0]["keys"] = {"build_id": 1}
    assert statuses(run(repo, rules))[("mixed/manifest.json", None)] == "unparsed_digests"
    # An allowance for a manifest that no longer needs one is stale.
    (repo / "evidence" / "plain" / "manifest.json").unlink()
    commit(repo, "drop plain")
    rules["recorded_values"][0]["keys"] = {"build_id": 1, "seen/[]": 1}
    assert statuses(run(repo, rules))[("plain/manifest.json", None)] == "stale_exception"


def test_reconstruct_proves_a_mixed_ending_working_copy(repo):
    blob = git(repo, "rev-parse", "HEAD:src/core.v").decode().strip()
    mixed = V2.replace(b"endmodule\n", b"endmodule\r\n")
    manifest = repo / "evidence" / "tested" / "tested-source-manifest.json"
    manifest.parent.mkdir()
    manifest.write_text(json.dumps({"src/core.v": sha(mixed)}))
    commit(repo, "tested source identity")
    assert statuses(run(repo))[("tested/tested-source-manifest.json", "src/core.v")] == "unbound"
    claim = [{"container": "", "path": "src/core.v", "sha256": sha(mixed), "status": "unbound"}]
    proof = exception("tested/tested-source-manifest.json", claim, reconstruct={"blob": blob, "crlf_lines": [2]})
    assert statuses(run(repo, [proof]))[("tested/tested-source-manifest.json", "src/core.v")] == "excepted"
    wrong = exception("tested/tested-source-manifest.json", claim, reconstruct={"blob": blob, "crlf_lines": [1]})
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
    found = list(audit.claims("evidence/x/manifest.json", data))
    assert {(c.kind, c.path, c.sha256[0]) for c in found} == {
        ("binding", "src/a.v", "a"), ("archive", "r.txt", "b"), ("archive", "x", "c"),
        ("unpathed", "winner_sha256", "d")}
    assert audit.unparsed_digests(data, found) == {"note": 1}
    binding = list(audit.claims("evidence/x/tested-source-manifest-02.json", {"autortl/fsm.py": "f" * 64}))
    assert [c.kind for c in binding] == ["binding"]


def test_is_manifest():
    assert audit.is_manifest("evidence/a/archive-manifest.json")
    assert audit.is_manifest("evidence/a/source-identity.json")
    assert not audit.is_manifest("evidence/a/missing-manifest-blobs.json")
    assert not audit.is_manifest("tools/tests/fixtures/evidence/a/manifest.json")
    assert not audit.is_manifest("evidence/a/summary.json")


def test_outside_scope_is_counted(repo):
    run_dir = repo / "evidence" / "run"
    run_dir.mkdir()
    (run_dir / "state.json").write_text(json.dumps({"best_sha256": "a" * 64, "seen": ["b" * 64]}))
    commit(repo, "a run record")
    scope = run(repo)["outside_scope"]
    assert scope["files"] == 1 and scope["digests"] == 2 and scope["by_name"] == {"state.json": {"files": 1, "digests": 2}}


def test_load_exceptions(tmp_path):
    path = tmp_path / "exceptions.json"
    path.write_text(json.dumps({"schema": 1, "exceptions": []}))
    with pytest.raises(audit.AuditError, match="schema 2"):
        audit.load_exceptions(path)
    path.write_text("{not json")
    with pytest.raises(audit.AuditError, match="not valid JSON"):
        audit.load_exceptions(path)
    assert audit.load_exceptions(tmp_path / "absent.json") == {"claims": {}, "empty": {}, "values": {}}


def test_each_revision_is_audited_with_its_own_exceptions(repo, tmp_path, capsys):
    before = git(repo, "rev-parse", "HEAD").decode().strip()
    listed = {"schema": 2, "exceptions": [loss("archive-a/archive-manifest.json", "gone/xsim.jou", "missing")]}
    (repo / "tools").mkdir()
    (repo / "tools" / "evidence_exceptions.json").write_text(json.dumps(listed))
    commit(repo, "record a loss")
    out = tmp_path / "now.json"
    audit.main(["--root", str(repo), "--report", str(out)])
    assert [r["path"] for r in json.loads(out.read_text())["exceptions"]] == ["gone/xsim.jou"]
    # The earlier commit had no list, so auditing it reproduces its failures.
    audit.main(["--root", str(repo), "--rev", before, "--report", str(out)])
    assert json.loads(out.read_text())["exceptions"] == []
    # An explicit file overrides the snapshot's list.
    empty = tmp_path / "empty.json"
    empty.write_text(json.dumps({"schema": 2}))
    audit.main(["--root", str(repo), "--exceptions", str(empty), "--report", str(out)])
    assert json.loads(out.read_text())["exceptions"] == []
    (repo / "tools" / "evidence_exceptions.json").write_text("{not json")
    commit(repo, "break the list")
    assert audit.main(["--root", str(repo)]) == 2
    assert "not valid JSON" in capsys.readouterr().err


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
    assert f"FAILED: {len(EXPECTED_FAILURES)} claims" in capsys.readouterr().out
    for manifest in ("archive-a", "cases-run-01", "board-01", "move", "counter-ref", "broken", "mixed", "plain"):
        shutil.rmtree(repo / "evidence" / manifest)
    commit(repo, "drop failing fixtures")
    assert audit.main(["--root", str(repo)]) == 0
    assert audit.main(["--root", str(repo), "--rev", "no-such-rev"]) == 2
