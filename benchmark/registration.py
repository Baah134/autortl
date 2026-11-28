"""Freeze the final benchmark task set before any model result is observed.

Pure function of (catalog, dataset commit, pilot tasks, explicit exclusions).
Every family containing a pilot task is excluded. An explicit exclusion removes
only that task, not its family. N tasks are chosen by largest-remainder quotas
over eligible family counts per category; within a category, families are
ranked by verilogeval.rank(commit, family) and each contributes its best-ranked
eligible task. Standard library only; no model, Vivado or network.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from benchmark import verilogeval as ve
from autortl.fileio import read_json

RULE = ("largest-remainder quotas over eligible family counts per category; families ranked by "
        f"{ve.RANK_PREFIX}|<commit>|<family> (tie: family name); each family contributes its "
        "best-ranked eligible task (min by rank, then task id); pilot families excluded; an "
        "explicit exclusion removes only that task, not its family")
TARGET_N = 40
MIN_N = 30


class RegistrationError(ValueError):
    pass


def quotas(counts: dict, n: int) -> dict:
    """Largest-remainder quotas, capped at each category's count, redistributed.

    Remainder ties break by ve.CATEGORIES order. Requires n <= sum(counts).
    """
    if n > sum(counts.values()):
        raise RegistrationError("not enough eligible families for the requested size")
    result = {c: 0 for c in ve.CATEGORIES}
    pool = {c: counts.get(c, 0) for c in ve.CATEGORIES if counts.get(c, 0) > 0}
    remaining = n
    while pool and remaining > 0:
        total = sum(pool.values())
        share = {c: remaining * k // total for c, k in pool.items()}
        rem = {c: remaining * k % total for c, k in pool.items()}
        left = remaining - sum(share.values())
        order = sorted(pool, key=lambda c: (-rem[c], ve.CATEGORIES.index(c)))
        for c in order[:left]:
            share[c] += 1
        over = [c for c in pool if share[c] > pool[c]]
        if not over:
            for c, s in share.items():
                result[c] += s
            return result
        for c in over:  # fix capped categories at full size and redistribute the rest
            result[c] = pool[c]
            remaining -= pool[c]
            del pool[c]
    if remaining:
        raise RegistrationError("quota redistribution failed")
    return result


def _parse_catalog(catalog: dict) -> tuple[dict, dict, dict]:
    task_family, family_category, family_tasks = {}, {}, {}
    for task_id, entry in sorted(catalog.items()):
        if not isinstance(entry, dict) or set(entry) != {"category", "family"}:
            raise RegistrationError(f"catalog entry {task_id} needs exactly category and family")
        category, family = entry["category"], entry["family"]
        if category not in ve.CATEGORIES:
            raise RegistrationError(f"catalog entry {task_id}: unknown category {category!r}")
        if type(family) is not str or not family:
            raise RegistrationError(f"catalog entry {task_id}: empty family")
        if family_category.setdefault(family, category) != category:
            raise RegistrationError(f"family {family} spans categories")
        task_family[task_id] = family
        family_tasks.setdefault(family, []).append(task_id)
    return task_family, family_category, family_tasks


def register(catalog: dict, commit: str, pilot_tasks, exclusions: dict, n: int = TARGET_N) -> dict:
    ve._check_commit(commit, "dataset commit")
    task_family, family_category, family_tasks = _parse_catalog(catalog)
    pilot = sorted(set(pilot_tasks))
    missing = [t for t in pilot if t not in task_family]
    if missing:
        raise RegistrationError(f"pilot tasks not in catalog: {missing}")
    exclusions = dict(exclusions)
    unknown = sorted(t for t in exclusions if t not in task_family)
    if unknown:
        raise RegistrationError(f"excluded tasks not in catalog: {unknown}")
    for task_id, reason in exclusions.items():
        if type(reason) is not str or not reason.strip():
            raise RegistrationError(f"exclusion {task_id} needs a reason")
    pilot_families = sorted({task_family[t] for t in pilot})
    barred = set(pilot_families)
    eligible_tasks = {f: sorted(t for t in ts if t not in exclusions)
                      for f, ts in family_tasks.items() if f not in barred}
    eligible_tasks = {f: ts for f, ts in eligible_tasks.items() if ts}
    per_category = {c: sorted(f for f in eligible_tasks if family_category[f] == c)
                    for c in ve.CATEGORIES}
    counts = {c: len(v) for c, v in per_category.items()}
    total = sum(counts.values())
    size = n if total >= n else total
    if size < MIN_N:
        raise RegistrationError(f"only {total} eligible families; need at least {MIN_N}")
    quota = quotas(counts, size)
    selected = []
    for c in ve.CATEGORIES:
        ranked = sorted(per_category[c], key=lambda f: (ve.rank(commit, f), f))
        for f in ranked[:quota[c]]:
            task = min(eligible_tasks[f], key=lambda t: (ve.rank(commit, t), t))
            selected.append({"task": task, "category": c, "family": f})
    canonical = json.dumps(selected, sort_keys=True, separators=(",", ":"))
    return {
        "rule": RULE, "commit": commit, "n": len(selected), "quotas": quota,
        "selected": selected,
        "excluded": [{"task": t, "reason": exclusions[t]} for t in sorted(exclusions)],
        "pilot_tasks": pilot, "pilot_families": pilot_families,
        "eligible": {"tasks": sum(len(v) for v in eligible_tasks.values()),
                     "families": total, "per_category": counts},
        "selection_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="python -m benchmark.registration")
    p.add_argument("--catalog", required=True, type=Path)
    p.add_argument("--commit", required=True)
    p.add_argument("--pilot-tasks", required=True, nargs="+")
    p.add_argument("--exclusions", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args(argv)
    if a.out.exists():
        print(f"refusing to overwrite {a.out}", file=sys.stderr)
        return 2
    catalog = read_json(a.catalog)
    exclusions = read_json(a.exclusions)
    result = register(catalog, a.commit, a.pilot_tasks, exclusions)
    with a.out.open("x", encoding="utf-8") as fh:
        fh.write(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(f"registered {result['n']} tasks, sha256 {result['selection_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
