"""Write tools/evidence_exceptions.json (schema 2) from a raw audit report.

The raw report is an audit with no exceptions (`--exceptions` pointing at a
file holding {"schema": 2}). Every failing claim must be classified by a rule
below, or this script stops: nothing is waived by default. Each exception
lists its claims pinned by container, path, digest and failure status, so a
changed claim falls out of the list and fails the audit again.

Usage: python make_exceptions.py <raw-report.json>
"""
from collections import defaultdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "tools" / "evidence_exceptions.json"
HERE = "evidence/2026-10-28/evidence-integrity-01"
RELOCATION = "evidence/2026-10-19/relocation-manifest.json"
LIVE = "evidence/2026-10-24/seed-binding-live-recovery-01/run/validation-manifest.json"
MIXED = "The tested working copy ended one line with a different line ending from the rest of the file; Git stores it normalized."
# (digest of the tested bytes) -> how the audit rebuilds them from a committed blob.
REBUILD = {
    "0285f2de84": {"blob": "b526b6eaa20b87d47df7e8ef27dc6d48692434c4", "crlf_lines": [89]},
    "a97bee21c3": {"blob": "f4ae1474b3ed18e7939b619bb69ab3e204105557", "crlf_lines": [90]},
}
# Tested versions edited before their first commit whose exact bytes survived
# in a Codex staging or pytest folder, now archived under recovered/<label>/.
RECOVERED = {
    ("evidence/2026-10-22/divider-admission-attempt-01/tested-source-manifest.json",
     "curriculum/tier3/iterative_divider_build/iterative_divider_tb.v"): "divider-admission-attempt-01",
    ("evidence/2026-10-23/proposal-fixes-tests-01/proposal-fixes-source-freeze-01.json", "autortl/fsm.py"): "proposal-fixes-tests-01",
    ("evidence/2026-10-23/proposal-fixes-tests-01/proposal-fixes-source-freeze-01.json", "data/taxonomy.yaml"): "proposal-fixes-tests-01",
    ("evidence/2026-10-23/proposal-fixes-tests-01/proposal-fixes-source-freeze-01.json", "tests/test_seed_planning.py"): "proposal-fixes-tests-01",
    ("evidence/2026-10-26/fir4-driver-comparison-01/stage-review/original-source228.json", "autortl/tbgen.py"): "fir4-driver-comparison-01",
    (RELOCATION, "data\\taxonomy.yaml"): "relocation-2026-10-19",
}
LOST = {
    ("evidence/2026-10-22/divider-admission-attempt-01/tested-source-manifest.json", "curriculum/tier3/iterative_divider_build/README.md"),
    ("evidence/2026-10-22/divider-admission-attempt-01/tested-source-manifest.json", "tests/test_iterative_divider_fixture.py"),
    ("evidence/2026-10-22/packet-fifo-admission/tested-source-manifest.json", "curriculum/tier2/packet_fifo_build/README.md"),
    ("evidence/2026-10-23/divider-admission-attempt-02/tested-source-manifest.json", "curriculum/tier3/iterative_divider_build/README.md"),
}


