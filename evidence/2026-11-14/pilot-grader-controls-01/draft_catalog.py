"""Draft a statement-only category/family catalog for VerilogEval spec-to-RTL.

Reads prompts only (never tests or references). Output is a draft for review.
usage: python draft_catalog.py <dataset_dir> <out.json>
"""
import json
import re
import sys
from pathlib import Path

root, out = Path(sys.argv[1]), Path(sys.argv[2])

# Obvious related-task families (shared behavior or one exam question's parts).
FAMILIES = {
    "fsm1": ["Prob107_fsm1s", "Prob109_fsm1"],
    "fsm2": ["Prob110_fsm2", "Prob111_fsm2s"],
    "fsm3": ["Prob079_fsm3onehot", "Prob100_fsm3comb", "Prob119_fsm3", "Prob120_fsm3s"],
    "lemmings": ["Prob127_lemmings1", "Prob142_lemmings2", "Prob152_lemmings3", "Prob155_lemmings4"],
    "fsm_ps2": ["Prob128_fsm_ps2", "Prob154_fsm_ps2data"],
    "fsm_serial": ["Prob137_fsm_serial", "Prob146_fsm_serialdata"],
    "review2015_fancytimer": ["Prob037_review2015_count1k", "Prob063_review2015_shiftcount",
                              "Prob095_review2015_fsmshift", "Prob096_review2015_fsmseq",
                              "Prob151_review2015_fsm", "Prob156_review2015_fancytimer",
                              "Prob150_review2015_fsmonehot"],
    "dff8": ["Prob034_dff8", "Prob041_dff8r", "Prob046_dff8p", "Prob047_dff8ar"],
    "mux256to1": ["Prob018_mux256to1", "Prob021_mux256to1v"],
    "mux2to1": ["Prob017_mux2to1v", "Prob022_mux2to1"],
    "gates_vector": ["Prob092_gatesv100", "Prob094_gatesv"],
    "gates_wide": ["Prob051_gates4", "Prob052_gates100"],
    "popcount": ["Prob009_popcount3", "Prob030_popcount255"],
    "edgedetect": ["Prob054_edgedetect", "Prob045_edgedetect2"],
    "rule_ca": ["Prob108_rule90", "Prob124_rule110"],
    "2014_q3": ["Prob121_2014_q3bfsm", "Prob133_2014_q3fsm", "Prob134_2014_q3c"],
    "2012_q2": ["Prob091_2012_q2b", "Prob138_2012_q2fsm"],
    "2013_q2": ["Prob139_2013_q2bfsm", "Prob148_2013_q2afsm"],
    "ece241_2014_q5": ["Prob088_ece241_2014_q5b", "Prob089_ece241_2014_q5a"],
    "m2014_q6": ["Prob099_m2014_q6c", "Prob135_m2014_q6b", "Prob136_m2014_q6"],
    "mt2015_q4": ["Prob010_mt2015_q4a", "Prob083_mt2015_q4b", "Prob131_mt2015_q4"],
    "m2014_q4_dff_latch": ["Prob048_m2014_q4c", "Prob049_m2014_q4b", "Prob053_m2014_q4d",
                           "Prob008_m2014_q4h", "Prob028_m2014_q4a"],
    "lfsr": ["Prob082_lfsr32", "Prob086_lfsr5"],
}
FAMILY_OF = {t: f for f, ts in FAMILIES.items() for t in ts}

FSM = re.compile(r"\b(state machine|FSM|Moore|Mealy|states?\b|one-hot|onehot|state transition)", re.I)
ARITH = re.compile(r"(\badd(er|ition)?\b|\bsum\b|\bsubtract|\bpopulation count|\bcarry|"
                   r"\boverflow\b|\bmultipl|two's complement|\bcomparator\b|\bcount the number of)", re.I)
CLOCK = re.compile(r"^\s*-\s*input\s+(clk|clock)\b", re.I | re.M)
SEQ_WORDS = re.compile(r"(posedge|positive edge|flip-flop|\bregister\b|clock edge|\bcounter\b|"
                       r"\blatch\b|\bshift register\b|negative edge)", re.I)

catalog, notes = {}, {}
for prompt in sorted(root.glob("*_prompt.txt")):
    task = prompt.name[: -len("_prompt.txt")]
    text = prompt.read_text(encoding="utf-8")
    clocked = bool(CLOCK.search(text)) or bool(SEQ_WORDS.search(text))
    if FSM.search(text) and clocked:
        category = "fsm_control"
    elif clocked:
        category = "sequential"
    elif ARITH.search(text):
        category = "combinational_arithmetic"
    else:
        category = "combinational_logic"
    catalog[task] = {"category": category, "family": FAMILY_OF.get(task, task)}

# A family takes one category: its highest-precedence member's.
order = ["fsm_control", "sequential", "combinational_arithmetic", "combinational_logic"]
for family, tasks in FAMILIES.items():
    best = min((catalog[t]["category"] for t in tasks), key=order.index)
    for t in tasks:
        if catalog[t]["category"] != best:
            notes[t] = f"family {family}: {catalog[t]['category']} -> {best}"
        catalog[t]["category"] = best

out.write_text(json.dumps(catalog, indent=1, sort_keys=True), encoding="utf-8")
from collections import Counter
print(Counter(e["category"] for e in catalog.values()))
print(len({e["family"] for e in catalog.values()}), "families")
for c in order:
    print(f"\n[{c}]", " ".join(t.split("_", 1)[1] for t, e in sorted(catalog.items()) if e["category"] == c))
print("\nfamily overrides:", json.dumps(notes, indent=1))
