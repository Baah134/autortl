from pathlib import Path
from autortl.report_parser import parse_methodology, parse_qor_suggestions
from autortl.taxonomy import Taxonomy
from autortl.device import budget_for, budget_text

FIX = Path(__file__).parent / "fixtures"
ROOT = Path(__file__).resolve().parent.parent


def test_methodology_parsed():
    rows = parse_methodology(FIX / "methodology.rpt")
    ids = [r[0] for r in rows]
    assert "TIMING-9" in ids and "LUTAR-1" in ids
    sev = dict((r[0], r[1]) for r in rows)
    assert sev["TIMING-9"] == "Critical Warning"


def test_methodology_missing_file_empty():
    assert parse_methodology(FIX / "nope.rpt") == []


def test_qor_parsed():
    sugg = parse_qor_suggestions(FIX / "qor_suggestions.rpt")
    assert any("RQS-1" in s for s in sugg)
    assert any("retiming" in s.lower() for s in sugg)


def test_taxonomy_methodology_lookup():
    t = Taxonomy(ROOT / "data" / "taxonomy.yaml")
    e = t.lookup_methodology("TIMING-9")
    assert e is not None and "synchron" in e["advice"].lower()
    assert t.lookup_methodology("NOPE-1") is None


def test_methodology_advisory_never_promotes():
    # methodology entries must NOT leak into the ERROR promotion set
    t = Taxonomy(ROOT / "data" / "taxonomy.yaml")
    assert "TIMING-9" not in t.promotions()


def test_device_budget_known_part():
    b = budget_for("xc7a35tcpg236-1")
    assert b["dsp48"] == 90 and b["luts"] == 20800
    assert "DSP48=90" in budget_text("xc7a35tcpg236-1")


def test_device_budget_unknown_part_empty():
    assert budget_for("xc-nonexistent") is None
    assert budget_text("xc-nonexistent") == ""