def classify(row):
    """Return (group key, entry fields) for one failing claim, or stop."""
    m, path, digest = row["manifest"], row["path"], row["sha256"]
    if m == LIVE:
        return (m, "superseded"), {
            "kind": "superseded_state_manifest", "predecessor": "evidence/2026-10-24/seed-binding-quota-block-01/run",
            "reason": "This run folder carries the validation manifest of the quota-blocked run it resumed, unchanged "
                      "(byte-identical to the one in seed-binding-quota-block-01). The resume advanced six state files "
                      "and did not archive the 77 simulator by-products the manifest lists; the predecessor archive "
                      "holds every recorded byte."}
    if m == "evidence/2026-10-28/basys3-uart-echo-01/manifest.json" and path == "bitstream_sha256":
        return (m, "bit"), {
            "kind": "unarchived_tested_binary", "predecessor": None,
            "reason": "The superseded v01 UART echo bitstream was overwritten by the v02 build in the same ignored "
                      "build folder before bitstreams were archived. Its source is kept in basys3-uart-echo-01/"
                      "source-snapshot, but a rebuild cannot reproduce the file digest: the header records the build time."}
    if row["status"] == "unbound" and digest[:10] in REBUILD:
        return (m, "eol", digest[:10]), {"kind": "mixed_eol_tested_source", "predecessor": None,
                                         "reconstruct": REBUILD[digest[:10]], "reason": MIXED}
    if m == RELOCATION and path == "tests\\test_tbqual.py":
        return (m, "eol-tbqual"), {"kind": "mixed_eol_tested_source", "predecessor": None, "reason": MIXED,
                                   "reconstruct": {"blob": "6a8aa61c706a0ba10148cd427839c5ed41a12c08", "lf_lines": [53]}}
    if (m, path) in RECOVERED:
        label = RECOVERED[(m, path)]
        return (m, "recovered"), {
            "kind": "uncommitted_tested_source", "predecessor": f"{HERE}/recovered/{label}",
            "reason": "These tested versions were edited before their first commit. Exact copies survived in Codex "
                      "staging or pytest folders and are archived in evidence-integrity-01/recovered."}
    if (m, path) in LOST:
        return (m, "lost"), {
            "kind": "uncommitted_tested_source", "predecessor": None,
            "reason": "Tested versions edited before their first commit. No commit, run folder or staging folder holds "
                      "the recorded bytes, and no single line-ending or trailing-newline variant of a committed "
                      "version reproduces them."}
    if m == RELOCATION and row["status"] == "unbound":
        return (m, "move"), {"kind": "working_directory_move_record", "predecessor": None, "reason": None}
    raise SystemExit(f"unclassified failure: {row}")


def relocation_reason(paths):
    norm = [p.replace("\\", "/") for p in paths]
    git = sum(p.startswith(".git/") for p in norm)
    cache = sum("__pycache__/" in p or p.startswith(".pytest_cache/") for p in norm)
    logs = [p for p in norm if p.endswith((".jsonl", ".log")) and not p.startswith(".git/")]
    sources = sorted(set(norm) - {p for p in norm if p.startswith(".git/") or "__pycache__/" in p
                                  or p.startswith(".pytest_cache/")} - set(logs))
    return (f"The 2026-10-19 relocation record hashed the whole folder at the move from Documents to Downloads; its "
            f"README says later changes are expected to differ. Not checkable from Git: {git} .git internals, {cache} "
            f"cache files, {len(logs)} ignored logs ({', '.join(logs)}), and {len(sources)} tracked sources whose "
            f"working-copy versions at the move were never committed ({', '.join(sources)}). Its other entries are "
            "checked normally.")


def main(raw_path):
    raw = json.loads(Path(raw_path).read_text(encoding="utf-8"))
    groups, fields = defaultdict(list), {}
    empty, values = [], []
    for row in raw["failures"]:
        if row["status"] == "no_claims" and row["manifest"] == "evidence/2026-10-19/generated-testbenches/manifest.json":
            empty.append({"manifest": row["manifest"], "reason": "A list of generated-testbench cases (name, top, "
                          "expected verdict); it records no digests. The case files carry their own hashes in sim logs."})
            continue
        if row["status"] == "unparsed_digests" and row["manifest"] == "evidence/2026-10-28/basys3-bitstreams-01/manifest.json":
            values.append({"manifest": row["manifest"], "keys": row["detail"],
                           "reason": "configuration_payload_digest is the SHA-256 of each bitstream's configuration "
                                     "data with the build-time header removed, a derived value, not a file. make_manifest.py "
                                     "checks it against the tested payloads in basys3-harness-winners-01/summary.json, "
                                     "and the board-suite tests recheck it in CI."})
            continue
        if "sha256" not in row:
            raise SystemExit(f"unclassified failure: {row}")
        key, entry = classify(row)
        groups[key].append({"container": row["container"], "path": row["path"], "sha256": row["sha256"],
                            "status": row["status"]})
        fields[key] = entry
    exceptions = []
    for key in sorted(groups):
        entry = dict(fields[key])
        if entry["kind"] == "working_directory_move_record":
            entry["reason"] = relocation_reason([c["path"] for c in groups[key]])
        exceptions.append({"manifest": key[0], **entry, "claims": sorted(groups[key], key=lambda c: (c["container"], c["path"]))})
    doc = {"schema": 2, "exceptions": exceptions, "manifests_without_claims": empty, "recorded_values": values}
    OUT.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(exceptions)} exceptions covering {sum(len(e['claims']) for e in exceptions)} claims; "
          f"{len(empty)} manifests without claims; {len(values)} recorded-value entries")


if __name__ == "__main__":
    main(sys.argv[1])
