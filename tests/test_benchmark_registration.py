"""Final task registration: determinism, exclusions, quotas, real catalog."""
import json
import random
from pathlib import Path

import pytest

from benchmark import registration as reg
from benchmark import verilogeval as ve

ROOT = Path(__file__).resolve().parent.parent
COMMIT = "c498220d0a52248f8e3fdffe279075215bde2da6"
PILOT = ["Prob036_ringer", "Prob033_ece241_2014_q1c", "Prob147_circuit10",
         "Prob038_count15", "Prob135_m2014_q6b", "Prob107_fsm1s"]


def synth(counts, tasks_per_family=2):
    cat = {}
    for idx, (c, k) in enumerate(counts.items()):
        for i in range(k):
            for j in range(tasks_per_family):
                cat[f"c{idx}_{i:03d}_t{j}"] = {"category": c, "family": f"c{idx}_fam{i:03d}"}
    return cat


def test_quotas_hand_computed():
    counts = dict(zip(ve.CATEGORIES, (7, 5, 4, 4)))
    # 10*7/20=3.5, 2.5, 2, 2 -> floors 3,2,2,2; one left, tie goes to first category
    assert reg.quotas(counts, 10) == dict(zip(ve.CATEGORIES, (4, 2, 2, 2)))
    # n=7: 2.45, 1.75, 1.4, 1.4 -> 2,1,1,1; two left go to .75 then .45
    assert reg.quotas(counts, 7) == dict(zip(ve.CATEGORIES, (3, 2, 1, 1)))


def test_quota_cap_redistributes():
    counts = dict(zip(ve.CATEGORIES, (1, 10, 10, 10)))
    q = reg.quotas(counts, 20)
    assert q["combinational_logic"] == 1 and sum(q.values()) == 20
    assert q == dict(zip(ve.CATEGORIES, (1, 7, 6, 6)))


def test_invariants_and_determinism():
    cat = synth(dict(zip(ve.CATEGORIES, (20, 15, 20, 15))))
    pilot = ["c0_000_t0", "c2_003_t1"]
    excl = {"c0_001_t0": "bad", "c1_002_t0": "bad"}
    a = reg.register(cat, COMMIT, pilot, excl)
    items = list(cat.items())
    random.Random(1).shuffle(items)
    b = reg.register(dict(items), COMMIT, list(reversed(pilot)), dict(reversed(list(excl.items()))))
    assert a == b
    assert a["n"] == 40 and sum(a["quotas"].values()) == 40
    sel = {s["task"] for s in a["selected"]}
    fams = [s["family"] for s in a["selected"]]
    assert len(set(fams)) == len(fams)
    assert not set(fams) & set(a["pilot_families"])
    assert not sel & set(excl)
    # an excluded task removes only itself; its family stays eligible via the sibling
    assert a["eligible"]["tasks"] == 2 * 70 - 2 * 2 - 2


def test_exclusion_picks_sibling():
    cat = synth(dict(zip(ve.CATEGORIES, (10, 10, 10, 10))))
    base = reg.register(cat, COMMIT, [], {})
    pick = base["selected"][0]
    other = reg.register(cat, COMMIT, [], {pick["task"]: "x"})
    same = [s for s in other["selected"] if s["family"] == pick["family"]]
    assert same and same[0]["task"] != pick["task"]


def test_fallback_and_error():
    cat = synth(dict(zip(ve.CATEGORIES, (9, 8, 8, 8))))  # 33 families
    r = reg.register(cat, COMMIT, [], {})
    assert r["n"] == 33 and sum(r["quotas"].values()) == 33
    with pytest.raises(reg.RegistrationError):
        reg.register(synth(dict(zip(ve.CATEGORIES, (8, 7, 7, 7)))), COMMIT, [], {})  # 29


def test_unknown_ids_rejected():
    cat = synth(dict(zip(ve.CATEGORIES, (10, 10, 10, 10))))
    with pytest.raises(reg.RegistrationError):
        reg.register(cat, COMMIT, ["nope"], {})
    with pytest.raises(reg.RegistrationError):
        reg.register(cat, COMMIT, [], {"nope": "r"})


def test_cli_refuses_overwrite(tmp_path):
    cat = tmp_path / "c.json"
    cat.write_text(json.dumps(synth(dict(zip(ve.CATEGORIES, (11, 10, 10, 10))))))
    ex = tmp_path / "e.json"
    ex.write_text("{}")
    out = tmp_path / "o.json"
    args = ["--catalog", str(cat), "--commit", COMMIT, "--pilot-tasks", "c0_000_t0",
            "--exclusions", str(ex), "--out", str(out)]
    assert reg.main(args) == 0
    assert json.loads(out.read_text())["n"] == 40
    assert reg.main(args) == 2


def test_real_catalog():
    cat = json.loads((ROOT / "benchmark/catalogs/verilogeval-c498220.json").read_text())
    excl = json.loads((ROOT / "benchmark/catalogs/exclusions_c498220.json").read_text())
    r = reg.register(cat, COMMIT, PILOT, excl)
    assert r["n"] == 40 and sum(r["quotas"].values()) == 40
    sel = {s["task"] for s in r["selected"]}
    assert len(sel) == 40
    assert not sel & set(excl)
    assert not {s["family"] for s in r["selected"]} & {cat[t]["family"] for t in PILOT}
    assert not sel & set(PILOT)
