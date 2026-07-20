from pathlib import Path
from autortl.taxonomy import Taxonomy

ROOT = Path(__file__).resolve().parent.parent


def test_seeded_entries_load():
    t = Taxonomy(ROOT / "data" / "taxonomy.yaml")
    assert t.lookup("Synth 8-327") is not None


def test_promotions_are_error_only():
    t = Taxonomy(ROOT / "data" / "taxonomy.yaml")
    promos = t.promotions()
    assert "Synth 8-327" in promos
    assert all(v == "ERROR" for v in promos.values())


def test_known_id_repair_text():
    t = Taxonomy(ROOT / "data" / "taxonomy.yaml")
    text = t.repair_instruction("Synth 8-327")
    assert "latch" in text.lower() and "Repair" in text


def test_unknown_id_logged(tmp_path):
    import shutil
    yml = tmp_path / "taxonomy.yaml"
    shutil.copy(ROOT / "data" / "taxonomy.yaml", yml)
    t = Taxonomy(yml)
    t.repair_instruction("Weird 99-999")
    assert "Weird 99-999" in (tmp_path / "unknown_message_ids.log").read_text()
