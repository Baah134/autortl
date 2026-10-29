"""Audit every SHA-256 claim in the evidence tree against committed bytes.

docs/PUBLICATION.md step 5 requires reading each manifest entry from the
committed Git blobs and comparing its digest; a working-copy pass alone does
not prove a complete published archive. This audit applies that rule to every
manifest under evidence/, not only to named archives.

Two kinds of claim are checked differently:

- Archive claims name files relative to the manifest's own folder. Each file
  must exist in the snapshot with exactly the recorded digest.
- Source bindings name repository files (tested harness or board sources) as
  they were when something was tested. Those files may have changed since, so
  a binding passes if the current file or any committed version of that path
  in the full Git history matches, as stored or as a Windows core.autocrlf
  checkout. A digest no commit ever held is unbound and fails.

Digests recorded without a path (source_sha256, bitstream_sha256) pass when a
file under the manifest's folder, or failing that anywhere in the snapshot,
has that digest.

Known exceptions live in tools/evidence_exceptions.json and name exact
claims. An exception must be proven by bytes the audit can read (a
predecessor archive, or a committed blob with its line endings restored), or
record a loss with its reason. One that no longer matches a failing claim
fails the audit, so the list cannot hide new problems or outlive old ones.

Usage: python tools/evidence_audit.py [--rev REV | --worktree] [--report FILE]
"""
from __future__ import annotations
import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EXCEPTIONS = ROOT / "tools" / "evidence_exceptions.json"
HEX = re.compile(r"[0-9a-fA-F]{64}")
PATH_KEYS = ("path", "file", "relative_path")
DIGEST_KEYS = ("sha256", "sha", "hash", "digest")
# Manifests whose entries are repository paths at test time, not archive files.
BINDING_NAMES = re.compile(r"tested-source-manifest(-\d+)?\.json|relocation-manifest\.json|source-identity\.json")
BINDING_CONTAINERS = {"sources"}
UNPATHED_KEY = re.compile(r"\w+_sha256")
PASS = {"ok", "ok_current", "ok_historical", "ok_digest_found", "ok_digest_elsewhere",
        "excepted", "accepted_loss"}


class AuditError(RuntimeError):
    pass


def _git(root, *args):
    try:
        done = subprocess.run(["git", *args], cwd=root, capture_output=True, check=True)
    except FileNotFoundError as error:
        raise AuditError("git is not on PATH") from error
    except subprocess.CalledProcessError as error:
        raise AuditError(f"git {' '.join(args)} failed: {error.stderr.decode(errors='replace').strip()}") from error
    return done.stdout


class _BlobReader:
    """One long-lived `git cat-file --batch` for reading many objects."""

    def __init__(self, root):
        self._proc = subprocess.Popen(["git", "cat-file", "--batch"], cwd=root,
                                      stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def read(self, spec):
        self._proc.stdin.write(spec.encode("utf-8") + b"\n")
        self._proc.stdin.flush()
        header = self._proc.stdout.readline().rstrip(b"\n").split()
        if len(header) == 2 and header[1] in (b"missing", b"ambiguous"):
            return None
        if len(header) != 3:
            raise AuditError(f"unexpected cat-file reply for {spec!r}: {header!r}")
        size = int(header[2])
        data = self._proc.stdout.read(size)
        if len(data) != size or self._proc.stdout.read(1) != b"\n":
            raise AuditError(f"short cat-file read for {spec!r}")
        return data if header[1] == b"blob" else None

    def close(self):
        self._proc.stdin.close()
        self._proc.stdout.close()
        self._proc.wait(timeout=30)


class CommitSnapshot:
    """The bytes Git stores for one revision: what a clone actually gets."""

    def __init__(self, root, rev):
        self.root = Path(root)
        self.rev = _git(root, "rev-parse", "--verify", f"{rev}^{{commit}}").decode().strip()
        listing = _git(root, "ls-tree", "-r", "-z", "--name-only", self.rev)
        self.paths = sorted(p for p in listing.decode("utf-8").split("\0") if p)
        self._blobs = _BlobReader(root)

    def read(self, path):
        return self._blobs.read(f"{self.rev}:{path}")

    def close(self):
        self._blobs.close()


class TreeSnapshot:
    """The working copy, for checking an archive before it is committed."""

    def __init__(self, root):
        self.root = Path(root)
        self.rev = None
        # Tracked plus untracked-but-not-ignored: exactly what a commit would hold.
        listing = _git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
        self.paths = sorted({p for p in listing.decode("utf-8").split("\0") if p and (self.root / p).is_file()})

    def read(self, path):
        target = self.root / path
        return target.read_bytes() if target.is_file() else None

    def close(self):
        pass


def checkout_digests(data):
    """SHA-256 of a blob as stored, and as a Windows core.autocrlf checkout.

    Harness sources are text in Git, so a Windows working copy holds them with
    CRLF endings. Source-identity manifests hashed those working-copy bytes.
    """
    found = {"raw": hashlib.sha256(data).hexdigest()}
    if b"\0" not in data and b"\n" in data:
        crlf = data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        if crlf != data:
            found["crlf"] = hashlib.sha256(crlf).hexdigest()
    return found


class History:
    """SHA-256 of every version a path has held in any commit (all refs)."""

    def __init__(self, root):
        self.root = Path(root)
        self._blob_ids = None
        self._digests = {}
        self._reader = None

    def _index(self):
        if _git(self.root, "rev-parse", "--is-shallow-repository").strip() == b"true":
            raise AuditError("source bindings need the full history; this clone is shallow "
                             "(git fetch --unshallow, or actions/checkout with fetch-depth: 0)")
        raw = _git(self.root, "log", "--all", "--root", "-m", "--no-renames", "--format=",
                   "--raw", "--no-abbrev", "-z").decode("utf-8")
        ids = {}
        tokens = raw.split("\0")
        i = 0
        while i < len(tokens):
            meta = tokens[i].lstrip("\n")
            if meta.startswith(":") and i + 1 < len(tokens):
                fields = meta.split()
                if len(fields) >= 5 and set(fields[3]) != {"0"}:
                    ids.setdefault(tokens[i + 1], set()).add(fields[3])
                i += 2
            else:
                i += 1
        return ids

    def digests(self, path):
        """Map each digest a committed version of path had to its line ending."""
        if self._blob_ids is None:
            self._blob_ids = self._index()
        if path not in self._digests:
            found = {}
            for blob in sorted(self._blob_ids.get(path, ())):
                data = self.blob(blob)
                if data is not None:
                    for eol, digest in checkout_digests(data).items():
                        found.setdefault(digest, eol)
            self._digests[path] = found
        return self._digests[path]

    def blob(self, oid):
        if self._reader is None:
            self._reader = _BlobReader(self.root)
        return self._reader.read(oid)

    def close(self):
        if self._reader is not None:
            self._reader.close()


@dataclass(frozen=True)
class Claim:
    manifest: str
    container: str
    kind: str  # archive | binding | unpathed
    path: str  # file path as written, or the digest key for unpathed claims
    sha256: str


def is_manifest(path):
    name = PurePosixPath(path).name
    return path.startswith("evidence/") and name.endswith(".json") and (
        "manifest" in name or name == "source-identity.json") and name != "missing-manifest-blobs.json"


def _is_digest(value):
    return isinstance(value, str) and HEX.fullmatch(value) is not None


def claims(manifest, data):
    """Yield every digest claim in a parsed manifest, whatever its layout."""
    binding_file = BINDING_NAMES.fullmatch(PurePosixPath(manifest).name) is not None

    def kind_for(trail):
        return "binding" if binding_file or (trail and trail[-1] in BINDING_CONTAINERS) else "archive"

    def walk(node, trail):
        label = "/".join(trail)
        if isinstance(node, dict):
            if node and all(_is_digest(v) for v in node.values()):
                for path, digest in node.items():
                    yield Claim(manifest, label, kind_for(trail), path, digest.lower())
                return
            path_key = next((k for k in PATH_KEYS if isinstance(node.get(k), str)), None)
            digest_key = next((k for k in DIGEST_KEYS if _is_digest(node.get(k))), None)
            if path_key and digest_key:
                yield Claim(manifest, label, kind_for(trail), node[path_key], node[digest_key].lower())
            elif not path_key:
                for key, value in node.items():
                    if UNPATHED_KEY.fullmatch(key) and _is_digest(value):
                        yield Claim(manifest, label, "unpathed", key, value.lower())
            for key, value in node.items():
                if isinstance(value, (dict, list)):
                    yield from walk(value, trail + (key,))
        elif isinstance(node, list):
            for value in node:
                yield from walk(value, trail + ("[]",))

    yield from walk(data, ())


def _resolve(base, path, files=frozenset(), folders=frozenset()):
    """Join a manifest path onto base, or None if it would leave base.

    Manifests written on Windows use backslash separators; they name the same
    relative path. Qualification case manifests record absolute paths of the
    run folder they were built in (C:/.../logs/<run>/...), and that folder was
    sometimes renamed when copied into evidence/. Such a path maps to its
    longest tail that names a file inside base, or else, so that a lost file
    is reported as missing, its longest tail whose folder exists inside base.
    """
    if not path:
        return None
    if path.startswith(("/", "\\")) or re.match(r"[A-Za-z]:", path):
        parts = [p for p in path.replace("\\", "/").split("/") if p][1:]
        if not base or ".." in parts:
            return None
        tails = ["/".join(parts[k:]) for k in range(len(parts))]
        path = (next((t for t in tails if f"{base}/{t}" in files), None)
                or next((t for t in tails if "/" in t and posixpath.dirname(f"{base}/{t}") in folders), None))
        if path is None:
            return None
    path = path.replace("\\", "/")
    joined = posixpath.normpath(posixpath.join(base, path)) if base else posixpath.normpath(path)
    if base and not (joined + "/").startswith(base.rstrip("/") + "/"):
        return None
    if joined.startswith("../") or joined == "..":
        return None
    return joined


def load_exceptions(path=EXCEPTIONS):
    if not Path(path).is_file():
        return []
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != 1 or not isinstance(data.get("exceptions"), list):
        raise AuditError(f"{path}: expected schema 1 with an exceptions list")
    for entry in data["exceptions"]:
        missing = {"manifest", "paths", "kind", "reason", "predecessor"} - set(entry)
        if missing:
            raise AuditError(f"{path}: exception for {entry.get('manifest')} lacks {sorted(missing)}")
        if entry["paths"] == ["*"] and not isinstance(entry.get("expected_count"), int):
            raise AuditError(f"{path}: a '*' exception for {entry['manifest']} needs expected_count")
        rebuild = entry.get("reconstruct")
        if rebuild is not None and (not isinstance(rebuild.get("blob"), str) or not rebuild.get("crlf_lines")
                                    and not rebuild.get("lf_lines")):
            raise AuditError(f"{path}: reconstruct for {entry['manifest']} needs blob and crlf_lines or lf_lines")
    return data["exceptions"]


def reconstruct(data, crlf_lines=(), lf_lines=()):
    """Rebuild a mixed-ending working copy from its line-normalized blob.

    A file edited on Windows can mix CRLF and LF lines. Git stores it
    normalized, so the tested bytes differ from every commit only in those
    line endings. Lines are numbered from 1; unlisted lines keep the ending
    the majority of the file had (LF if crlf_lines are given, else CRLF).
    """
    lines = data.replace(b"\r\n", b"\n").split(b"\n")
    body, last = lines[:-1], lines[-1]
    default, flip = (b"\n", b"\r\n") if crlf_lines else (b"\r\n", b"\n")
    chosen = set(crlf_lines or lf_lines)
    return b"".join(line + (flip if n in chosen else default) for n, line in enumerate(body, 1)) + last


def audit(snapshot, history, exceptions=()):
    """Check every claim; return a report dict (see `summarize`)."""
    present = set(snapshot.paths)
    cache = {}
    everywhere = {}

    def variants_of(path):
        if path not in cache:
            data = snapshot.read(path) if path in present else None
            cache[path] = {} if data is None else checkout_digests(data)
        return cache[path]

    def digest_of(path):
        return variants_of(path).get("raw")

    def anywhere(digest):
        if not everywhere:
            for path in snapshot.paths:
                everywhere.setdefault(digest_of(path), path)
        return everywhere.get(digest)

    folders = {posixpath.dirname(p) for p in present}
    excepted = {}
    for entry in exceptions:
        for rel in entry["paths"]:
            excepted[(entry["manifest"], rel)] = entry
    used = {}
    results = []
    manifests = sorted(p for p in present if is_manifest(p))
    for manifest in manifests:
        base = posixpath.dirname(manifest)
        try:
            raw = snapshot.read(manifest)
            data = json.loads(raw.decode("utf-8-sig"))
        except (UnicodeDecodeError, ValueError) as error:
            results.append({"manifest": manifest, "status": "unreadable_manifest", "detail": str(error)})
            continue
        found = list(claims(manifest, data))
        if not found:
            results.append({"manifest": manifest, "status": "no_claims"})
            continue
        folder = [p for p in present if p.startswith(base + "/")]
        for claim in found:
            row = {"manifest": manifest, "container": claim.container, "kind": claim.kind,
                   "path": claim.path, "sha256": claim.sha256}
            if claim.kind == "unpathed":
                hit = next((p for p in folder if digest_of(p) == claim.sha256), None)
                status = "ok_digest_found"
                if hit is None:
                    hit = anywhere(claim.sha256)
                    status = "ok_digest_elsewhere" if hit else "digest_not_found"
                row.update(status=status, matched=hit)
            elif claim.kind == "binding":
                target = _resolve("", claim.path)
                current = {} if target is None else {d: e for e, d in variants_of(target).items()}
                if target is None:
                    row["status"] = "unsafe_path"
                elif claim.sha256 in current:
                    row.update(status="ok_current", eol=current[claim.sha256])
                elif claim.sha256 in history.digests(target):
                    row.update(status="ok_historical", eol=history.digests(target)[claim.sha256])
                else:
                    row["status"] = "unbound"
            else:
                target = _resolve(base, claim.path, present, folders)
                actual = None if target is None else digest_of(target)
                row["status"] = ("unsafe_path" if target is None else "missing" if actual is None
                                 else "ok" if actual == claim.sha256 else "mismatch")
            key = (manifest, claim.path)
            if key not in excepted and (manifest, "*") in excepted:
                key = (manifest, "*")
            entry = excepted.get(key)
            if entry and row["status"] not in PASS:
                used[key] = used.get(key, 0) + 1
                row.update(exception=entry["kind"], reason=entry["reason"])
                rebuild = entry.get("reconstruct")
                if rebuild:
                    data = history.blob(rebuild["blob"])
                    rebuilt = None if data is None else reconstruct(
                        data, rebuild.get("crlf_lines", ()), rebuild.get("lf_lines", ()))
                    ok = rebuilt is not None and hashlib.sha256(rebuilt).hexdigest() == claim.sha256
                    row.update(status="excepted" if ok else "exception_unproven",
                               proven_by=f"blob {rebuild['blob']} with line endings restored")
                elif entry["predecessor"] is None:
                    row["status"] = "accepted_loss"
                else:
                    predecessor = _resolve(entry["predecessor"], claim.path)
                    if predecessor is not None and digest_of(predecessor) == claim.sha256:
                        row.update(status="excepted", proven_by=predecessor)
                    else:
                        row["status"] = "exception_unproven"
            results.append(row)
    for key, entry in sorted(excepted.items()):
        if key not in used:
            # A working copy's line endings depend on the checkout, so a mixed-
            # ending file can pass there as stored; only committed bytes are fixed.
            status = "stale_exception" if snapshot.rev else "unused_exception"
            results.append({"manifest": key[0], "path": key[1], "status": status})
        elif key[1] == "*" and used[key] != entry["expected_count"]:
            results.append({"manifest": key[0], "path": "*", "status": "exception_count_changed",
                            "detail": f"expected {entry['expected_count']} failing claims, found {used[key]}"})
    return summarize(snapshot, manifests, results)


def summarize(snapshot, manifests, results):
    counts = Counter(r["status"] for r in results if r["status"] not in ("no_claims",))
    kinds = Counter(r["kind"] for r in results if "kind" in r)
    failures = [r for r in results if r["status"] not in PASS | {"no_claims", "unused_exception"}]
    return {"schema": 1, "revision": snapshot.rev, "manifests": len(manifests),
            "claims": sum(kinds.values()), "claims_by_kind": dict(sorted(kinds.items())),
            "status": dict(sorted(counts.items())),
            "bindings_by_line_ending": dict(sorted(Counter(
                f"{r['status']}/{r['eol']}" for r in results if "eol" in r).items())),
            "manifests_without_claims": sorted(r["manifest"] for r in results if r["status"] == "no_claims"),
            "exceptions": [r for r in results if r["status"] in ("excepted", "accepted_loss")],
            "failures": failures, "passed": not failures}


def render(report, limit=40):
    lines = [f"revision: {report['revision'] or 'working tree'}",
             f"manifests: {report['manifests']}  claims: {report['claims']}  {report['claims_by_kind']}",
             f"status: {report['status']}"]
    for row in report["exceptions"]:
        how = f"proven by {row['proven_by']}" if row["status"] == "excepted" else "bytes not recoverable"
        lines.append(f"{row['status']} ({row['exception']}): {row['manifest']} :: {row['path']}, {how}")
    for row in report["failures"][:limit]:
        lines.append(f"FAIL {row['status']}: {row['manifest']} :: {row.get('path', row.get('detail', ''))}")
    if len(report["failures"]) > limit:
        lines.append(f"... {len(report['failures']) - limit} more failures")
    lines.append("PASS" if report["passed"] else f"FAILED: {len(report['failures'])} claims")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    where = parser.add_mutually_exclusive_group()
    where.add_argument("--rev", default="HEAD", help="audit the committed blobs of this revision (default HEAD)")
    where.add_argument("--worktree", action="store_true", help="audit the working copy instead")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--exceptions", type=Path, default=None)
    parser.add_argument("--report", type=Path, help="also write the full JSON report here")
    args = parser.parse_args(argv)
    exceptions_path = args.exceptions or args.root / "tools" / "evidence_exceptions.json"
    try:
        snapshot = TreeSnapshot(args.root) if args.worktree else CommitSnapshot(args.root, args.rev)
        history = History(args.root)
        try:
            report = audit(snapshot, history, load_exceptions(exceptions_path))
        finally:
            snapshot.close()
            history.close()
    except AuditError as error:
        print(f"evidence audit error: {error}", file=sys.stderr)
        return 2
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(render(report))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
